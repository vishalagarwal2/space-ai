
import os
import json
import logging
import time
from typing import List, Dict, Any, Optional, Union
from abc import ABC, abstractmethod
import numpy as np
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum

from sentence_transformers import SentenceTransformer
import tiktoken

import chromadb
from chromadb.config import Settings
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from pinecone import Pinecone, ServerlessSpec, PodSpec
    from pinecone.grpc import PineconeGRPC
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    Pinecone = None
    PineconeGRPC = None

try:
    from tenacity import (
        retry, 
        stop_after_attempt, 
        wait_exponential, 
        retry_if_exception_type,
        before_sleep_log,
        after_log
    )
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    # Fallback decorator that doesn't retry
    def retry(**kwargs):
        def decorator(func):
            return func
        return decorator
    
    def stop_after_attempt(n):
        return None
    
    def wait_exponential(**kwargs):
        return None
    
    def retry_if_exception_type(*args):
        return None
    
    def before_sleep_log(*args):
        return None
    
    def after_log(*args):
        return None

from .models import Document, KnowledgeBaseConfig

logger = logging.getLogger(__name__)


class PineconeError(Exception):
    """Base exception for Pinecone operations"""
    pass


class PineconeConfigError(PineconeError):
    """Configuration related errors"""
    pass


class PineconeConnectionError(PineconeError):
    """Connection related errors"""
    pass


class PineconeOperationError(PineconeError):
    """Operation related errors"""
    pass


class ConfigurationError(Exception):
    """Raised when configuration building fails"""
    pass


class CloudProvider(Enum):
    """Supported cloud providers"""
    GCP = "gcp"
    AZURE = "azure"


class Region(Enum):
    """Supported regions"""
    # GCP regions
    US_CENTRAL1_GCP = "us-central1-gcp"
    EU_WEST1_GCP = "eu-west1-gcp"
    
    # Azure regions
    EASTUS_AZURE = "eastus-azure"
    WESTEUROPE_AZURE = "westeurope-azure"


@dataclass
class PineconeConfig:
    """Configuration for Pinecone vector store"""
    api_key: str
    index_name: str
    dimension: int
    namespace: str = ""
    cloud: CloudProvider = CloudProvider.GCP
    region: Region = Region.US_CENTRAL1_GCP
    metric: str = "cosine"
    use_grpc: bool = True
    batch_size: int = 100
    delete_batch_size: int = 1000
    timeout: int = 30
    max_retries: int = 3
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        self.validate()
    
    def validate(self):
        """Validate configuration parameters"""
        if not self.api_key:
            raise PineconeConfigError("API key is required")
        
        if not self.index_name or not isinstance(self.index_name, str):
            raise PineconeConfigError("Valid index name is required")
        
        if not isinstance(self.dimension, int) or self.dimension <= 0:
            raise PineconeConfigError("Dimension must be a positive integer")
        
        if self.metric not in ["cosine", "euclidean", "dotproduct"]:
            raise PineconeConfigError(f"Unsupported metric: {self.metric}")
        
        if not isinstance(self.batch_size, int) or self.batch_size <= 0:
            raise PineconeConfigError("Batch size must be a positive integer")
        
        if self.batch_size > 1000:
            logger.warning(f"Batch size {self.batch_size} is large, consider using smaller batches")


@dataclass
class UserEmbeddingPreferences:
    """User's embedding preferences extracted from database"""
    user_id: str
    default_embedding_model: str = 'sentence_transformer'
    default_vector_store: str = 'chroma'
    # Note: API keys are now always read from environment variables, not stored in user preferences
    
    @classmethod
    def from_knowledge_base_config(cls, user_id: str, config) -> 'UserEmbeddingPreferences':
        """Create preferences from KnowledgeBaseConfig object"""
        if not config:
            logger.info(f"No KnowledgeBaseConfig for user {user_id}, using defaults")
            return cls(user_id=user_id)
        
        return cls(
            user_id=user_id,
            default_embedding_model=getattr(config, 'default_embedding_model', 'sentence_transformer'),
            default_vector_store=getattr(config, 'default_vector_store', 'chroma')
        )
    
    def __str__(self) -> str:
        return f"UserPreferences(user={self.user_id}, model={self.default_embedding_model}, store={self.default_vector_store})"


@dataclass
class EmbeddingModelConfig:
    """Configuration for a specific embedding model"""
    wrapper_name: str  # 'sentence_transformer' or 'openai_ada'
    model_name: str    # 'all-MiniLM-L6-v2' or 'text-embedding-ada-002'
    dimension: int     # 384 or 1536
    model_type: str    # 'sentence_transformer' or 'openai'


