# knowledge_base/ai_agents.py

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import time


# AI/ML libraries
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False

# LangChain for advanced agent capabilities
try:
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain.tools import Tool
    from langchain.schema import Document as LangchainDocument
    from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
    from langchain_community.callbacks.manager import get_openai_callback
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

from django.contrib.auth.models import User
from django.utils import timezone

from .models import AIAgent, Conversation, Message, Document, AgentUsage
from .embeddings import EmbeddingManager, build_user_or_doc_filter
from .utils import RateLimiter

logger = logging.getLogger(__name__)


class BaseAIModel(ABC):
    """Base class for AI models"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get('model_name', 'default')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 1000)
        self.api_key = config.get('api_key')
    
    @abstractmethod
    def generate_response(self, messages: List[Dict[str, str]], 
                               context: str = "", **kwargs) -> Dict[str, Any]:
        """Generate AI response"""
        pass
    
    def format_context(self, context_docs: List[Dict[str, Any]]) -> str:
        """Format context documents for the model"""
        if not context_docs:
            return ""
        
        context_parts = []
        for doc in context_docs:
            context_parts.append(f"Document: {doc.get('title', 'Unknown')}")
            context_parts.append(f"Content: {doc.get('content', doc.get('text', ''))}")
            context_parts.append("---")
        
        return "\n".join(context_parts)


class OpenAIModel(BaseAIModel):
    """OpenAI GPT model"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available")
        
        if self.api_key:
            openai.api_key = self.api_key
        
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def generate_response(self, messages: List[Dict[str, str]], 
                        context: str = "", **kwargs) -> Dict[str, Any]:
        """Generate response using OpenAI API (synchronous version)"""
        try:
            # Add context to system message if provided
            if context:
                context_message = {
                    "role": "system",
                    "content": f"Use the following context to answer the user's question:\n\n{context}"
                }
                messages = [context_message] + messages

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            )

            return {
                'content': response.choices[0].message.content,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                'model': response.model,
                'finish_reason': response.choices[0].finish_reason
            }

        except Exception as e:
            logger.error(f"Error generating OpenAI response: Model={self.model_name}, Error={e}")
            logger.error(f"Error type: {type(e).__name__}, Error details: {str(e)}")
            
            # Parse OpenAI API errors for better user feedback
            error_message = str(e)
            error_type = 'model'
            
            # Check for quota/billing errors
            if 'insufficient_quota' in error_message.lower() or '429' in error_message:
                error_type = 'quota'
                error_message = "You have exceeded your OpenAI API quota. Please check your OpenAI billing and plan details at https://platform.openai.com/account/billing"
            elif 'invalid_api_key' in error_message.lower() or 'authentication' in error_message.lower():
                error_type = 'authentication'
                error_message = "Invalid OpenAI API key. Please check your API key configuration."
            elif 'rate_limit' in error_message.lower():
                error_type = 'rate_limit'
                error_message = "Rate limit exceeded. Please try again in a moment."
            
            return {
                'error': error_message,
                'error_type': error_type,
                'content': f"Error generating response: {error_message}"
            }
    
