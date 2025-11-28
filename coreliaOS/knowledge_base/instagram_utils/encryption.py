# knowledge_base/utils/encryption.py

import base64
import logging
from cryptography.fernet import Fernet
from django.conf import settings

logger = logging.getLogger(__name__)


class TokenEncryption:
    """Utility class for encrypting and decrypting sensitive tokens"""
    
    def __init__(self):
        # Use Django's SECRET_KEY as the base for encryption
        # Pad or truncate to 32 bytes for Fernet
        secret_key = settings.SECRET_KEY.encode()
        if len(secret_key) < 32:
            secret_key = secret_key.ljust(32, b'0')
        else:
            secret_key = secret_key[:32]
        
        # Create Fernet cipher
        self.cipher = Fernet(base64.urlsafe_b64encode(secret_key))
    
    def encrypt_token(self, token):
        """Encrypt a token string"""
        try:
            if not token:
                return None
            return self.cipher.encrypt(token.encode()).decode()
        except Exception as e:
            logger.error(f"Error encrypting token: {str(e)}")
            raise
    
    def decrypt_token(self, encrypted_token):
        """Decrypt an encrypted token string"""
        try:
            if not encrypted_token:
                return None
            return self.cipher.decrypt(encrypted_token.encode()).decode()
        except Exception as e:
            logger.error(f"Error decrypting token: {str(e)}")
            raise
    
    def encrypt_dict(self, data_dict):
        """Encrypt all string values in a dictionary"""
        if not isinstance(data_dict, dict):
            return data_dict
        
        encrypted_dict = {}
        for key, value in data_dict.items():
            if isinstance(value, str) and value:
                try:
                    encrypted_dict[key] = self.encrypt_token(value)
                except Exception as e:
                    logger.error(f"Error encrypting dict value for key {key}: {str(e)}")
                    encrypted_dict[key] = value
            else:
                encrypted_dict[key] = value
        
        return encrypted_dict
    
    def decrypt_dict(self, encrypted_dict):
        """Decrypt all string values in a dictionary"""
        if not isinstance(encrypted_dict, dict):
            return encrypted_dict
        
        decrypted_dict = {}
        for key, value in encrypted_dict.items():
            if isinstance(value, str) and value:
                try:
                    decrypted_dict[key] = self.decrypt_token(value)
                except Exception as e:
                    logger.error(f"Error decrypting dict value for key {key}: {str(e)}")
                    decrypted_dict[key] = value
            else:
                decrypted_dict[key] = value
        
        return decrypted_dict


# Global instance
token_encryption = TokenEncryption()