class BaseEmbeddingModel(ABC):
    """Base class for embedding models"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.model_name = self.config.get('model_name', 'default')
        self.dimension = self.config.get('dimension', 384)
    
    @abstractmethod
    def encode(self, texts: Union[str, List[str]]) -> Union[np.ndarray, List[List[float]]]:
        """Encode text(s) into embeddings"""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimension of the embeddings"""
        pass
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text before embedding"""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        # Truncate if too long
        max_tokens = self.config.get('max_tokens', 8192)
        if len(text) > max_tokens:
            text = text[:max_tokens]
        return text


class SentenceTransformerEmbedding(BaseEmbeddingModel):
    """Sentence Transformer embedding model"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.model_name = self.config.get('model_name', 'all-MiniLM-L6-v2')
        self.model = SentenceTransformer(self.model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
    
    def encode(self, texts: Union[str, List[str]]) -> Union[np.ndarray, List[List[float]]]:
        """Encode text(s) into embeddings"""
        if isinstance(texts, str):
            texts = [texts]
        
        # Preprocess texts
        texts = [self.preprocess_text(text) for text in texts]
        
        # Generate embeddings
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        
        if len(embeddings) == 1:
            return embeddings[0]
        return embeddings
    
    def get_dimension(self) -> int:
        return self.dimension


class OpenAIEmbedding(BaseEmbeddingModel):
    """OpenAI embedding model"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.model_name = self.config.get('model_name', 'text-embedding-ada-002')
        self.api_key = self.config.get('api_key')
        self.dimension = self.config.get('dimension', 1536)
        self.client = None
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available")
        
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
            openai.api_key = self.api_key
        else:
            raise ValueError("OpenAI API key is required for OpenAIEmbedding")
    
    def encode(self, texts: Union[str, List[str]]) -> Union[np.ndarray, List[List[float]]]:
        """Encode text(s) into embeddings"""
        if isinstance(texts, str):
            texts = [texts]
        
        # Preprocess texts
        texts = [self.preprocess_text(text) for text in texts]

        logger.info(f"OpenAIEmbedding.encode called with {len(texts)} texts using model '{self.model_name}'")

        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model_name
            )
            logger.info(f"OpenAI API returned {len(response.data)} embeddings")
            embeddings = [data.embedding for data in response.data]
            if len(embeddings) == 1:
                logger.debug("Returning single embedding as np.array")
                return np.array(embeddings[0])
            logger.debug("Returning list of embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating OpenAI embeddings: {e}")
            raise
    
    def get_dimension(self) -> int:
        return self.dimension


class BaseVectorStore(ABC):
    """Base class for vector stores"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.collection_name = self.config.get('collection_name', 'default')
    
    @abstractmethod
    def add_embeddings(self, embeddings: List[List[float]], texts: List[str], 
                      metadata: List[Dict[str, Any]] = None, ids: List[str] = None):
        """Add embeddings to the vector store"""
        pass
    
    @abstractmethod
    def search(self, query_embedding: List[float], k: int = 10, 
               filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for similar embeddings"""
        pass
    
    @abstractmethod
    def delete(self, ids: List[str]):
        """Delete embeddings by IDs"""
        pass
    
    @abstractmethod
    def update_metadata(self, ids: List[str], metadata: List[Dict[str, Any]]):
        """Update metadata for embeddings"""
        pass


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB vector store with configurable persistence path"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        # Handle path configuration with multiple options
        self.persist_directory = self._get_persist_directory()
        
        # Ensure directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize ChromaDB with the configured path
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        logger.info(json.dumps({"event": "ChromaVectorStoreConfig", "config": self.config}, default=str))

        logger.info(json.dumps({"event": "ChromaVectorStoreInit", "chroma_config": self.config}, default=str))
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        
        logger.info(f"ChromaDB initialized with persist directory: {self.persist_directory}")
    
    def _get_persist_directory(self) -> str:
        """Get the persistence directory from various sources"""
        # Priority order: config > environment variable > default
        persist_dir = None
        
        # Check environment variable
        if os.getenv('CHROMA_DB_PATH'):
            persist_dir = os.getenv('CHROMA_DB_PATH')
        
        # Use default
        else:
            persist_dir = './chroma_db'
        
        # Convert to absolute path for consistency
        return os.path.abspath(persist_dir)
    
    def get_persist_directory(self) -> str:
        """Get the current persistence directory"""
        return self.persist_directory
    
    def change_persist_directory(self, new_path: str):
        """Change the persistence directory and reinitialize client"""
        try:
            # Close existing client if needed
            if hasattr(self.client, 'close'):
                self.client.close()
            
            # Update path
            self.persist_directory = os.path.abspath(new_path)
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Reinitialize client with new path
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Reconnect to collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(f"ChromaDB path changed to: {self.persist_directory}")
            
        except Exception as e:
            logger.error(f"Error changing persist directory: {e}")
            raise
    
    def add_embeddings(self, embeddings: List[List[float]], texts: List[str], 
                      metadata: List[Dict[str, Any]] = None, ids: List[str] = None):
        """Add embeddings to ChromaDB"""
        try:
            if not ids:
                ids = [f"doc_{i}" for i in range(len(texts))]
            
            if not metadata:
                metadata = [{}] * len(texts)

            
            logger.info(f"Adding {len(embeddings)} embeddings to ChromaDB with ids: {ids}")
            logger.debug(f"Embeddings: {embeddings}")
            logger.debug(f"Texts: {texts}")
            logger.debug(f"Metadata: {metadata}")
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadata,
                ids=ids
            )
            logger.info(f"Successfully added embeddings to ChromaDB collection '{self.collection_name}'")
            
            logger.debug(f"Added {len(embeddings)} embeddings to ChromaDB")
            
        except Exception as e:
            logger.error(f"Error adding embeddings to ChromaDB: {e}")
            raise
    
    def search(self, query_embedding: List[float], k: int = 10, 
               filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search ChromaDB for similar embeddings"""
        try:
            # where_filter = {}
            # logger.info(f"Received filter_metadata: {filter_metadata}")
            # if filter_metadata:
            #     filter_clauses = []
            #     for key, value in filter_metadata.items():
            #         logger.info(f"Processing filter key: {key}, value: {value}")
            #         if isinstance(value, list):
            #             clause = {key: {"$in": value}}
            #             logger.info(f"Filter clause for list: {clause}")
            #         elif isinstance(value, dict) and any(k.startswith("$") for k in value.keys()):
            #             clause = {key: value}
            #             logger.info(f"Filter clause for dict with operator: {clause}")
            #         else:
            #             clause = {key: {"$eq": value}}
            #             logger.info(f"Filter clause for eq: {clause}")
            #         filter_clauses.append(clause)
            #     if len(filter_clauses) == 1:
            #         where_filter = filter_clauses[0]
            #         logger.info(f"Single filter clause used: {where_filter}")
            #     else:
            #         where_filter = {"$and": filter_clauses}
            #         logger.info(f"Multiple filter clauses combined with $and: {where_filter}")
            # else:
            #     where_filter = None
            #     logger.info("No filter_metadata provided; where_filter set to None")

            # # Convert UUIDs to strings before logging and querying
            # where_filter = _convert_uuids(where_filter)
            # logger.info(f"Searching ChromaDB: k={k}, filter={where_filter}")

            where_filter = None
            logger.info(f"Received filter_metadata: {filter_metadata}")

            if filter_metadata:
                # Assume filter_metadata is already a logical filter
                where_filter = _convert_uuids(filter_metadata)

            logger.info(f"Searching ChromaDB: k={k}, filter={where_filter}")

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_filter
            )

            logger.info(f"ChromaDB search returned {len(results['ids'][0]) if results and 'ids' in results and results['ids'] else 0} results")
            logger.info(f"ChromaDB search raw results: {json.dumps(results, indent=2, default=str)}")

            # Format results - FIXED: Check if results exist and have data
            formatted_results = []
            
            # Check if results exist and have the expected structure
            if (results and 
                'ids' in results and 
                'documents' in results and 
                'metadatas' in results and 
                'distances' in results and
                results['ids'] and 
                len(results['ids']) > 0 and
                len(results['ids'][0]) > 0):
                
                # Get the first (and typically only) query result
                ids = results['ids'][0]
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]
                
                # Format each result
                for i in range(len(ids)):
                    formatted_result = {
                        'id': ids[i],
                        'text': documents[i] if i < len(documents) else '',
                        'metadata': metadatas[i] if i < len(metadatas) else {},
                        'distance': distances[i] if i < len(distances) else 0.0
                    }
                    formatted_results.append(formatted_result)

                logger.info(f"Formatted search results: {json.dumps(formatted_results, indent=2, default=str)}")
                
                logger.info(f"Successfully formatted {len(formatted_results)} search results")
            else:
                logger.warning("No results found or results structure is invalid")

            return formatted_results

        except Exception as e:
            logger.error(f"Error searching ChromaDB: {e}")
            return []
    
    def delete(self, ids: List[str]):
        """Delete embeddings from ChromaDB"""
        try:
            self.collection.delete(ids=ids)
            logger.debug(f"Deleted {len(ids)} embeddings from ChromaDB")
            
        except Exception as e:
            logger.error(f"Error deleting from ChromaDB: {e}")
    
    def update_metadata(self, ids: List[str], metadata: List[Dict[str, Any]]):
        """Update metadata in ChromaDB"""
        try:
            self.collection.update(
                ids=ids,
                metadatas=metadata
            )
            logger.debug(f"Updated metadata for {len(ids)} embeddings")
            
        except Exception as e:
            logger.error(f"Error updating metadata in ChromaDB: {e}")
    
    def backup_to_path(self, backup_path: str):
        """Create a backup of the current database to a different path"""
        try:
            import shutil
            backup_path = os.path.abspath(backup_path)
            
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
            
            shutil.copytree(self.persist_directory, backup_path)
            logger.info(f"Database backed up to: {backup_path}")
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the current collection"""
        try:
            count = self.collection.count()
            return {
                'name': self.collection_name,
                'count': count,
                'persist_directory': self.persist_directory
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents from the collection"""
        try:
            # Get all documents from the collection
            results = self.collection.get()
            
            formatted_results = []
            if (results and 
                'ids' in results and 
                'documents' in results and 
                'metadatas' in results and
                results['ids']):
                
                for i in range(len(results['ids'])):
                    formatted_result = {
                        'id': results['ids'][i],
                        'text': results['documents'][i] if i < len(results['documents']) else '',
                        'metadata': results['metadatas'][i] if i < len(results['metadatas']) else {}
                    }
                    formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error getting all documents: {e}")
            return []


class FAISSVectorStore(BaseVectorStore):
    """FAISS vector store"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.dimension = self.config.get('dimension', 384)
        self.index_file = self.config.get('index_file', f'faiss_{self.collection_name}.index')
        self.metadata_file = self.config.get('metadata_file', f'faiss_{self.collection_name}_metadata.json')
        
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS library not available")
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata_store = {}
        self.id_to_index = {}
        self.index_to_id = {}
        
        # Load existing index if available
        self._load_index()
    
    def _load_index(self):
        """Load existing FAISS index"""
        try:
            if os.path.exists(self.index_file):
                self.index = faiss.read_index(self.index_file)
            
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    self.metadata_store = data.get('metadata', {})
                    self.id_to_index = data.get('id_to_index', {})
                    self.index_to_id = data.get('index_to_id', {})
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")
    
    def _save_index(self):
        """Save FAISS index"""
        try:
            faiss.write_index(self.index, self.index_file)
            
            with open(self.metadata_file, 'w') as f:
                json.dump({
                    'metadata': self.metadata_store,
                    'id_to_index': self.id_to_index,
                    'index_to_id': self.index_to_id
                }, f)
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")
    
    def add_embeddings(self, embeddings: List[List[float]], texts: List[str], 
                      metadata: List[Dict[str, Any]] = None, ids: List[str] = None):
        """Add embeddings to FAISS"""
        try:
            if not ids:
                ids = [f"doc_{i}" for i in range(len(texts))]
            
            if not metadata:
                metadata = [{}] * len(texts)
            
            # Convert to numpy array
            embeddings_np = np.array(embeddings).astype('float32')
            
            # Add to FAISS index
            start_index = self.index.ntotal
            self.index.add(embeddings_np)
            
            # Store metadata
            for i, (doc_id, text, meta) in enumerate(zip(ids, texts, metadata)):
                index_pos = start_index + i
                self.id_to_index[doc_id] = index_pos
                self.index_to_id[str(index_pos)] = doc_id
                self.metadata_store[doc_id] = {
                    'text': text,
                    'metadata': meta
                }
            
            self._save_index()
        except Exception as e:
            logger.error(f"Error adding embeddings to FAISS: {e}")
            raise
    
    def search(self, query_embedding: List[float], k: int = 10, 
               filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search FAISS for similar embeddings"""
        try:
            if filter_metadata and any(key.startswith('$') for key in filter_metadata.keys()):
                logger.warning("FAISSVectorStore does not support logical filters ($and/$or). Ignoring filter.")
                filter_metadata = None

            query_np = np.array([query_embedding]).astype('float32')
            
            # Search FAISS
            distances, indices = self.index.search(query_np, k)
            
            # Format results
            results = []
            for i, (distance, index) in enumerate(zip(distances[0], indices[0])):
                if index == -1:  # No more results
                    break
                
                doc_id = self.index_to_id.get(str(index))
                if doc_id and doc_id in self.metadata_store:
                    doc_data = self.metadata_store[doc_id]
                    
                    # Apply metadata filter if specified
                    if filter_metadata:
                        if not self._matches_filter(doc_data['metadata'], filter_metadata):
                            continue
                    
                    results.append({
                        'id': doc_id,
                        'text': doc_data['text'],
                        'metadata': doc_data['metadata'],
                        'distance': float(distance)
                    })
            
            return results
        except Exception as e:
            logger.error(f"Error searching FAISS: {e}")
            return []
    
    def delete(self, ids: List[str]):
        """Delete embeddings from FAISS (mark as deleted)"""
        try:
            for doc_id in ids:
                if doc_id in self.metadata_store:
                    del self.metadata_store[doc_id]
                if doc_id in self.id_to_index:
                    index_pos = self.id_to_index[doc_id]
                    del self.id_to_index[doc_id]
                    if str(index_pos) in self.index_to_id:
                        del self.index_to_id[str(index_pos)]
            
            self._save_index()
        except Exception as e:
            logger.error(f"Error deleting from FAISS: {e}")
    
    def update_metadata(self, ids: List[str], metadata: List[Dict[str, Any]]):
        """Update metadata in FAISS"""
        try:
            for doc_id, meta in zip(ids, metadata):
                if doc_id in self.metadata_store:
                    self.metadata_store[doc_id]['metadata'] = meta
            
            self._save_index()
        except Exception as e:
            logger.error(f"Error updating metadata in FAISS: {e}")
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_metadata: Dict[str, Any]) -> bool:
        """Check if metadata matches filter"""
        for key, value in filter_metadata.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True


