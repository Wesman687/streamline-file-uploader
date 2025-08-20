import base64
import os
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from app.logging_config import server_logger, error_logger


class JWTValidator:
    def __init__(self):
        # Load configuration
        self.algorithm = os.getenv("AUTH_JWT_ALG", "RS256")
        self.issuer = os.getenv("AUTH_JWT_ISSUER")
        self.audience = os.getenv("AUTH_JWT_AUDIENCE")
        self.kid = os.getenv("JWKS_KID")
        
        try:
            self.public_key = self._load_public_key()
        except Exception as e:
            server_logger.warning(f"Failed to load JWT public key: {e}")
            self.public_key = None
        
        # Service token for API authentication - use default production token if not set
        self.service_token = os.getenv("AUTH_SERVICE_TOKEN", "ee6d52ece4fa6c4c8836820d2eb7feeb6c78cbf2e2661ef76c9f5a805fc16340")
        
        # Log which token is being used (masked for security)
        if os.getenv("AUTH_SERVICE_TOKEN"):
            server_logger.info("Using custom AUTH_SERVICE_TOKEN from environment")
        else:
            server_logger.info("Using default production AUTH_SERVICE_TOKEN")

    def _load_public_key(self) -> rsa.RSAPublicKey:
        """Load public key from file path or base64."""
        from pathlib import Path
        
        # Try file path first
        public_key_path = os.getenv("JWT_PUBLIC_KEY_PATH")
        if public_key_path and Path(public_key_path).exists():
            with open(public_key_path, 'rb') as f:
                return serialization.load_pem_public_key(f.read())
        
        # Fall back to base64 environment variable
        public_key_b64 = os.getenv("AUTH_JWT_PUBLIC_KEY_BASE64")
        if not public_key_b64:
            # If no JWT key is provided, JWT validation will be disabled
            # This allows the server to work with just service token authentication
            server_logger.warning("No JWT public key configured - JWT validation disabled, only service token auth available")
            return None
        
        try:
            public_key_pem = base64.b64decode(public_key_b64)
            return serialization.load_pem_public_key(public_key_pem)
        except Exception as e:
            raise ValueError(f"Failed to decode base64 public key: {e}")

    def verify_jwt(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token with proper issuer/audience validation."""
        if not self.public_key:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="JWT validation not configured"
            )
        
        try:
            # Convert the public key to PEM format for jose
            public_key_pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Prepare decode options
            decode_options = {
                "algorithms": [self.algorithm],
            }
            
            # Add issuer validation if configured
            if self.issuer:
                decode_options["issuer"] = self.issuer
            
            # Add audience validation if configured  
            if self.audience:
                decode_options["audience"] = self.audience
            
            payload = jwt.decode(
                token,
                public_key_pem,
                **decode_options
            )
            return payload
        except JWTError as e:
            error_logger.warning(f"JWT validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    def verify_service_token(self, token: str) -> bool:
        """Verify service authentication token."""
        is_valid = token == self.service_token
        
        if is_valid:
            server_logger.info("Service token authentication successful")
        else:
            server_logger.warning("Service token authentication failed")
        
        return is_valid


# Global validator instance
jwt_validator = JWTValidator()

# HTTP Bearer security scheme
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Dict[str, Any]:
    """Extract and validate JWT from Authorization header or cookies."""
    token = None
    
    # Try Authorization header first
    if credentials:
        token = credentials.credentials
    else:
        # Try cookie fallback
        token = request.cookies.get("auth_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        payload = jwt_validator.verify_jwt(token)
        server_logger.info(f"JWT authentication successful for user: {payload.get('user_id', 'unknown')}")
        return payload
    except HTTPException:
        error_logger.warning("JWT authentication failed")
        raise


async def get_auth_user_or_service(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[Dict[str, Any]]:
    """
    Authentication for endpoints that support both user JWT and service tokens.
    Returns user payload for JWT auth, None for service auth.
    """
    # Check for service token in headers
    service_token = request.headers.get("x-service-token")
    if service_token:
        if jwt_validator.verify_service_token(service_token):
            server_logger.info("Service authentication successful")
            return None  # Indicates service authentication
        else:
            error_logger.warning("Service authentication failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid service token"
            )
    
    # Try JWT authentication
    token = None
    if credentials:
        token = credentials.credentials
    else:
        token = request.cookies.get("auth_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    try:
        payload = jwt_validator.verify_jwt(token)
        server_logger.info(f"JWT authentication successful for user: {payload.get('user_id', 'unknown')}")
        return payload
    except HTTPException:
        error_logger.warning("JWT authentication failed")
        raise
