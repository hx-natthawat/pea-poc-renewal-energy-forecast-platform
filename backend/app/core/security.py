"""
Authentication and authorization module using Keycloak.

This module provides JWT validation and role-based access control
per TOR requirements (Section 7.1.3 - Keycloak, Section 7.1.6 - Audit Trail).
"""

import logging
from datetime import UTC, datetime

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: str  # Subject (user ID)
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp
    email: str | None = None
    name: str | None = None
    preferred_username: str | None = None
    realm_access: dict | None = None
    azp: str | None = None  # Authorized party (client ID)


class CurrentUser(BaseModel):
    """Current authenticated user information."""

    id: str
    email: str | None = None
    name: str | None = None
    username: str | None = None
    roles: list[str] = []

    @property
    def user_id(self) -> str:
        """Alias for id for backwards compatibility."""
        return self.id


class JWKSClient:
    """Client for fetching and caching JWKS from Keycloak."""

    def __init__(self):
        self._jwks: dict | None = None
        self._last_fetch: datetime | None = None

    async def get_jwks(self) -> dict:
        """Fetch JWKS from Keycloak, with caching."""
        now = datetime.now(UTC)

        # Check if cache is valid
        if self._jwks and self._last_fetch:
            age = (now - self._last_fetch).total_seconds()
            if age < settings.JWKS_CACHE_TTL:
                return self._jwks

        # Fetch new JWKS
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    settings.KEYCLOAK_JWKS_URL,
                    timeout=10.0,
                )
                response.raise_for_status()
                self._jwks = response.json()
                self._last_fetch = now
                logger.info("JWKS fetched successfully from Keycloak")
                return self._jwks
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            # Return cached JWKS if available
            if self._jwks:
                logger.warning("Using cached JWKS due to fetch failure")
                return self._jwks
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable",
            )

    def get_key(self, kid: str) -> dict | None:
        """Get a specific key from JWKS by key ID."""
        if not self._jwks:
            return None

        for key in self._jwks.get("keys", []):
            if key.get("kid") == kid:
                return {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key.get("use", "sig"),
                    "n": key["n"],
                    "e": key["e"],
                }
        return None


# Global JWKS client instance
jwks_client = JWKSClient()


async def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token."""
    try:
        # Get the unverified header to find the key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing key ID",
            )

        # Fetch JWKS and get the signing key
        await jwks_client.get_jwks()
        rsa_key = jwks_client.get_key(kid)

        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate signing key",
            )

        # Decode and validate the token
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=[settings.JWT_ALGORITHM],
            audience="account",  # Keycloak default audience
            issuer=settings.KEYCLOAK_ISSUER,
            options={
                "verify_aud": True,
                "verify_iss": True,
                "verify_exp": True,
            },
        )

        return TokenPayload(**payload)

    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",  # Generic message for security
        )


async def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> CurrentUser | None:
    """
    Get current user if authenticated, None otherwise.

    Use this for endpoints that work with or without authentication.
    """
    if not credentials:
        return None

    try:
        payload = await decode_token(credentials.credentials)

        roles = []
        if payload.realm_access:
            roles = payload.realm_access.get("roles", [])

        return CurrentUser(
            id=payload.sub,
            email=payload.email,
            name=payload.name,
            username=payload.preferred_username,
            roles=roles,
        )
    except HTTPException:
        return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> CurrentUser:
    """
    Get current authenticated user.

    Raises 401 if not authenticated and AUTH_ENABLED is True.
    Returns a mock user if AUTH_ENABLED is False.
    """
    # If auth is disabled, return a mock admin user
    if not settings.AUTH_ENABLED:
        return CurrentUser(
            id="dev-user",
            email="dev@pea.co.th",
            name="Development User",
            username="dev",
            roles=["admin", "operator", "analyst", "viewer"],
        )

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = await decode_token(credentials.credentials)

    roles = []
    if payload.realm_access:
        roles = payload.realm_access.get("roles", [])

    return CurrentUser(
        id=payload.sub,
        email=payload.email,
        name=payload.name,
        username=payload.preferred_username,
        roles=roles,
    )


def require_roles(required_roles: list[str]):
    """
    Dependency factory for role-based access control.

    Usage:
        @router.get("/admin")
        async def admin_only(user: CurrentUser = Depends(require_roles(["admin"]))):
            ...
    """

    async def role_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        # If auth is disabled, allow all
        if not settings.AUTH_ENABLED:
            return current_user

        # Check if user has any of the required roles
        user_roles = set(current_user.roles)
        required = set(required_roles)

        if not user_roles.intersection(required):
            logger.warning(
                f"User {current_user.username} denied access. "
                f"Has roles: {current_user.roles}, required: {required_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {required_roles}",
            )

        return current_user

    return role_checker


# Convenience dependencies for common role requirements
require_admin = require_roles(["admin"])
require_operator = require_roles(["admin", "operator"])
require_analyst = require_roles(["admin", "analyst"])
require_viewer = require_roles(["admin", "operator", "analyst", "viewer"])
require_api = require_roles(["admin", "api"])