class AnthropicModel(BaseAIModel):
    """Anthropic Claude model"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic library not available")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def generate_response(self, messages: List[Dict[str, str]], 
                        context: str = "", **kwargs) -> Dict[str, Any]:
        """Generate response using Anthropic API (synchronous version)"""
        try:
            # Convert messages to Anthropic format
            anthropic_messages = []
            system_message = ""
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message += msg['content'] + "\n"
                else:
                    anthropic_messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            # Add context to system message
            if context:
                system_message += f"\nUse the following context to answer:\n{context}"
            
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_message,
                messages=anthropic_messages
            )
            
            return {
                'content': response.content[0].text,
                'usage': {
                    'prompt_tokens': response.usage.input_tokens,
                    'completion_tokens': response.usage.output_tokens,
                    'total_tokens': response.usage.input_tokens + response.usage.output_tokens
                },
                'model': response.model,
                'finish_reason': response.stop_reason
            }
            
        except Exception as e:
            logger.error(f"Error generating Anthropic response: {e}")
            return {
                'error': str(e),
                'content': f"Error generating response: {e}"
            }

class CohereModel(BaseAIModel):
    """Cohere model"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not COHERE_AVAILABLE:
            raise ImportError("Cohere library not available")
        
        self.client = cohere.Client(api_key=self.api_key)

    def generate_response(self, messages: List[Dict[str, str]], 
                        context: str = "", **kwargs) -> Dict[str, Any]:
        """Generate response using Cohere API (synchronous version)"""
        try:
            # Convert messages to a single prompt
            prompt_parts = []
            for msg in messages:
                if msg['role'] == 'system':
                    prompt_parts.append(f"System: {msg['content']}")
                elif msg['role'] == 'user':
                    prompt_parts.append(f"User: {msg['content']}")
                elif msg['role'] == 'assistant':
                    prompt_parts.append(f"Assistant: {msg['content']}")
            
            if context:
                prompt_parts.insert(0, f"Context: {context}")
            
            prompt = "\n".join(prompt_parts)
            
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                **kwargs
            )
            
            return {
                'content': response.generations[0].text,
                'usage': {
                    'prompt_tokens': len(prompt.split()),
                    'completion_tokens': len(response.generations[0].text.split()),
                    'total_tokens': len(prompt.split()) + len(response.generations[0].text.split())
                },
                'model': self.model_name,
                'finish_reason': response.generations[0].finish_reason
            }
            
        except Exception as e:
            logger.error(f"Error generating Cohere response: {e}")
            return {
                'error': str(e),
                'content': f"Error generating response: {e}"
            }

class ConversationMemory:
    """Manages conversation memory for AI agents"""
    
    def __init__(self, conversation: Conversation, config: Dict[str, Any] = None):
        self.conversation = conversation
        self.config = config or {}
        self.mode = self.config.get('mode', 'session')
        self.max_tokens = self.config.get('max_tokens', 4000)
        self.summary_threshold = self.config.get('summary_threshold', 3000)
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        logger.info(f"Fetching conversation history for conversation {self.conversation.id} in mode '{self.mode}'")
        if self.mode == 'stateless':
            logger.info("Mode is 'stateless'; returning empty history.")
            return []
        messages = []
        recent_messages = list(self.conversation.messages.order_by('created_at'))
        logger.info(f"Fetched {len(recent_messages)} messages from DB for conversation {self.conversation.id}")
        if self.mode == 'session':
            session_start = timezone.now() - timedelta(hours=24)
            recent_messages = [msg for msg in recent_messages if msg.created_at >= session_start]
            logger.info(f"Filtered messages to last 24 hours: {len(recent_messages)} messages remain")
        for msg in recent_messages:
            messages.append({'role': msg.role, 'content': msg.content})
        if self.mode in ['persistent', 'contextual']:
            logger.info(f"Truncating messages for mode '{self.mode}' to fit token limit")
            messages = self._truncate_messages(messages)
        logger.info(f"Returning {len(messages)} messages for conversation history")
        return messages
    
    def _truncate_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Truncate messages to fit within token limit"""
        total_tokens = 0
        truncated_messages = []
        
        # Count tokens from the end
        for msg in reversed(messages):
            msg_tokens = len(msg['content'].split())  # Rough token count
            if total_tokens + msg_tokens > self.max_tokens:
                break
            total_tokens += msg_tokens
            truncated_messages.insert(0, msg)
        
        return truncated_messages
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add a message to conversation memory"""
        Message.objects.create(
            conversation=self.conversation,
            role=role,
            content=content,
            metadata=metadata or {}
        )
    
    def update_context(self, context_update: Dict[str, Any]):
        """Update conversation context"""
        if self.mode == 'contextual':
            current_context = self.conversation.context
            current_context.update(context_update)
            self.conversation.context = current_context
            self.conversation.save()