class ProductionPineconeVectorStore:
    """Production-ready Pinecone vector store implementation"""
    
    def __init__(self, config: PineconeConfig):
        if not PINECONE_AVAILABLE:
            raise ImportError(
                "Pinecone library not available. Install with: "
                "pip install 'pinecone[grpc]' for best performance"
            )
        
        self.config = config
        self._client: Optional[Union[Pinecone, PineconeGRPC]] = None
        self._index = None
        
        # Initialize connection
        self._initialize_client()
        self._initialize_index()
        
        logger.info(
            f"ProductionPineconeVectorStore initialized: index={self.config.index_name}, "
            f"namespace={self.config.namespace}, grpc={self.config.use_grpc}"
        )
    
    @property
    def client(self) -> Union[Pinecone, PineconeGRPC]:
        """Get Pinecone client with lazy initialization"""
        if self._client is None:
            self._initialize_client()
        return self._client
    
    @property
    def index(self):
        """Get Pinecone index with lazy initialization"""
        if self._index is None:
            self._initialize_index()
        return self._index
    
    def _initialize_client(self):
        """Initialize Pinecone client with proper error handling"""
        try:
            if self.config.use_grpc:
                self._client = PineconeGRPC(
                    api_key=self.config.api_key,
                    pool_threads=30  # For better performance
                )
                logger.info("Initialized Pinecone gRPC client")
            else:
                self._client = Pinecone(
                    api_key=self.config.api_key,
                    pool_threads=30
                )
                logger.info("Initialized Pinecone HTTP client")
        except Exception as e:
            raise PineconeConnectionError(f"Failed to initialize Pinecone client: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((Exception, ConnectionError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.ERROR)
    ) if TENACITY_AVAILABLE else lambda x: x
    def _initialize_index(self):
        """Initialize or create Pinecone index with retry logic"""
        try:
            # Check if index exists
            if self._index_exists():
                logger.info(f"Connecting to existing index: {self.config.index_name}")
                index_info = self.client.describe_index(self.config.index_name)
                
                # Validate index configuration
                self._validate_index_config(index_info)
                
                self._index = self.client.Index(host=index_info.host)
            else:
                logger.info(f"Creating new index: {self.config.index_name}")
                self._create_index()
                self._wait_for_index_ready()
                
                # Get the created index
                index_info = self.client.describe_index(self.config.index_name)
                self._index = self.client.Index(host=index_info.host)
                
        except Exception as e:
            raise PineconeOperationError(f"Failed to initialize index: {str(e)}")
    
    def _index_exists(self) -> bool:
        """Check if index exists"""
        try:
            existing_indexes = [idx.name for idx in self.client.list_indexes()]
            return self.config.index_name in existing_indexes
        except Exception as e:
            logger.error(f"Error checking index existence: {e}")
            return False
    
    def _validate_index_config(self, index_info):
        """Validate that existing index matches configuration"""
        if hasattr(index_info, 'dimension') and index_info.dimension != self.config.dimension:
            raise PineconeConfigError(
                f"Index dimension mismatch: expected {self.config.dimension}, "
                f"got {index_info.dimension}"
            )
        
        if hasattr(index_info, 'metric') and index_info.metric != self.config.metric:
            logger.warning(
                f"Index metric mismatch: expected {self.config.metric}, "
                f"got {index_info.metric}"
            )
    
    def _create_index(self):
        """Create a new Pinecone index"""
        try:
            # Convert enum to Pinecone SDK format
            from pinecone import ServerlessSpec, CloudProvider as PineconeCloudProvider
            
            # Map our enums to Pinecone enums
            cloud_mapping = {
                CloudProvider.GCP: PineconeCloudProvider.GCP,
                CloudProvider.AZURE: PineconeCloudProvider.AZURE
            }
            
            # Map regions (simplified - you'd extend this)
            region_str = self.config.region.value
            
            index_config = self.client.create_index(
                name=self.config.index_name,
                dimension=self.config.dimension,
                metric=self.config.metric,
                spec=ServerlessSpec(
                    cloud=cloud_mapping[self.config.cloud],
                    region=region_str
                ),
                deletion_protection="disabled"  # Can be made configurable
            )
            
            logger.info(f"Created index: {self.config.index_name}")
            return index_config
            
        except Exception as e:
            raise PineconeOperationError(f"Failed to create index: {str(e)}")
    
    def _wait_for_index_ready(self, max_wait_time: int = 300):
        """Wait for index to be ready with timeout"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                index_info = self.client.describe_index(self.config.index_name)
                if hasattr(index_info, 'status') and index_info.status.ready:
                    logger.info(f"Index {self.config.index_name} is ready")
                    return
                    
                logger.info(f"Waiting for index {self.config.index_name} to be ready...")
                time.sleep(5)
                
            except Exception as e:
                logger.warning(f"Error checking index status: {e}")
                time.sleep(5)
        
        raise TimeoutError(
            f"Index {self.config.index_name} did not become ready within "
            f"{max_wait_time} seconds"
        )
    
    @contextmanager
    def _error_context(self, operation: str):
        """Context manager for consistent error handling"""
        try:
            logger.debug(f"Starting operation: {operation}")
            yield
            logger.debug(f"Completed operation: {operation}")
        except Exception as e:
            logger.error(f"Unexpected error in {operation}: {e}")
            raise PineconeOperationError(f"{operation} failed unexpectedly: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception, ConnectionError, TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    ) if TENACITY_AVAILABLE else lambda x: x
    def add_embeddings(
        self,
        embeddings: List[List[float]],
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ):
        """Add embeddings to Pinecone with robust error handling and detailed logging"""
        
        logger.info(
            f"add_embeddings called: embeddings={len(embeddings)}, texts={len(texts)}, "
            f"metadata={'provided' if metadata else 'not provided'}, ids={'provided' if ids else 'not provided'}"
        )

        # Input validation
        if not embeddings:
            logger.error("Embeddings list cannot be empty")
            raise ValueError("Embeddings list cannot be empty")
        
        if len(embeddings) != len(texts):
            logger.error(f"Embeddings and texts must have the same length: {len(embeddings)} vs {len(texts)}")
            raise ValueError("Embeddings and texts must have the same length")
        
        # Validate embedding dimensions
        for i, embedding in enumerate(embeddings):
            if len(embedding) != self.config.dimension:
                logger.error(
                    f"Embedding {i} has dimension {len(embedding)}, expected {self.config.dimension}"
                )
                raise ValueError(
                    f"Embedding {i} has dimension {len(embedding)}, "
                    f"expected {self.config.dimension}"
                )
        
        # Generate IDs if not provided
        if not ids:
            ids = [f"doc_{uuid.uuid4()}" for _ in range(len(texts))]
            logger.info(f"Generated {len(ids)} new IDs for embeddings")
        elif len(ids) != len(texts):
            logger.error(f"IDs and texts must have the same length: {len(ids)} vs {len(texts)}")
            raise ValueError("IDs and texts must have the same length")
        
        # Prepare metadata
        if not metadata:
            metadata = [{}] * len(texts)
            logger.info("No metadata provided, using empty dicts")
        elif len(metadata) != len(texts):
            logger.error(f"Metadata and texts must have the same length: {len(metadata)} vs {len(texts)}")
            raise ValueError("Metadata and texts must have the same length")
        
        with self._error_context("add_embeddings"):
            vectors = []
            for idx, (vec_id, embedding, text, meta) in enumerate(zip(ids, embeddings, texts, metadata)):
                # Add text to metadata for retrieval
                full_metadata = meta.copy()
                full_metadata['text'] = text
                full_metadata['created_at'] = time.time()
                
                vectors.append({
                    'id': str(vec_id),  # Ensure ID is string
                    'values': embedding,
                    'metadata': full_metadata
                })
                logger.debug(
                    f"Prepared vector {idx}: id={vec_id}, text_len={len(text)}, metadata_keys={list(full_metadata.keys())}"
                )
            
            logger.info(
                f"Prepared {len(vectors)} vectors for upsert to Pinecone index '{self.config.index_name}' "
                f"namespace '{self.config.namespace}'"
            )
            # Batch upsert
            self._batch_upsert(vectors)
            
            logger.info(
                f"Successfully added {len(embeddings)} embeddings to "
                f"index '{self.config.index_name}', namespace '{self.config.namespace}'"
            )

    def _batch_upsert(self, vectors: List[Dict]):
        """Perform batch upsert with proper error handling and detailed logging"""
        batch_size = self.config.batch_size
        total_batches = (len(vectors) + batch_size - 1) // batch_size

        logger.info(
            f"Starting batch upsert: total_vectors={len(vectors)}, batch_size={batch_size}, total_batches={total_batches}, "
            f"index='{self.config.index_name}', namespace='{self.config.namespace}'"
        )

        for i in range(0, len(vectors), batch_size):
            batch_num = i // batch_size + 1
            batch = vectors[i:i + batch_size]

            logger.info(
                f"Upserting batch {batch_num}/{total_batches} "
                f"({len(batch)} vectors) to index='{self.config.index_name}', namespace='{self.config.namespace}'"
            )
            logger.info(f"Batch {batch_num} vector IDs: {[v['id'] for v in batch]}")

            try:
                response = self.index.upsert(
                    vectors=batch,
                    namespace=self.config.namespace
                )

                # Validate response
                if hasattr(response, 'upserted_count'):
                    logger.info(
                        f"Batch {batch_num}: upserted_count={response.upserted_count}, expected={len(batch)}"
                    )
                    if response.upserted_count != len(batch):
                        logger.warning(
                            f"Expected to upsert {len(batch)} vectors, "
                            f"but only {response.upserted_count} were upserted in batch {batch_num}"
                        )
                else:
                    logger.info(f"Batch {batch_num}: upsert response has no 'upserted_count' attribute")

            except Exception as e:
                logger.error(f"Failed to upsert batch {batch_num}: {e}")
                raise

        logger.info(
            f"Completed batch upsert: total_vectors={len(vectors)}, batches={total_batches}, "
            f"index='{self.config.index_name}', namespace='{self.config.namespace}'"
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((Exception, ConnectionError, TimeoutError))
    ) if TENACITY_AVAILABLE else lambda x: x
    def search(
        self,
        query_embedding: List[float],
        k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar embeddings with robust error handling"""

        logger.info(
            f"Starting Pinecone search: k={k}, filter_metadata={json.dumps(filter_metadata, default=str)}, "
            f"index='{self.config.index_name}', namespace='{self.config.namespace}'"
        )

        # Input validation
        if not query_embedding:
            logger.info("Query embedding is empty")
            raise ValueError("Query embedding cannot be empty")

        if len(query_embedding) != self.config.dimension:
            logger.info(
                f"Query embedding dimension {len(query_embedding)} doesn't match index dimension {self.config.dimension}"
            )
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} doesn't "
                f"match index dimension {self.config.dimension}"
            )

        if k <= 0:
            logger.info("k must be positive")
            raise ValueError("k must be positive")

        with self._error_context("search"):
            # Convert filter to Pinecone format
            # pinecone_filter = self._convert_filter(filter_metadata) if filter_metadata else None

            pinecone_filter = filter_metadata if filter_metadata else None

            if pinecone_filter is not None:
                pinecone_filter = _sanitize_filter_for_pinecone(pinecone_filter)

            logger.info(
                f"Performing Pinecone query: top_k={min(k, 10000)}, filter={json.dumps(pinecone_filter, default=str)}, "
                f"namespace='{self.config.namespace}'"
            )

            # Perform query
            response = self.index.query(
                vector=query_embedding,
                top_k=min(k, 10000),  # Pinecone limit
                filter=pinecone_filter,
                namespace=self.config.namespace,
                include_metadata=True,
                include_values=False
            )

            # Format results
            results = []
            if response and hasattr(response, 'matches'):
                logger.info(f"Pinecone returned {len(response.matches)} matches")
                for match in response.matches:
                    # Validate match structure
                    if not hasattr(match, 'id') or not hasattr(match, 'score'):
                        logger.warning(f"Invalid match structure: {match}")
                        continue

                    metadata = getattr(match, 'metadata', {}) or {}
                    text = metadata.pop('text', '')

                    result = {
                        'id': match.id,
                        'text': text,
                        'metadata': metadata,
                        'score': float(match.score),
                        'distance': 1.0 - float(match.score)  # Convert to distance
                    }
                    results.append(result)
            else:
                logger.info("No matches returned from Pinecone search")

            logger.info(
                f"Search returned {len(results)} results from "
                f"index '{self.config.index_name}', namespace '{self.config.namespace}'"
            )

            return results

    def _convert_filter(self, filter_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Convert filter to Pinecone format with validation"""
        logger.info(f"Converting filter_metadata to Pinecone format: {json.dumps(filter_metadata, default=str)}")
        if not isinstance(filter_metadata, dict):
            logger.info("Filter metadata must be a dictionary")
            raise ValueError("Filter metadata must be a dictionary")

        pinecone_filter = {}

        for key, value in filter_metadata.items():
            if not isinstance(key, str):
                logger.info(f"Filter key must be string, got {type(key)}")
                raise ValueError(f"Filter key must be string, got {type(key)}")

            if isinstance(value, list):
                pinecone_filter[key] = {"$in": value}
                logger.info(f"Filter for key '{key}': $in {value}")
            elif isinstance(value, dict):
                # Validate operators
                valid_operators = {"$eq", "$ne", "$gt", "$gte", "$lt", "$lte", "$in", "$nin"}
                for op in value.keys():
                    if op not in valid_operators:
                        logger.info(f"Invalid filter operator: {op}")
                        raise ValueError(f"Invalid filter operator: {op}")
                pinecone_filter[key] = value
                logger.info(f"Filter for key '{key}': {value}")
            else:
                pinecone_filter[key] = {"$eq": value}
                logger.info(f"Filter for key '{key}': $eq {value}")

        logger.info(f"Converted Pinecone filter: {json.dumps(pinecone_filter, default=str)}")
        return pinecone_filter
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception, ConnectionError))
    ) if TENACITY_AVAILABLE else lambda x: x
    def delete(self, ids: List[str]):
        """Delete embeddings by IDs with batch processing"""
        if not ids:
            logger.warning("No IDs provided for deletion")
            return
        
        if not all(isinstance(id_, str) for id_ in ids):
            raise ValueError("All IDs must be strings")
        
        with self._error_context("delete"):
            # Batch delete
            batch_size = self.config.delete_batch_size
            total_batches = (len(ids) + batch_size - 1) // batch_size
            
            for i in range(0, len(ids), batch_size):
                batch_num = i // batch_size + 1
                batch_ids = ids[i:i + batch_size]
                
                logger.debug(f"Deleting batch {batch_num}/{total_batches} ({len(batch_ids)} IDs)")
                
                self.index.delete(
                    ids=batch_ids,
                    namespace=self.config.namespace
                )
            
            logger.info(f"Deleted {len(ids)} embeddings from Pinecone")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    ) if TENACITY_AVAILABLE else lambda x: x
    def update_metadata(self, ids: List[str], metadata_list: List[Dict[str, Any]]):
        """Update metadata for existing vectors"""
        if not ids or not metadata_list:
            raise ValueError("IDs and metadata list cannot be empty")
        
        if len(ids) != len(metadata_list):
            raise ValueError("IDs and metadata must have the same length")
        
        with self._error_context("update_metadata"):
            # Fetch existing vectors
            try:
                fetch_response = self.index.fetch(
                    ids=ids,
                    namespace=self.config.namespace
                )
            except Exception as e:
                raise PineconeOperationError(f"Failed to fetch vectors for update: {e}")
            
            if not fetch_response or not hasattr(fetch_response, 'vectors'):
                logger.warning("No vectors found to update")
                return
            
            # Prepare updated vectors
            updated_vectors = []
            vectors_dict = fetch_response.vectors
            
            for vec_id, new_metadata in zip(ids, metadata_list):
                if vec_id not in vectors_dict:
                    logger.warning(f"Vector {vec_id} not found, skipping")
                    continue
                
                existing_vector = vectors_dict[vec_id]
                
                # Merge metadata
                updated_meta = getattr(existing_vector, 'metadata', {}).copy()
                updated_meta.update(new_metadata)
                updated_meta['updated_at'] = time.time()
                
                updated_vectors.append({
                    'id': vec_id,
                    'values': getattr(existing_vector, 'values', []),
                    'metadata': updated_meta
                })
            
            # Re-upsert with updated metadata
            if updated_vectors:
                self._batch_upsert(updated_vectors)
                logger.info(f"Updated metadata for {len(updated_vectors)} vectors")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            with self._error_context("get_stats"):
                stats = self.index.describe_index_stats()
                
                return {
                    'total_vector_count': getattr(stats, 'total_vector_count', 0),
                    'dimension': getattr(stats, 'dimension', self.config.dimension),
                    'index_fullness': getattr(stats, 'index_fullness', 0.0),
                    'namespaces': getattr(stats, 'namespaces', {}),
                    'index_name': self.config.index_name
                }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                'error': str(e),
                'index_name': self.config.index_name
            }
    
    def health_check(self) -> bool:
        """Perform health check on the vector store"""
        try:
            # Try a simple describe operation
            self.client.describe_index(self.config.index_name)
            
            # Try a simple query if there's data
            stats = self.get_stats()
            if stats.get('total_vector_count', 0) > 0:
                # Test query with a zero vector
                test_vector = [0.0] * self.config.dimension
                self.index.query(
                    vector=test_vector,
                    top_k=1,
                    namespace=self.config.namespace
                )
            
            logger.info("Health check passed")
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def delete_namespace(self, namespace: Optional[str] = None):
        """Delete all vectors in a namespace"""
        target_namespace = namespace or self.config.namespace
        
        with self._error_context("delete_namespace"):
            self.index.delete(
                delete_all=True,
                namespace=target_namespace
            )
            logger.info(f"Deleted all vectors in namespace '{target_namespace}'")
    
    def close(self):
        """Clean up resources"""
        # Pinecone client doesn't require explicit cleanup, but we can clear references
        self._index = None
        self._client = None
        logger.info("ProductionPineconeVectorStore closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class PineconeVectorStore(BaseVectorStore):
    """Adapter to make ProductionPineconeVectorStore compatible with BaseVectorStore interface"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        if not PINECONE_AVAILABLE:
            raise ImportError("Pinecone library not available. Install with: pip install 'pinecone[grpc]'")
        
        try:
            # Create PineconeConfig from the config dict
            pinecone_config = self._create_pinecone_config(config or {})
            
            # Initialize the production store
            self.store = ProductionPineconeVectorStore(pinecone_config)
            
            logger.info(f"PineconeVectorStore initialized with index: {pinecone_config.index_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize PineconeVectorStore: {e}")
            raise
    
    def _create_pinecone_config(self, config: Dict[str, Any]) -> PineconeConfig:
        """Create PineconeConfig from configuration dictionary"""
        
        # Required parameters
        api_key = config.get('api_key') or os.getenv('PINECONE_API_KEY')
        if not api_key:
            raise PineconeConfigError("Pinecone API key is required")
        
        index_name = config.get('index_name', 'knowledge-base-prod')
        dimension = config.get('dimension', 1536)
        namespace = config.get('namespace', '')
        
        # Optional parameters with defaults
        cloud_str = config.get('cloud', 'gcp').lower()
        region_str = config.get('region', 'us-central1-gcp')
        
        # Convert strings to enums
        cloud = CloudProvider.GCP
        if cloud_str == 'azure':
            cloud = CloudProvider.AZURE
        
        region = Region.US_EAST_1
        region_mapping = {
            'us-east-1': Region.US_EAST_1,
            'us-west-2': Region.US_WEST_2,
            'eu-west-1': Region.EU_WEST_1,
            'ap-southeast-1': Region.AP_SOUTHEAST_1,
            'us-central1-gcp': Region.US_CENTRAL1_GCP,
            'eu-west1-gcp': Region.EU_WEST1_GCP,
            'eastus-azure': Region.EASTUS_AZURE,
            'westeurope-azure': Region.WESTEUROPE_AZURE
        }
        region = region_mapping.get(region_str, Region.US_EAST_1)
        
        return PineconeConfig(
            api_key=api_key,
            index_name=index_name,
            dimension=dimension,
            namespace=namespace,
            cloud=cloud,
            region=region,
            metric=config.get('metric', 'cosine'),
            use_grpc=config.get('use_grpc', True),
            batch_size=config.get('batch_size', 100),
            delete_batch_size=config.get('delete_batch_size', 1000),
            timeout=config.get('timeout', 30),
            max_retries=config.get('max_retries', 3)
        )
    
    def add_embeddings(self, embeddings: List[List[float]], texts: List[str], 
                      metadata: List[Dict[str, Any]] = None, ids: List[str] = None):
        """Add embeddings to Pinecone"""
        try:
            self.store.add_embeddings(
                embeddings=embeddings,
                texts=texts,
                metadata=metadata,
                ids=ids
            )
        except PineconeError as e:
            logger.error(f"Pinecone operation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in add_embeddings: {e}")
            raise
    
    def search(self, query_embedding: List[float], k: int = 10, 
               filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for similar embeddings"""
        try:
            return self.store.search(
                query_embedding=query_embedding,
                k=k,
                filter_metadata=filter_metadata
            )
        except PineconeError as e:
            logger.error(f"Pinecone search failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in search: {e}")
            return []
    
    def delete(self, ids: List[str]):
        """Delete embeddings by IDs"""
        try:
            self.store.delete(ids)
        except PineconeError as e:
            logger.error(f"Pinecone delete failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in delete: {e}")
            raise
    
    def update_metadata(self, ids: List[str], metadata: List[Dict[str, Any]]):
        """Update metadata for embeddings"""
        try:
            self.store.update_metadata(ids, metadata)
        except PineconeError as e:
            logger.error(f"Pinecone update_metadata failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in update_metadata: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        return self.store.get_stats()
    
    def health_check(self) -> bool:
        """Perform health check"""
        return self.store.health_check()
    
    def delete_namespace(self, namespace: str = None):
        """Delete all vectors in namespace"""
        self.store.delete_namespace(namespace)
    
    def close(self):
        """Clean up resources"""
        if hasattr(self.store, 'close'):
            self.store.close()


class UserConfigurationBuilder:
    """Builder class for creating user-specific embedding configurations"""
    
    def __init__(self, user_preferences: UserEmbeddingPreferences):
        self.preferences = user_preferences
        self.config = EmbeddingConfig.get_default_config()
        
    def build(self) -> Dict[str, Any]:
        """
        Build complete user configuration
        
        Returns:
            Dict containing configuration for all embedding models and vector stores
            
        Raises:
            ConfigurationError: If configuration building fails
        """
        try:
            logger.debug(f"Building configuration for {self.preferences}")
            
            # Step 1: Determine embedding model and dimensions
            embedding_model_config = self._resolve_embedding_model_config()
            
            # Step 2: Resolve API keys from multiple sources
            api_keys = self._resolve_api_keys()
            
            # Step 3: Configure each component separately
            self._configure_embedding_models(embedding_model_config, api_keys)
            self._configure_vector_stores(embedding_model_config, api_keys)
            
            # Step 4: Validate final configuration
            self._validate_configuration()
            
            logger.info(f"Successfully built configuration for user {self.preferences.user_id}")
            return self.config
            
        except Exception as e:
            logger.error(f"Failed to build config for user {self.preferences.user_id}: {e}")
            raise ConfigurationError(f"Configuration build failed: {str(e)}") from e
    
    def _resolve_embedding_model_config(self) -> EmbeddingModelConfig:
        """
        Resolve embedding model configuration and dimensions
        
        Returns:
            EmbeddingModelConfig with resolved model details
        """
        model_name = self.preferences.default_embedding_model
        
        # Validate model exists in configuration
        if model_name not in self.config:
            logger.warning(f"Unknown embedding model '{model_name}', falling back to 'sentence_transformer'")
            model_name = 'sentence_transformer'
        
        model_config = self.config[model_name]
        actual_model_name = model_config['model_name']
        
        # Look up dimension for this specific model
        dimension = EmbeddingConfig.get_model_dimensions().get(actual_model_name, 384)
        
        embedding_config = EmbeddingModelConfig(
            wrapper_name=model_name,
            model_name=actual_model_name,
            dimension=dimension,
            model_type=model_config.get('type', 'sentence_transformer')
        )
        
        logger.debug(f"Resolved embedding model: {embedding_config}")
        return embedding_config
    
    def _resolve_api_keys(self) -> Dict[str, Optional[str]]:
        """
        Resolve API keys from environment variables only
        
        Returns:
            Dict mapping service names to API keys
        """
        api_keys = {
            'openai': os.getenv('OPENAI_API_KEY'),
            'pinecone': os.getenv('PINECONE_API_KEY')
        }
        
        # Log which keys were found (without exposing the actual keys)
        for service, key in api_keys.items():
            status = "found" if key else "not found"
            logger.debug(f"{service.upper()} API key: {status} (source: environment)")
        
        return api_keys
    
    def _configure_embedding_models(self, model_config: EmbeddingModelConfig, api_keys: Dict[str, Optional[str]]):
        """
        Configure embedding model settings based on user preferences
        
        Args:
            model_config: Resolved embedding model configuration
            api_keys: Resolved API keys for external services
        """
        # Always update sentence transformer with correct dimension
        self.config['sentence_transformer']['dimension'] = model_config.dimension
        
        # Configure OpenAI if API key is available
        if api_keys['openai']:
            self.config['openai_ada']['api_key'] = api_keys['openai']
            
            # OpenAI models have fixed dimensions - look them up
            openai_model = self.config['openai_ada']['model_name']
            openai_dimension = EmbeddingConfig.get_model_dimensions().get(openai_model, 1536)
            self.config['openai_ada']['dimension'] = openai_dimension
            
            logger.debug(f"Configured OpenAI model {openai_model} with dimension {openai_dimension}")
        else:
            logger.debug("No OpenAI API key found, OpenAI embeddings will not be available")
    
    def _configure_vector_stores(self, model_config: EmbeddingModelConfig, api_keys: Dict[str, Optional[str]]):
        """
        Configure all vector store settings with user-specific isolation
        
        Args:
            model_config: Resolved embedding model configuration  
            api_keys: Resolved API keys for external services
        """
        user_id = self.preferences.user_id
        dimension = model_config.dimension
        
        # Configure each vector store
        self._configure_chroma_store(user_id, model_config)
        self._configure_faiss_store(user_id, dimension)
        self._configure_pinecone_store(user_id, dimension, api_keys['pinecone'])
    
    def _configure_chroma_store(self, user_id: str, model_config: EmbeddingModelConfig):
        """
        Configure ChromaDB with user-specific collection
        
        Collection naming pattern: user_{user_id}_{embedding_model}
        This ensures users with different embedding models get separate collections
        """
        collection_name = f"user_{user_id}_{model_config.wrapper_name}"
        
        self.config['chroma'].update({
            'collection_name': collection_name,
            'model_name': model_config.model_name,
            'type': model_config.model_type
        })
        
        logger.debug(f"ChromaDB configured: collection='{collection_name}'")
    
    def _configure_faiss_store(self, user_id: str, dimension: int):
        """
        Configure FAISS with user-specific files
        
        Each user gets their own FAISS index and metadata files
        """
        self.config['faiss'].update({
            'collection_name': f"user_{user_id}",
            'dimension': dimension,
            'index_file': f"./faiss_{user_id}.index",
            'metadata_file': f"./faiss_{user_id}_metadata.json"
        })
        
        logger.debug(f"FAISS configured: user={user_id}, dimension={dimension}")
    
    def _configure_pinecone_store(self, user_id: str, dimension: int, api_key: Optional[str]):
        """
        Configure Pinecone with proper multi-tenant architecture
        
        CRITICAL DESIGN DECISION:
        - Index Name: SHARED across all users (cost-effective)
        - Namespace: UNIQUE per user (data isolation)
        
        This provides complete data isolation while minimizing costs
        """
        # Multi-tenant architecture constants
        SHARED_INDEX_NAME = "knowledge-base-prod"  # Same for ALL users
        user_namespace = f"user_{user_id}"         # Unique per user
        
        self.config['pinecone'].update({
            'api_key': api_key,
            'index_name': SHARED_INDEX_NAME,
            'namespace': user_namespace,
            'dimension': dimension
        })
        
        logger.debug(
            f"Pinecone configured: index='{SHARED_INDEX_NAME}' (shared), "
            f"namespace='{user_namespace}' (isolated), dimension={dimension}"
        )
        
        if not api_key:
            logger.warning(f"No Pinecone API key found for user {user_id}, Pinecone will not be available")
    
    def _validate_configuration(self):
        """
        Validate the final configuration for common issues
        
        Raises:
            ConfigurationError: If validation fails
        """
        # Check that required fields are present
        required_sections = ['sentence_transformer', 'openai_ada', 'chroma', 'faiss', 'pinecone']
        for section in required_sections:
            if section not in self.config:
                raise ConfigurationError(f"Missing required configuration section: {section}")
        
        # Validate dimensions are consistent
        st_dim = self.config['sentence_transformer'].get('dimension', 0)
        faiss_dim = self.config['faiss'].get('dimension', 0)
        
        if st_dim != faiss_dim:
            logger.warning(f"Dimension mismatch: SentenceTransformer={st_dim}, FAISS={faiss_dim}")
        
        # Validate collection names don't contain problematic characters
        chroma_collection = self.config['chroma'].get('collection_name', '')
        if not chroma_collection or ' ' in chroma_collection:
            raise ConfigurationError(f"Invalid ChromaDB collection name: '{chroma_collection}'")
        
        logger.debug("Configuration validation passed")
    
    def get_fallback_config(self) -> Dict[str, Any]:
        """
        Get safe fallback configuration if building fails
        
        Returns:
            Minimal safe configuration that allows system to function
        """
        user_id = self.preferences.user_id
        
        fallback_config = EmbeddingConfig.get_default_config()
        
        # Apply minimal user-specific settings for data isolation
        fallback_config['chroma']['collection_name'] = f"user_{user_id}"
        fallback_config['faiss']['collection_name'] = f"user_{user_id}"
        fallback_config['faiss']['index_file'] = f"./faiss_{user_id}.index"
        fallback_config['faiss']['metadata_file'] = f"./faiss_{user_id}_metadata.json"
        
        # Pinecone fallback with proper multi-tenancy
        fallback_config['pinecone'].update({
            'api_key': os.getenv('PINECONE_API_KEY'),
            'index_name': "knowledge-base-prod",  # Shared index
            'namespace': f"user_{user_id}"        # Isolated namespace
        })
        
        logger.warning(f"Using fallback configuration for user {user_id}")
        return fallback_config


class EmbeddingManager:
    """
    Manager for handling embeddings and vector stores with improved architecture
    
    Responsibilities:
    1. User configuration management
    2. Embedding model initialization  
    3. Vector store initialization
    4. Document processing coordination
    5. Search coordination
    """
    
    def __init__(self, user_id: str, config: Optional[Dict[str, Any]] = None):        
        # Step 1: Validate and sanitize user input
        self.user_id = self._validate_and_sanitize_user_id(user_id)
        
        logger.info(f"Initializing EmbeddingManager for user '{self.user_id}'")
        
        # Step 2: Load user's stored preferences from database
        self.knowledge_base_config = self._load_knowledge_base_config()
        
        # Step 3: Build user-specific configuration
        self.config = self._build_user_configuration(config)
        
        # Step 4: Initialize system components
        self.embedding_models = {}
        self.vector_stores = {}
        
        self._initialize_components()
        
        logger.info(f"EmbeddingManager initialized for user '{self.user_id}' with {len(self.embedding_models)} models and {len(self.vector_stores)} stores")
    
    def _validate_and_sanitize_user_id(self, user_id: str) -> str:
        """
        Validate and sanitize user ID for safe usage
        
        Args:
            user_id: Raw user ID from input
            
        Returns:
            Sanitized user ID safe for use in file names and collections
            
        Raises:
            ValueError: If user ID is invalid
        """
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")
        
        original_id = user_id
        sanitized_id = user_id.strip()
        
        # Remove/replace problematic characters
        sanitized_id = sanitized_id.replace(' ', '_')
        sanitized_id = sanitized_id.replace('/', '_')
        sanitized_id = sanitized_id.replace('\\', '_')
        
        # Ensure not empty after sanitization
        if not sanitized_id:
            raise ValueError("user_id cannot be empty after sanitization")
        
        if sanitized_id != original_id:
            logger.info(f"Sanitized user_id: '{original_id}' -> '{sanitized_id}'")
        
        return sanitized_id
    
    def _load_knowledge_base_config(self):
        """
        Load user's knowledge base configuration from database
        
        Returns:
            KnowledgeBaseConfig object or None if not found
        """
        try:
            config = KnowledgeBaseConfig.objects.get(user_id=self.user_id)
            logger.debug(f"Loaded KnowledgeBaseConfig for user '{self.user_id}'")
            return config
        except KnowledgeBaseConfig.DoesNotExist:
            logger.info(f"No KnowledgeBaseConfig found for user '{self.user_id}', will use defaults")
            return None
        except Exception as e:
            logger.error(f"Error loading KnowledgeBaseConfig for user '{self.user_id}': {e}")
            return None
    
    def _build_user_configuration(self, override_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Build user-specific configuration using builder pattern
        
        Args:
            override_config: Optional configuration overrides from caller
            
        Returns:
            Complete configuration dictionary for this user
        """
        try:
            # Step 1: Extract user preferences from database
            user_preferences = UserEmbeddingPreferences.from_knowledge_base_config(
                self.user_id, 
                self.knowledge_base_config
            )
            
            # Step 2: Build base configuration using builder pattern
            builder = UserConfigurationBuilder(user_preferences)
            base_config = builder.build()
            
            # Step 3: Apply any configuration overrides
            if override_config:
                final_config = self._merge_configurations(base_config, override_config)
                logger.info(f"Applied configuration overrides for user '{self.user_id}'")
                return final_config
            
            return base_config
            
        except ConfigurationError as e:
            logger.error(f"Configuration build failed for user '{self.user_id}': {e}")
            # Fall back to safe defaults
            builder = UserConfigurationBuilder(
                UserEmbeddingPreferences(user_id=self.user_id)
            )
            return builder.get_fallback_config()
        except Exception as e:
            logger.error(f"Unexpected error building config for user '{self.user_id}': {e}")
            # Return absolute fallback
            return self._get_emergency_fallback_config()
    
    def _merge_configurations(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two configuration dictionaries
        
        Args:
            base: Base configuration
            override: Override configuration (takes precedence)
            
        Returns:
            Merged configuration dictionary
        """
        result = dict(base)
        
        for key, value in override.items():
            if (key in result and 
                isinstance(result[key], dict) and 
                isinstance(value, dict)):
                # Recursively merge nested dictionaries
                result[key] = self._merge_configurations(result[key], value)
            else:
                # Override the value completely
                result[key] = value
                logger.debug(f"Configuration override: {key} = {type(value).__name__}")
        
        return result
    
    def _get_emergency_fallback_config(self) -> Dict[str, Any]:
        """
        Get absolute emergency fallback configuration
        
        This is used when even the builder fallback fails
        """
        logger.critical(f"Using emergency fallback config for user '{self.user_id}'")
        
        return {
            'sentence_transformer': {
                'type': 'sentence_transformer',
                'model_name': 'all-MiniLM-L6-v2',
                'dimension': 384,
                'max_tokens': 512
            },
            'openai_ada': {
                'type': 'openai',
                'model_name': 'text-embedding-ada-002',
                'dimension': 1536,
                'max_tokens': 8192,
                'api_key': os.getenv('OPENAI_API_KEY')
            },
            'chroma': {
                'persist_directory': './chroma_db',
                'collection_name': f"user_{self.user_id}_emergency"
            },
            'faiss': {
                'dimension': 384,
                'collection_name': f"user_{self.user_id}",
                'index_file': f"./faiss_{self.user_id}.index",
                'metadata_file': f"./faiss_{self.user_id}_metadata.json"
            },
            'pinecone': {
                'api_key': os.getenv('PINECONE_API_KEY'),
                'index_name': 'knowledge-base-prod',
                'namespace': f"user_{self.user_id}",
                'dimension': 384,
                'metric': 'cosine',
                'use_grpc': True,
                'batch_size': 100
            }
        }
    
    def _initialize_components(self):
        """Initialize embedding models and vector stores"""
        try:
            logger.debug(f"Initializing components for user '{self.user_id}'")
            
            # Initialize embedding models first (vector stores may depend on them)
            self._initialize_embedding_models()
            
            # Then initialize vector stores
            self._initialize_vector_stores()
            
            logger.info(f"Component initialization complete for user '{self.user_id}'")
            
        except Exception as e:
            logger.error(f"Component initialization failed for user '{self.user_id}': {e}")
            raise
    
    def _initialize_embedding_models(self):
        """Initialize embedding models"""
        logger.info(f"Initializing embedding models for user {self.user_id}")
        
        # Default sentence transformer model
        try:
            self.embedding_models['sentence_transformer'] = SentenceTransformerEmbedding(
                self.config.get('sentence_transformer', {})
            )
            logger.info(f"Initialized SentenceTransformer model: {self.embedding_models['sentence_transformer'].model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize SentenceTransformer: {e}")
        
        # OpenAI embedding model if API key is available
        openai_config = self.config.get('openai_ada', {})
        logger.info(f"Initializing OpenAI embedding model with config: {openai_config}")
        if openai_config.get('api_key'):
            try:
                self.embedding_models['openai_ada'] = OpenAIEmbedding(openai_config)
                logger.info("OpenAI embedding model initialized")
            except ImportError:
                logger.warning("OpenAI library not available")
            except Exception as e:
                logger.error(f"Error initializing OpenAI embedding model: {e}")
    
    def _initialize_vector_stores(self):
        """Initialize vector stores"""
        # ChromaDB vector store
        try:
            chroma_config = self.config.get('chroma', {})
            logger.info(f"Initializing ChromaDB for user {self.user_id} with collection {chroma_config['collection_name']} and model {chroma_config.get('model_name')}")
            self.vector_stores['chroma'] = ChromaVectorStore(chroma_config)
            logger.info(f"ChromaDB initialized with collection: {chroma_config['collection_name']}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")

        # FAISS vector store if available
        if FAISS_AVAILABLE:
            try:
                faiss_config = self.config.get('faiss', {})
                self.vector_stores['faiss'] = FAISSVectorStore(faiss_config)
                logger.info("FAISS initialized")
            except Exception as e:
                logger.error(f"Failed to initialize FAISS: {e}")
        
        logger.info("PINECONE AVAILABLE: " + str(PINECONE_AVAILABLE))

        # Pinecone vector store if available (PRODUCTION VERSION)
        if PINECONE_AVAILABLE:
            pinecone_config = self.config.get('pinecone', {})
            api_key = pinecone_config.get('api_key') or os.getenv('PINECONE_API_KEY')
            
            if api_key:
                try:
                    self.vector_stores['pinecone'] = PineconeVectorStore(pinecone_config)
                    logger.info(f"Pinecone initialized with index: {pinecone_config.get('index_name')}")
                except Exception as e:
                    logger.error(f"Failed to initialize Pinecone: {e}")
            else:
                logger.warning("Pinecone API key not found, skipping Pinecone initialization")
    
    def get_embedding_model(self, model_name: str) -> Optional[BaseEmbeddingModel]:
        """Get embedding model by name"""
        return self.embedding_models.get(model_name)
    
    def get_vector_store(self, store_name: str) -> Optional[BaseVectorStore]:
        """Get vector store by name"""
        return self.vector_stores.get(store_name)
    
    def add_document_embeddings(self, document_id: str, chunks: List[str], 
                              metadata: Dict[str, Any] = None,
                              embedding_model: str = None,
                              vector_store: str = None):
        """Add document embeddings to vector store"""
        try:
            logger.info(json.dumps({
                "event": "AddDocumentEmbeddings",
                "knowledge_base_config": str(self.knowledge_base_config),
                "embedding_model": embedding_model,
                "vector_store": vector_store,
                "chunks": chunks,
            }, default=str))

            if not embedding_model:
                embedding_model = self.knowledge_base_config.default_embedding_model if self.knowledge_base_config else 'sentence_transformer'
            
            if not vector_store:
                vector_store = self.knowledge_base_config.default_vector_store if self.knowledge_base_config else 'chroma'

            logger.info(f"Adding document embeddings for {document_id} using model {embedding_model} and store {vector_store}")

            # Get embedding model and vector store
            emb_model = self.get_embedding_model(embedding_model)
            vec_store = self.get_vector_store(vector_store)

            if not emb_model:
                raise ValueError(f"Embedding model '{embedding_model}' not available")
            
            if not vec_store:
                raise ValueError(f"Vector store '{vector_store}' not available")
            
            embeddings = emb_model.encode(chunks)
            embeddings = np.array(embeddings)
            if len(embeddings.shape) == 1:
                embeddings = [embeddings.tolist()]
            else:
                embeddings = embeddings.tolist()
            
            # Prepare metadata
            chunk_metadata = []
            for i, chunk in enumerate(chunks):
                chunk_meta = {
                    'document_id': document_id,
                    'chunk_index': i,
                    'user_id': self.user_id,
                    **(metadata or {})
                }
                chunk_metadata.append(chunk_meta)
            
            # Generate IDs
            chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
            
            logger.info(f"Chunk metadata for document {document_id}: {json.dumps(chunk_metadata, indent=2, default=str)}")
            # Add to vector store
            vec_store.add_embeddings(embeddings, chunks, chunk_metadata, chunk_ids)
            
            logger.info(f"Added {len(chunks)} chunks for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error adding document embeddings: {e}")
            raise
    
    def search_similar_documents(self, query: str, k: int = 10,
                               filter_metadata: Dict[str, Any] = None,
                               embedding_model: str = None,
                               vector_store: str = None) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            logger.info(json.dumps({
                "event": "SearchSimilarDocuments",
                "knowledge_base_config": str(self.knowledge_base_config),
                "embedding_model": embedding_model,
                "vector_store": vector_store
            }, default=str))

            if not embedding_model:
                embedding_model = self.knowledge_base_config.default_embedding_model if self.knowledge_base_config else 'sentence_transformer'
            
            if not vector_store:
                vector_store = self.knowledge_base_config.default_vector_store if self.knowledge_base_config else 'chroma'
                
            # Get embedding model and vector store
            emb_model = self.get_embedding_model(embedding_model)
            vec_store = self.get_vector_store(vector_store)
            
            logger.info(f"Searching similar documents for query: '{query}' using model {embedding_model} and store {vector_store}")
            if not emb_model or not vec_store:
                raise ValueError(f"Embedding model '{embedding_model}' or vector store '{vector_store}' not available")
            
            # Generate query embedding
            query_embedding = emb_model.encode(query)
            if hasattr(query_embedding, 'tolist'):
                query_embedding = query_embedding.tolist()
            
            # # Add user filter
            # if not filter_metadata:
            #     filter_metadata = {}
            # filter_metadata['user_id'] = self.user_id
            
            # Search vector store
            results = vec_store.search(query_embedding, k, filter_metadata)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {e}")
            return []
    
    def delete_document_embeddings(self, document_id: str, vector_store: str = 'chroma'):
        """Delete document embeddings from vector store"""
        try:
            vec_store = self.get_vector_store(vector_store)
            if not vec_store:
                raise ValueError(f"Vector store '{vector_store}' not available")
            
            # Find all chunk IDs for this document
            # This is a simplified approach - in practice, you might want to search first
            # to find all chunks for this document
            search_results = self.search_similar_documents(
                query="dummy", k=1000, 
                filter_metadata={'document_id': document_id},
                vector_store=vector_store
            )
            
            chunk_ids = [result['id'] for result in search_results]
            
            if chunk_ids:
                vec_store.delete(chunk_ids)
                logger.info(f"Deleted {len(chunk_ids)} chunks for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error deleting document embeddings: {e}")
            raise
    
    def update_document_metadata(self, document_id: str, metadata: Dict[str, Any],
                               vector_store: str = 'chroma'):
        """Update metadata for document chunks"""
        try:
            vec_store = self.get_vector_store(vector_store)
            if not vec_store:
                raise ValueError(f"Vector store '{vector_store}' not available")
            
            # Find all chunk IDs for this document
            search_results = self.search_similar_documents(
                query="dummy", k=1000,
                filter_metadata={'document_id': document_id},
                vector_store=vector_store
            )
            
            chunk_ids = [result['id'] for result in search_results]
            
            if chunk_ids:
                # Update metadata for all chunks
                updated_metadata = []
                for result in search_results:
                    chunk_meta = result['metadata'].copy()
                    chunk_meta.update(metadata)
                    updated_metadata.append(chunk_meta)
                
                vec_store.update_metadata(chunk_ids, updated_metadata)
                logger.info(f"Updated metadata for {len(chunk_ids)} chunks of document {document_id}")
            
        except Exception as e:
            logger.error(f"Error updating document metadata: {e}")
            raise
    
    def health_check(self) -> Dict[str, bool]:
        """Perform health check on all components"""
        health_status = {}
        
        # Check embedding models
        for name, model in self.embedding_models.items():
            try:
                # Try a simple encoding
                test_embedding = model.encode("test")
                health_status[f"embedding_{name}"] = True
            except Exception as e:
                logger.error(f"Health check failed for embedding model {name}: {e}")
                health_status[f"embedding_{name}"] = False
        
        # Check vector stores
        for name, store in self.vector_stores.items():
            try:
                if hasattr(store, 'health_check'):
                    health_status[f"store_{name}"] = store.health_check()
                else:
                    # Try a simple operation for stores without health_check
                    if hasattr(store, 'get_stats'):
                        store.get_stats()
                    health_status[f"store_{name}"] = True
            except Exception as e:
                logger.error(f"Health check failed for vector store {name}: {e}")
                health_status[f"store_{name}"] = False
        
        return health_status
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Get comprehensive stats for the user"""
        stats = {
            'user_id': self.user_id,
            'available_models': list(self.embedding_models.keys()),
            'available_stores': list(self.vector_stores.keys()),
            'store_stats': {}
        }
        
        # Get stats from each store
        for name, store in self.vector_stores.items():
            try:
                if hasattr(store, 'get_stats'):
                    stats['store_stats'][name] = store.get_stats()
                else:
                    stats['store_stats'][name] = {'status': 'available'}
            except Exception as e:
                stats['store_stats'][name] = {'error': str(e)}
        
        return stats
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current configuration for debugging/monitoring
        
        Returns:
            Dictionary with configuration summary (API keys redacted)
        """
        summary = {
            'user_id': self.user_id,
            'available_models': list(self.embedding_models.keys()),
            'available_stores': list(self.vector_stores.keys()),
            'preferred_model': getattr(self.knowledge_base_config, 'default_embedding_model', 'sentence_transformer'),
            'preferred_store': getattr(self.knowledge_base_config, 'default_vector_store', 'chroma'),
            'chroma_collection': self.config.get('chroma', {}).get('collection_name'),
            'pinecone_index': self.config.get('pinecone', {}).get('index_name'),
            'pinecone_namespace': self.config.get('pinecone', {}).get('namespace'),
            'has_openai_key': bool(self.config.get('openai_ada', {}).get('api_key')),
            'has_pinecone_key': bool(self.config.get('pinecone', {}).get('api_key'))
        }
        
        return summary
    
    def close(self):
        """Clean up resources"""
        for store in self.vector_stores.values():
            if hasattr(store, 'close'):
                try:
                    store.close()
                except Exception as e:
                    logger.error(f"Error closing vector store: {e}")
        
        logger.info(f"EmbeddingManager closed for user {self.user_id}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class EmbeddingConfig:
    """Configuration for embedding models and vector stores"""
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'sentence_transformer': {
                'type': 'sentence_transformer',
                'model_name': 'all-MiniLM-L6-v2',
                'dimension': 384,
                'max_tokens': 512
            },
            'openai_ada': {
                'type': 'openai',
                'model_name': 'text-embedding-ada-002',
                'dimension': 1536,
                'max_tokens': 8192
            },
            'chroma': {
                'persist_directory': './chroma_db'
            },
            'faiss': {
                'dimension': 384,
                'index_file': './faiss_index.index',
                'metadata_file': './faiss_metadata.json'
            },
            'pinecone': {
                'index_name': 'knowledge-base-prod',  # Single shared index
                'dimension': 1536,
                'metric': 'cosine',
                'region': 'us-east-1',
                'cloud': 'gcp',
                'use_grpc': True,
                'batch_size': 100,
                'namespace': '',  # Will be set per user
                'delete_batch_size': 1000
            }
        }
    
    @staticmethod
    def get_model_dimensions() -> Dict[str, int]:
        """Get dimensions for different embedding models"""
        return {
            'all-MiniLM-L6-v2': 384,
            'all-MiniLM-L12-v2': 384,
            'all-mpnet-base-v2': 768,
            'all-distilroberta-v1': 768,
            'text-embedding-ada-002': 1536,
            'text-embedding-3-small': 1536,
            'text-embedding-3-large': 3072
        }
    
    @staticmethod
    def get_recommended_models() -> Dict[str, Dict[str, Any]]:
        """Get recommended models for different use cases"""
        return {
            'general': {
                'model': 'all-MiniLM-L6-v2',
                'dimension': 384,
                'description': 'Good balance of speed and quality'
            },
            'high_quality': {
                'model': 'all-mpnet-base-v2',
                'dimension': 768,
                'description': 'Better quality, slower'
            },
            'openai': {
                'model': 'text-embedding-ada-002',
                'dimension': 1536,
                'description': 'OpenAI embedding model'
            },
            'multilingual': {
                'model': 'paraphrase-multilingual-MiniLM-L12-v2',
                'dimension': 384,
                'description': 'Supports multiple languages'
            }
        }


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # Try to break at sentence boundary
        chunk = text[start:end]
        last_sentence = chunk.rfind('.')
        if last_sentence > chunk_size // 2:
            chunk = chunk[:last_sentence + 1]
            end = start + last_sentence + 1
        
        chunks.append(chunk)
        start = end - overlap
    
    return chunks


def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """Calculate cosine similarity between two embeddings"""
    import numpy as np
    
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    # Cosine similarity
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def get_token_count(text: str, model: str = 'gpt-3.5-turbo') -> int:
    """Get approximate token count for text"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except:
        # Fallback: approximate 4 characters per token
        return len(text) // 4


def _convert_uuids(obj):
    """Recursively convert UUID objects to strings in a dict or list."""
    if isinstance(obj, dict):
        return {k: _convert_uuids(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_uuids(i) for i in obj]
    elif isinstance(obj, uuid.UUID):
        return str(obj)
    else:
        return obj


def create_pinecone_store(
    api_key: str,
    index_name: str,
    dimension: int,
    namespace: str = "",
    **kwargs
) -> PineconeVectorStore:
    """Factory function to create PineconeVectorStore with validation"""
    
    # Validate required parameters
    if not api_key:
        raise PineconeConfigError("API key is required")
    
    if not index_name:
        raise PineconeConfigError("Index name is required")
    
    if not isinstance(dimension, int) or dimension <= 0:
        raise PineconeConfigError("Dimension must be a positive integer")
    
    # Set defaults
    config_dict = {
        'api_key': api_key,
        'index_name': index_name,
        'dimension': dimension,
        'namespace': namespace,
        **kwargs
    }
    
    # Handle enum conversions
    if 'cloud' in config_dict and isinstance(config_dict['cloud'], str):
        config_dict['cloud'] = CloudProvider(config_dict['cloud'])
    
    if 'region' in config_dict and isinstance(config_dict['region'], str):
        config_dict['region'] = Region(config_dict['region'])
    
    return PineconeVectorStore(config_dict)


def example_usage():
    """Example showing how to use the production system"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize manager for user
        with EmbeddingManager(user_id="user_123") as manager:
            
            # Health check
            health = manager.health_check()
            print(f"Health status: {health}")
            
            # Get configuration summary
            summary = manager.get_configuration_summary()
            print(f"Configuration: {json.dumps(summary, indent=2)}")
            
            # Add documents
            chunks = [
                "This is the first document chunk about machine learning.",
                "This is the second chunk about natural language processing.",
                "This chunk discusses vector databases and embeddings."
            ]
            
            manager.add_document_embeddings(
                document_id="doc_1",
                chunks=chunks,
                metadata={'category': 'ml', 'source': 'tutorial'},
                embedding_model="sentence_transformer",
                vector_store="pinecone"  # Uses production Pinecone with proper multi-tenancy
            )
            
            # Search
            results = manager.search_similar_documents(
                query="What is machine learning?",
                k=3,
                filter_metadata={'category': 'ml'},
                embedding_model="sentence_transformer",
                vector_store="pinecone"
            )
            
            print(f"Search results: {len(results)}")
            for result in results:
                print(f"- {result['text'][:50]}... (score: {result.get('score', 0):.3f})")
            
            # Get stats
            stats = manager.get_user_stats()
            print(f"User stats: {json.dumps(stats, indent=2, default=str)}")
            
    except Exception as e:
        logger.error(f"Example failed: {e}")
        raise


if __name__ == "__main__":
    example_usage()

def _sanitize_filter_for_pinecone(obj):
    """Recursively convert UUIDs and numpy types to JSON-serializable types for Pinecone filters."""
    import uuid
    import numpy as np
    if isinstance(obj, dict):
        return {k: _sanitize_filter_for_pinecone(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_filter_for_pinecone(i) for i in obj]
    elif isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    else:
        return obj
    
# TODO: move this to a separate utility module
def build_user_or_doc_filter(user_id, data_source_ids=None, document_ids=None):
    clauses = []
    if data_source_ids:
        clauses.append({"data_source_id": {"$in": data_source_ids}})
    if document_ids:
        clauses.append({"document_id": {"$in": document_ids}})
    if not clauses:
        return {"user_id": {"$eq": user_id}}
    return {
        "$and": [
            {"user_id": {"$eq": user_id}},
            {"$or": clauses}
        ]
    }