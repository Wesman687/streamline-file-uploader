import base64
import hashlib
import hmac
import os
import time
from typing import Optional
from urllib.parse import quote


class URLSigner:
    def __init__(self):
        # Use default signing key if not provided - this allows basic functionality
        self.signing_key = os.getenv("UPLOAD_SIGNING_KEY", "default-signing-key-change-in-production")
        if self.signing_key == "default-signing-key-change-in-production":
            # Log warning about using default key
            import logging
            logger = logging.getLogger('server')
            logger.warning("Using default UPLOAD_SIGNING_KEY - set UPLOAD_SIGNING_KEY environment variable for production")
        
        self.signing_key_bytes = self.signing_key.encode('utf-8')
        self.default_ttl = int(os.getenv("SIGNED_URL_TTL_DEFAULT", "3600"))

    def sign_url(self, key: str, ttl: Optional[int] = None) -> str:
        """Generate a signed URL for file access."""
        if ttl is None:
            ttl = self.default_ttl
        
        # Calculate expiration timestamp
        exp = int(time.time()) + ttl
        
        # Encode the key for URL safety
        encoded_key = base64.urlsafe_b64encode(key.encode('utf-8')).decode('ascii')
        
        # Create HMAC signature: HMAC_SHA256(key | exp, signing_key)
        message = f"{key}|{exp}"
        signature = hmac.new(
            self.signing_key_bytes,
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Construct the signed URL
        base_url = os.getenv("PUBLIC_BASE_URL", "https://file-server.stream-lineai.com")
        return f"{base_url}/get/{encoded_key}?exp={exp}&sig={signature}"

    def verify_signature(self, key: str, exp: int, signature: str) -> bool:
        """Verify the HMAC signature and expiration."""
        # Check if the URL has expired
        if int(time.time()) > exp:
            return False
        
        # Recreate the expected signature
        message = f"{key}|{exp}"
        expected_signature = hmac.new(
            self.signing_key_bytes,
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected_signature)

    def decode_key_from_url(self, encoded_key: str) -> str:
        """Decode the base64-encoded key from URL."""
        try:
            return base64.urlsafe_b64decode(encoded_key.encode('ascii')).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Invalid encoded key: {e}")


# Global instance
url_signer = URLSigner()