class KnowledgeRetriever:
    """Retrieves relevant knowledge for AI agents"""
    
    def __init__(self, user: User, embedding_manager: EmbeddingManager):
        self.user = user
        self.embedding_manager = embedding_manager
    
    def retrieve_context(self, query: str, agent: AIAgent) -> List[Dict[str, Any]]:
        """Retrieve relevant context for a query (synchronous version)"""
        try:
            max_documents = agent.max_documents
            similarity_threshold = agent.similarity_threshold

            # filter_metadata = {
            #     'user_id': str(self.user.id)
            # }

            data_source_ids = None
            file_type_names = None
            document_ids = None

            # Add data source filter if specified
            if agent.data_sources.exists():
                data_source_ids = list(agent.data_sources.values_list('id', flat=True))
                logger.info(f"Retrieving context for agent {agent.id} with data sources: {data_source_ids}")
                # filter_metadata['data_source_id'] = source_ids

            # Add file type filter if specified
            if agent.file_types.exists():
                file_type_names = list(agent.file_types.values_list('name', flat=True))
                # filter_metadata['file_type'] = file_type_names

            if(agent.documents.exists()):
                document_ids = list(agent.documents.values_list('id', flat=True))
                # filter_metadata['document_id'] = document_ids

            filter_metadata = build_user_or_doc_filter(str(self.user.id), data_source_ids, document_ids) 

            logger.info(f"Filter metadata for agent {agent.id}: {filter_metadata}")

            # Search for similar documents
            search_results = self.embedding_manager.search_similar_documents(
                query=query,
                k=max_documents,
                filter_metadata=filter_metadata,
            )

            # Filter by similarity threshold
            relevant_results = [
                result for result in search_results
                if result.get('distance', 0) <= (1 - similarity_threshold)
            ]

            # Format results
            context_docs = []
            for result in relevant_results:
                # Get document metadata
                doc_metadata = result.get('metadata', {})
                document_id = doc_metadata.get('document_id')

                if document_id:
                    try:
                        document = Document.objects.get(id=document_id, user=self.user)
                        context_docs.append({
                            'id': document_id,
                            'title': document.title,
                            'content': result.get('text', ''),
                            'metadata': doc_metadata,
                            'similarity': 1 - result.get('distance', 0)
                        })
                    except Document.DoesNotExist:
                        continue

            return context_docs

        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []

class AIAgentExecutor:
    """Executes AI agent requests"""
    
    def __init__(self):
        self.models = {}
        self.rate_limiters = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize AI models"""
        # Will be populated based on available API keys
        pass
    
    def get_model(self, provider: str, config: Dict[str, Any]) -> Optional[BaseAIModel]:
        """Get AI model instance"""
        model_key = f"{provider}_{config.get('model_name', 'default')}"
        
        if model_key not in self.models:
            try:
                if provider == 'openai' and OPENAI_AVAILABLE:
                    self.models[model_key] = OpenAIModel(config)
                elif provider == 'anthropic' and ANTHROPIC_AVAILABLE:
                    self.models[model_key] = AnthropicModel(config)
                elif provider == 'cohere' and COHERE_AVAILABLE:
                    self.models[model_key] = CohereModel(config)
                else:
                    logger.error(f"Model provider '{provider}' not available")
                    return None
            except Exception as e:
                logger.error(f"Error initializing model {provider}: {e}")
                return None
        
        return self.models.get(model_key)
    
    def get_rate_limiter(self, user_id: str, agent_id: str) -> RateLimiter:
        """Get rate limiter for user and agent"""
        key = f"{user_id}_{agent_id}"
        if key not in self.rate_limiters:
            self.rate_limiters[key] = RateLimiter()
        return self.rate_limiters[key]
    
    def execute_agent_request(self, agent: AIAgent, user_message: str,
                                   conversation: Conversation = None) -> Dict[str, Any]:
        """Execute an AI agent request"""
        try:
            start_time = time.time()
            
            # Check rate limits
            user_id = agent.user.id
            rate_limiter = self.get_rate_limiter(str(user_id), str(agent.id))

            if not rate_limiter.check_rate_limit(agent.rate_limit_per_hour, agent.rate_limit_per_day):
                return {
                    'error': 'Rate limit exceeded',
                    'content': 'You have exceeded the rate limit for this agent. Please try again later.'
                }
            
            # Get or create conversation
            if not conversation:
                conversation = Conversation.objects.create(
                    user=agent.user,
                    agent=agent,
                    title=user_message[:100] + "..." if len(user_message) > 100 else user_message
                )
            
            # Initialize conversation memory
            memory = ConversationMemory(conversation, {
                'mode': agent.conversation_mode,
                'max_tokens': agent.context_window
            })
            
            # Get conversation history
            conversation_history = memory.get_conversation_history()
            logger.info(f"Conversation history: {conversation_history}")
            
            logger.info(f"Executing agent request for user {agent.user.id}, agent {agent.id}, conversation {conversation.id}")
            # Initialize knowledge retriever
            
            context_docs = []

            # Retrieve relevant context
            if(agent.documents.exists() or agent.data_sources.exists()):
                embedding_manager = EmbeddingManager(str(agent.user.id))
                retriever = KnowledgeRetriever(agent.user, embedding_manager)
                context_docs = retriever.retrieve_context(user_message, agent)
            else:
                logger.info(f"No documents or data sources associated with agent {agent.id}. Skipping context retrieval.")

            # Format context
            context_text = ""
            if context_docs:
                context_parts = []
                for doc in context_docs:
                    context_parts.append(f"Document: {doc['title']}")
                    context_parts.append(f"Content: {doc['content']}")
                    context_parts.append("---")
                context_text = "\n".join(context_parts)
            
            # Prepare messages
            messages = []
            
            # Add system prompt
            if agent.system_prompt:
                messages.append({
                    'role': 'system',
                    'content': agent.system_prompt
                })
            
            # Add conversation history
            messages.extend(conversation_history)
            
            # Add current user message
            user_prompt = user_message
            if agent.user_prompt_template:
                user_prompt = agent.user_prompt_template.format(
                    user_message=user_message,
                    context=context_text
                )
            
            messages.append({
                'role': 'user',
                'content': user_prompt
            })
            
            # Get AI model - always use environment variables for API keys
            import os
            
            # Map provider names to environment variable names
            api_key_env_vars = {
                'openai': 'OPENAI_API_KEY',
                'anthropic': 'ANTHROPIC_API_KEY',
                'cohere': 'COHERE_API_KEY',
            }
            
            env_var_name = api_key_env_vars.get(agent.model_provider, 'OPENAI_API_KEY')
            api_key = os.getenv(env_var_name)
            
            model_config = {
                'model_name': agent.model_name,
                'api_key': api_key,
                **agent.model_parameters
            }
            
            # Log model being used for debugging
            logger.info(f"Using model: {agent.model_name} (provider: {agent.model_provider}) for agent {agent.id} ({agent.name})")
            logger.info(f"API key from environment variable: {env_var_name}")
            
            model = self.get_model(agent.model_provider, model_config)
            if not model:
                return {
                    'error': 'Model not available',
                    'content': 'The requested AI model is not available. Please check your configuration.'
                }
        
            # Generate response
            logger.info(f"Calling OpenAI API with model: {model.model_name}")
            response = model.generate_response(messages, context_text)
            logger.info(f"OpenAI API response received. Model used: {response.get('model', 'unknown')}, Tokens: {response.get('usage', {}).get('total_tokens', 0)}")
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Save messages to memory
            memory.add_message('user', user_message)
            memory.add_message('assistant', response.get('content', ''), {
                'context_docs': [doc['id'] for doc in context_docs],
                'model_info': {
                    'provider': agent.model_provider,
                    'model': agent.model_name,
                    'usage': response.get('usage', {})
                }
            })
            
            # Log usage
            usage_data = response.get('usage', {})
            AgentUsage.objects.create(
                user=agent.user,
                agent=agent,
                tokens_used=usage_data.get('total_tokens', 0),
                response_time=response_time,
                request_data={
                    'message_length': len(user_message),
                    'context_docs_count': len(context_docs),
                    'conversation_id': str(conversation.id)
                }
            )
            
            return {
                'content': response.get('content', ''),
                'conversation_id': str(conversation.id),
                'context_docs': context_docs,
                'response_time': response_time,
                'usage': usage_data
            }
            
        except Exception as e:
            logger.error(f"Error executing agent request: {e}")
            return {
                'error': str(e),
                'content': f"An error occurred while processing your request: {e}"
            }


class AgentTemplateManager:
    """Manages predefined agent templates"""
    
    @staticmethod
    def get_templates() -> Dict[str, Dict[str, Any]]:
        """Get predefined agent templates"""
        return {
            'generic_assistant': {
                'name': 'Generic Assistant',
                'description': 'A general-purpose AI assistant',
                'agent_type': 'generic',
                'system_prompt': '''You are a helpful AI assistant. Use the provided context to answer questions accurately and helpfully. If the context doesn't contain relevant information, let the user know and provide general guidance if possible.''',
                'conversation_mode': 'session',
                'max_documents': 5,
                'similarity_threshold': 0.7,
                'rate_limit_per_hour': 100,
                'rate_limit_per_day': 1000
            },
            'research_assistant': {
                'name': 'Research Assistant',
                'description': 'Specialized in research and analysis',
                'agent_type': 'research_assistant',
                'system_prompt': '''You are a research assistant specialized in analyzing documents and providing detailed insights. Focus on finding relevant information, identifying patterns, and providing comprehensive analysis based on the available context.''',
                'conversation_mode': 'contextual',
                'max_documents': 15,
                'similarity_threshold': 0.6,
                'rate_limit_per_hour': 50,
                'rate_limit_per_day': 500
            },
            'code_assistant': {
                'name': 'Code Assistant',
                'description': 'Specialized in code analysis and programming help',
                'agent_type': 'code_assistant',
                'system_prompt': '''You are a code assistant specialized in analyzing code, providing programming guidance, and helping with technical documentation. Focus on code quality, best practices, and practical solutions.''',
                'conversation_mode': 'session',
                'max_documents': 10,
                'similarity_threshold': 0.8,
                'rate_limit_per_hour': 75,
                'rate_limit_per_day': 750
            },
            'customer_support': {
                'name': 'Customer Support',
                'description': 'Specialized in customer service and support',
                'agent_type': 'customer_support',
                'system_prompt': '''You are a customer support assistant. Provide helpful, friendly, and professional responses to customer inquiries. Use the knowledge base to find relevant information and solutions.''',
                'conversation_mode': 'persistent',
                'max_documents': 8,
                'similarity_threshold': 0.75,
                'rate_limit_per_hour': 150,
                'rate_limit_per_day': 1500
            },
            'data_analyst': {
                'name': 'Data Analyst',
                'description': 'Specialized in data analysis and insights',
                'agent_type': 'data_analyst',
                'system_prompt': '''You are a data analyst specialized in interpreting data, identifying trends, and providing actionable insights. Focus on data-driven analysis and clear explanations of findings.''',
                'conversation_mode': 'contextual',
                'max_documents': 12,
                'similarity_threshold': 0.7,
                'rate_limit_per_hour': 60,
                'rate_limit_per_day': 600
            }
        }
    
    @staticmethod
    def create_agent_from_template(user: User, template_name: str, 
                                 custom_config: Dict[str, Any] = None) -> AIAgent:
        """Create an agent from a template"""
        templates = AgentTemplateManager.get_templates()
        
        if template_name not in templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = templates[template_name]
        
        # Merge custom configuration
        if custom_config:
            template.update(custom_config)
        
        # Create agent
        agent = AIAgent.objects.create(
            user=user,
            name=template['name'],
            description=template['description'],
            agent_type=template['agent_type'],
            system_prompt=template['system_prompt'],
            conversation_mode=template['conversation_mode'],
            max_documents=template['max_documents'],
            similarity_threshold=template['similarity_threshold'],
            rate_limit_per_hour=template['rate_limit_per_hour'],
            rate_limit_per_day=template['rate_limit_per_day']
        )
        
        return agent


# Global agent executor
agent_executor = AIAgentExecutor()