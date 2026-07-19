"""JWT token manager service handling cryptographically signed token creation and decoding validation."""

import time
import jwt
from typing import Dict, Any, Optional
from backend.models.user_role import UserRole
from backend.models.security_context import UserPrincipal, TokenData

SECRET_KEY = "DELL_HACKATHON_SECRET_SECURE_KEY_179"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 3600


class JWTManager:
    """Manages creation, signature, and decoding validation of JSON Web Tokens."""

    @classmethod
    def create_tokens(cls, user_id: str, username: str, role: UserRole) -> TokenData:
        """Generates access and refresh tokens for user principals.

        Args:
            user_id: Unique user identifier.
            username: User credential username.
            role: User role enum.

        Returns:
            TokenData model.
        """
        now = int(time.time())
        expires = now + ACCESS_TOKEN_EXPIRE_SECONDS

        payload = {
            "sub": user_id,
            "username": username,
            "role": role.value,
            "iat": now,
            "exp": expires
        }

        access_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        refresh_token = f"refresh-{uuid_like_hash(user_id)}"

        return TokenData(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in_seconds=ACCESS_TOKEN_EXPIRE_SECONDS
        )

    @classmethod
    def decode_token(cls, token: str) -> Optional[UserPrincipal]:
        """Decodes and validates a JWT access token signature.

        Args:
            token: Encrypted JWT string.

        Returns:
            Optional[UserPrincipal]: User principal if valid, else None.
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            user_id = payload.get("sub")
            username = payload.get("username")
            role_val = payload.get("role")

            if not user_id or not username or not role_val:
                return None

            try:
                role = UserRole(role_val)
            except ValueError:
                return None

            # Resolve permission scopes
            from backend.models.user_role import ROLE_PERMISSIONS
            permissions = ROLE_PERMISSIONS.get(role, [])

            return UserPrincipal(
                user_id=user_id,
                username=username,
                role=role,
                permissions=permissions
            )
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None


def uuid_like_hash(val: str) -> str:
    import hashlib
    return hashlib.sha256(val.encode("utf-8")).hexdigest()[:16]
