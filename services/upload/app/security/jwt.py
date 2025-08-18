import base64
import os
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


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
            print(f"Warning: Failed to load JWT public key: {e}")
            self.public_key = None
        
        self.service_token = os.getenv("AUTH_SERVICE_TOKEN")
        if not self.service_token:
            raise ValueError("AUTH_SERVICE_TOKEN environment variable is required")

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
            raise ValueError("Neither JWT_PUBLIC_KEY_PATH file nor AUTH_JWT_PUBLIC_KEY_BASE64 environment variable is available")
        
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid JWT token: {e}"
            )

    def verify_service_token(self, token: str) -> bool:
        """Verify service-to-service token."""
        return token == self.service_token


# Global instance
jwt_validator = JWTValidator()

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Dict[str, Any]:
    """Extract and validate user from JWT token (Bearer or Cookie)."""
    token = None
    
    # Try Bearer token first
    if credentials:
        token = credentials.credentials
    
    # Try cookie if no Bearer token
    if not token:
        token = request.cookies.get("auth_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    payload = jwt_validator.verify_jwt(token)
    
    if "user_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user_id"
        )
    
    return payload


async def get_service_auth(request: Request) -> bool:
    """Validate service-to-service authentication."""
    service_token = request.headers.get("X-Service-Token")
    
    if not service_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Service token required"
        )
    
    if not jwt_validator.verify_service_token(service_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service token"
        )
    
    return True


async def get_auth_user_or_service(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[Dict[str, Any]]:
    """Get user from JWT or validate service token. Returns user payload or None for service."""
    # Try service token first
    service_token = request.headers.get("X-Service-Token")
    if service_token:
        if jwt_validator.verify_service_token(service_token):
            return None  # Service authentication, no user
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid service token"
            )
    
    # Fall back to user authentication
    return await get_current_user(request, credentials)
