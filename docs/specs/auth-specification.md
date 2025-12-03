# Authentication Specification

> **Project**: PEA RE Forecast Platform
> **Version**: 1.0.0
> **Status**: Draft
> **Created**: 2025-12-03
> **TOR Reference**: Section 7.1.3 (Keycloak), Section 7.1.6 (Audit Trail)

---

## 1. Overview

### 1.1 Purpose

This specification defines the authentication and authorization implementation for the PEA RE Forecast Platform using Keycloak as the identity provider, per TOR requirements.

### 1.2 Scope

- OAuth2/OIDC authentication flow
- JWT token validation
- Role-based access control (RBAC)
- Audit logging
- Session management

### 1.3 TOR Requirements

| Requirement | Description | Implementation |
|-------------|-------------|----------------|
| 7.1.3 | Keycloak for security | OAuth2/OIDC with JWT |
| 7.1.6 | Access logs and audit trail | Structured logging to audit_log table |

---

## 2. Architecture

### 2.1 Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AUTHENTICATION FLOW                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐          │
│   │  User    │     │ Frontend │     │ Keycloak │     │ Backend  │          │
│   └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘          │
│        │                │                │                │                 │
│        │  1. Access     │                │                │                 │
│        │────────────────▶                │                │                 │
│        │                │                │                │                 │
│        │  2. Redirect   │                │                │                 │
│        │◀────────────────                │                │                 │
│        │                                 │                │                 │
│        │  3. Login page                  │                │                 │
│        │─────────────────────────────────▶                │                 │
│        │                                 │                │                 │
│        │  4. Credentials                 │                │                 │
│        │─────────────────────────────────▶                │                 │
│        │                                 │                │                 │
│        │  5. Auth code                   │                │                 │
│        │◀─────────────────────────────────                │                 │
│        │                │                │                │                 │
│        │                │  6. Exchange   │                │                 │
│        │                │────────────────▶                │                 │
│        │                │                │                │                 │
│        │                │  7. Tokens     │                │                 │
│        │                │◀────────────────                │                 │
│        │                │                │                │                 │
│        │                │  8. API call + JWT              │                 │
│        │                │─────────────────────────────────▶                 │
│        │                │                │                │                 │
│        │                │                │  9. Validate   │                 │
│        │                │                │◀───────────────│                 │
│        │                │                │                │                 │
│        │                │                │  10. Valid     │                 │
│        │                │                │────────────────▶                 │
│        │                │                │                │                 │
│        │                │  11. Response                   │                 │
│        │                │◀─────────────────────────────────                 │
│        │                │                │                │                 │
│        │  12. Display   │                │                │                 │
│        │◀────────────────                │                │                 │
│        │                │                │                │                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AUTHENTICATION COMPONENTS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         KEYCLOAK SERVER                              │    │
│  │                                                                      │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │    │
│  │  │    Realm    │  │   Client    │  │    Users    │                  │    │
│  │  │ pea-forecast│  │ pea-web-app │  │   & Roles   │                  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │    │
│  │                                                                      │    │
│  │  Port: 8080 (HTTP) / 8443 (HTTPS)                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────┐    ┌─────────────────────────────┐         │
│  │       FRONTEND (React)      │    │      BACKEND (FastAPI)      │         │
│  │                             │    │                             │         │
│  │  ┌─────────────────────┐   │    │  ┌─────────────────────┐   │         │
│  │  │   AuthProvider      │   │    │  │   JWT Middleware    │   │         │
│  │  │   - Login/Logout    │   │    │  │   - Token decode    │   │         │
│  │  │   - Token refresh   │   │    │  │   - Signature check │   │         │
│  │  │   - Session state   │   │    │  │   - Claims extract  │   │         │
│  │  └─────────────────────┘   │    │  └─────────────────────┘   │         │
│  │                             │    │                             │         │
│  │  ┌─────────────────────┐   │    │  ┌─────────────────────┐   │         │
│  │  │   useAuth Hook      │   │    │  │   RBAC Decorator    │   │         │
│  │  │   - User context    │   │    │  │   - Role checking   │   │         │
│  │  │   - Role checking   │   │    │  │   - Permission deny │   │         │
│  │  └─────────────────────┘   │    │  └─────────────────────┘   │         │
│  │                             │    │                             │         │
│  │  Port: 3000                 │    │  Port: 8000                 │         │
│  └─────────────────────────────┘    └─────────────────────────────┘         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Keycloak Configuration

### 3.1 Realm Configuration

```json
{
  "realm": "pea-forecast",
  "enabled": true,
  "displayName": "PEA RE Forecast Platform",
  "sslRequired": "external",
  "registrationAllowed": false,
  "loginWithEmailAllowed": true,
  "duplicateEmailsAllowed": false,
  "resetPasswordAllowed": true,
  "editUsernameAllowed": false,
  "bruteForceProtected": true,
  "permanentLockout": false,
  "maxFailureWaitSeconds": 900,
  "minimumQuickLoginWaitSeconds": 60,
  "waitIncrementSeconds": 60,
  "quickLoginCheckMilliSeconds": 1000,
  "maxDeltaTimeSeconds": 43200,
  "failureFactor": 5,
  "accessTokenLifespan": 900,
  "accessTokenLifespanForImplicitFlow": 900,
  "ssoSessionIdleTimeout": 1800,
  "ssoSessionMaxLifespan": 36000,
  "offlineSessionIdleTimeout": 2592000,
  "accessCodeLifespan": 60,
  "accessCodeLifespanUserAction": 300,
  "accessCodeLifespanLogin": 1800
}
```

### 3.2 Client Configuration

```json
{
  "clientId": "pea-forecast-web",
  "name": "PEA RE Forecast Web Application",
  "description": "Frontend SPA client",
  "rootUrl": "http://localhost:3000",
  "adminUrl": "http://localhost:3000",
  "baseUrl": "/",
  "surrogateAuthRequired": false,
  "enabled": true,
  "alwaysDisplayInConsole": true,
  "clientAuthenticatorType": "client-secret",
  "redirectUris": [
    "http://localhost:3000/*",
    "https://pea-forecast.go.th/*"
  ],
  "webOrigins": [
    "http://localhost:3000",
    "https://pea-forecast.go.th"
  ],
  "notBefore": 0,
  "bearerOnly": false,
  "consentRequired": false,
  "standardFlowEnabled": true,
  "implicitFlowEnabled": false,
  "directAccessGrantsEnabled": true,
  "serviceAccountsEnabled": false,
  "publicClient": true,
  "frontchannelLogout": true,
  "protocol": "openid-connect",
  "attributes": {
    "pkce.code.challenge.method": "S256",
    "post.logout.redirect.uris": "http://localhost:3000/*"
  },
  "fullScopeAllowed": true,
  "defaultClientScopes": [
    "web-origins",
    "profile",
    "roles",
    "email"
  ],
  "optionalClientScopes": [
    "address",
    "phone",
    "offline_access"
  ]
}
```

### 3.3 Backend Client (Service Account)

```json
{
  "clientId": "pea-forecast-api",
  "name": "PEA RE Forecast API Service",
  "description": "Backend service account for M2M communication",
  "enabled": true,
  "clientAuthenticatorType": "client-secret",
  "secret": "${PEA_KEYCLOAK_CLIENT_SECRET}",
  "bearerOnly": true,
  "consentRequired": false,
  "standardFlowEnabled": false,
  "implicitFlowEnabled": false,
  "directAccessGrantsEnabled": false,
  "serviceAccountsEnabled": true,
  "publicClient": false,
  "protocol": "openid-connect"
}
```

---

## 4. Role-Based Access Control

### 4.1 Role Definitions

| Role | Description | Permissions |
|------|-------------|-------------|
| `admin` | System administrator | Full access to all resources |
| `operator` | Grid operator | View dashboards, acknowledge alerts, view forecasts |
| `analyst` | Data analyst | View dashboards, export data, view history |
| `api` | Machine-to-machine | Prediction endpoints only |
| `viewer` | Read-only user | View dashboards only |

### 4.2 Permission Matrix

| Endpoint | admin | operator | analyst | api | viewer |
|----------|-------|----------|---------|-----|--------|
| `GET /forecast/solar` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `POST /forecast/solar` | ✅ | ✅ | ✅ | ✅ | ❌ |
| `GET /forecast/voltage` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `POST /forecast/voltage` | ✅ | ✅ | ✅ | ✅ | ❌ |
| `GET /data/*` | ✅ | ✅ | ✅ | ❌ | ✅ |
| `POST /data/ingest` | ✅ | ❌ | ❌ | ✅ | ❌ |
| `GET /alerts` | ✅ | ✅ | ✅ | ❌ | ✅ |
| `POST /alerts/acknowledge` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `POST /alerts/resolve` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `GET /history/*` | ✅ | ✅ | ✅ | ❌ | ✅ |
| `POST /history/export` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `GET /admin/*` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `POST /admin/*` | ✅ | ❌ | ❌ | ❌ | ❌ |

### 4.3 Role Realm Configuration

```json
{
  "roles": {
    "realm": [
      {
        "name": "admin",
        "description": "System administrator with full access",
        "composite": true,
        "composites": {
          "realm": ["operator", "analyst", "viewer"]
        }
      },
      {
        "name": "operator",
        "description": "Grid operator with alert management",
        "composite": true,
        "composites": {
          "realm": ["viewer"]
        }
      },
      {
        "name": "analyst",
        "description": "Data analyst with export capabilities",
        "composite": true,
        "composites": {
          "realm": ["viewer"]
        }
      },
      {
        "name": "api",
        "description": "Machine-to-machine service account",
        "composite": false
      },
      {
        "name": "viewer",
        "description": "Read-only access to dashboards",
        "composite": false
      }
    ]
  }
}
```

---

## 5. JWT Token Structure

### 5.1 Access Token Claims

```json
{
  "exp": 1702000000,
  "iat": 1701999100,
  "jti": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "iss": "https://auth.pea-forecast.go.th/realms/pea-forecast",
  "aud": "account",
  "sub": "user-uuid-here",
  "typ": "Bearer",
  "azp": "pea-forecast-web",
  "session_state": "session-uuid-here",
  "acr": "1",
  "allowed-origins": ["http://localhost:3000"],
  "realm_access": {
    "roles": ["operator", "viewer"]
  },
  "resource_access": {
    "account": {
      "roles": ["manage-account", "view-profile"]
    }
  },
  "scope": "openid profile email",
  "sid": "session-id-here",
  "email_verified": true,
  "name": "Somchai Operator",
  "preferred_username": "somchai.op",
  "given_name": "Somchai",
  "family_name": "Operator",
  "email": "somchai.op@pea.co.th"
}
```

### 5.2 Token Validation Rules

| Rule | Description | Action on Failure |
|------|-------------|-------------------|
| Expiration | `exp` > current time | 401 Unauthorized |
| Issuer | `iss` matches Keycloak URL | 401 Unauthorized |
| Audience | `azp` matches client ID | 401 Unauthorized |
| Signature | RS256 signature valid | 401 Unauthorized |
| Role | User has required role | 403 Forbidden |

---

## 6. Backend Implementation

### 6.1 Configuration

```python
# backend/app/core/config.py

class Settings(BaseSettings):
    # Keycloak Configuration
    KEYCLOAK_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "pea-forecast"
    KEYCLOAK_CLIENT_ID: str = "pea-forecast-web"
    KEYCLOAK_CLIENT_SECRET: Optional[str] = None

    # JWT Settings
    JWT_ALGORITHM: str = "RS256"
    JWT_AUDIENCE: str = "account"

    # JWKS Cache
    JWKS_CACHE_TTL: int = 3600  # 1 hour

    @property
    def keycloak_openid_config_url(self) -> str:
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}/.well-known/openid-configuration"

    @property
    def keycloak_jwks_url(self) -> str:
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}/protocol/openid-connect/certs"
```

### 6.2 JWT Validation Middleware

```python
# backend/app/core/security.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
from functools import lru_cache
from typing import Optional, List
from pydantic import BaseModel

security = HTTPBearer()

class TokenPayload(BaseModel):
    sub: str
    email: Optional[str] = None
    name: Optional[str] = None
    preferred_username: Optional[str] = None
    realm_access: Optional[dict] = None
    exp: int
    iat: int

class CurrentUser(BaseModel):
    id: str
    email: Optional[str]
    name: Optional[str]
    username: Optional[str]
    roles: List[str]

@lru_cache(maxsize=1)
def get_jwks_client():
    """Get cached JWKS client."""
    from app.core.config import get_settings
    settings = get_settings()
    return httpx.get(settings.keycloak_jwks_url).json()

def decode_token(token: str) -> TokenPayload:
    """Decode and validate JWT token."""
    from app.core.config import get_settings
    settings = get_settings()

    try:
        jwks = get_jwks_client()
        unverified_header = jwt.get_unverified_header(token)

        # Find the key
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break

        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key"
            )

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}"
        )

        return TokenPayload(**payload)

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}"
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """Extract current user from JWT token."""
    token = credentials.credentials
    payload = decode_token(token)

    roles = []
    if payload.realm_access:
        roles = payload.realm_access.get("roles", [])

    return CurrentUser(
        id=payload.sub,
        email=payload.email,
        name=payload.name,
        username=payload.preferred_username,
        roles=roles
    )

def require_roles(required_roles: List[str]):
    """Dependency factory for role-based access control."""
    async def role_checker(
        current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        for role in required_roles:
            if role in current_user.roles:
                return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required roles: {required_roles}"
        )

    return role_checker
```

### 6.3 Audit Logging Middleware

```python
# backend/app/core/middleware.py

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import json
from datetime import datetime
from app.db.session import async_session
from app.core.security import decode_token, TokenPayload
from sqlalchemy import text

class AuditLogMiddleware(BaseHTTPMiddleware):
    """Log all API access to audit_log table per TOR 7.1.6."""

    SKIP_PATHS = ["/health", "/ready", "/docs", "/openapi.json", "/redoc"]

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip health checks and docs
        if any(request.url.path.startswith(p) for p in self.SKIP_PATHS):
            return await call_next(request)

        # Extract user info from token if present
        user_id = None
        user_email = None

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = decode_token(token)
                user_id = payload.sub
                user_email = payload.email
            except Exception:
                pass  # Continue without user info

        # Get request body for non-GET requests
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    request_body = json.loads(body)
                    # Mask sensitive fields
                    for field in ["password", "secret", "token"]:
                        if field in request_body:
                            request_body[field] = "***MASKED***"
            except Exception:
                pass

        # Call the actual endpoint
        response = await call_next(request)

        # Log to audit_log table
        try:
            async with async_session() as session:
                await session.execute(
                    text("""
                        INSERT INTO audit_log (
                            time, user_id, user_email, user_ip,
                            action, resource_type, resource_id,
                            request_method, request_path, request_body,
                            response_status, user_agent, session_id
                        ) VALUES (
                            :time, :user_id, :user_email, :user_ip,
                            :action, :resource_type, :resource_id,
                            :request_method, :request_path, :request_body,
                            :response_status, :user_agent, :session_id
                        )
                    """),
                    {
                        "time": datetime.utcnow(),
                        "user_id": user_id,
                        "user_email": user_email,
                        "user_ip": request.client.host if request.client else None,
                        "action": self._get_action(request.method),
                        "resource_type": self._get_resource_type(request.url.path),
                        "resource_id": self._get_resource_id(request.url.path),
                        "request_method": request.method,
                        "request_path": str(request.url.path),
                        "request_body": json.dumps(request_body) if request_body else None,
                        "response_status": response.status_code,
                        "user_agent": request.headers.get("User-Agent"),
                        "session_id": request.headers.get("X-Session-ID")
                    }
                )
                await session.commit()
        except Exception as e:
            # Don't fail the request if logging fails
            import logging
            logging.error(f"Audit log failed: {e}")

        return response

    def _get_action(self, method: str) -> str:
        return {
            "GET": "read",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete"
        }.get(method, "unknown")

    def _get_resource_type(self, path: str) -> str:
        parts = path.strip("/").split("/")
        if len(parts) >= 3:  # api/v1/resource
            return parts[2]
        return "unknown"

    def _get_resource_id(self, path: str) -> Optional[str]:
        parts = path.strip("/").split("/")
        if len(parts) >= 4:
            return parts[3]
        return None
```

### 6.4 Protected Endpoint Example

```python
# backend/app/api/v1/endpoints/forecast.py

from fastapi import APIRouter, Depends
from app.core.security import get_current_user, require_roles, CurrentUser

router = APIRouter()

@router.post("/solar")
async def predict_solar(
    request: SolarPredictionRequest,
    current_user: CurrentUser = Depends(require_roles(["operator", "analyst", "api", "admin"]))
):
    """Generate solar power prediction. Requires operator, analyst, api, or admin role."""
    # Log who made the request
    logger.info(f"Solar prediction requested by {current_user.username}")
    # ... prediction logic
```

---

## 7. Frontend Implementation

### 7.1 Auth Provider

```typescript
// frontend/src/lib/auth.ts

import Keycloak from 'keycloak-js';

const keycloakConfig = {
  url: process.env.NEXT_PUBLIC_KEYCLOAK_URL || 'http://localhost:8080',
  realm: process.env.NEXT_PUBLIC_KEYCLOAK_REALM || 'pea-forecast',
  clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID || 'pea-forecast-web',
};

let keycloakInstance: Keycloak | null = null;

export function getKeycloak(): Keycloak {
  if (!keycloakInstance) {
    keycloakInstance = new Keycloak(keycloakConfig);
  }
  return keycloakInstance;
}

export async function initKeycloak(): Promise<boolean> {
  const keycloak = getKeycloak();

  try {
    const authenticated = await keycloak.init({
      onLoad: 'check-sso',
      silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
      pkceMethod: 'S256',
    });

    if (authenticated) {
      // Setup token refresh
      setInterval(async () => {
        try {
          await keycloak.updateToken(60); // Refresh if expires in 60s
        } catch (error) {
          console.error('Token refresh failed:', error);
          keycloak.login();
        }
      }, 30000); // Check every 30s
    }

    return authenticated;
  } catch (error) {
    console.error('Keycloak init failed:', error);
    return false;
  }
}

export function login(): void {
  getKeycloak().login();
}

export function logout(): void {
  getKeycloak().logout();
}

export function getToken(): string | undefined {
  return getKeycloak().token;
}

export function hasRole(role: string): boolean {
  return getKeycloak().hasRealmRole(role);
}

export function getUserInfo(): { name?: string; email?: string; username?: string } | null {
  const keycloak = getKeycloak();
  if (!keycloak.authenticated) return null;

  return {
    name: keycloak.tokenParsed?.name,
    email: keycloak.tokenParsed?.email,
    username: keycloak.tokenParsed?.preferred_username,
  };
}
```

### 7.2 Auth Context Hook

```typescript
// frontend/src/hooks/useAuth.ts

import { createContext, useContext, useEffect, useState } from 'react';
import { initKeycloak, login, logout, hasRole, getUserInfo, getToken } from '@/lib/auth';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: { name?: string; email?: string; username?: string } | null;
  hasRole: (role: string) => boolean;
  login: () => void;
  logout: () => void;
  getToken: () => string | undefined;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<AuthContextType['user']>(null);

  useEffect(() => {
    initKeycloak()
      .then((authenticated) => {
        setIsAuthenticated(authenticated);
        if (authenticated) {
          setUser(getUserInfo());
        }
      })
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <AuthContext.Provider value={{
      isAuthenticated,
      isLoading,
      user,
      hasRole,
      login,
      logout,
      getToken,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
```

### 7.3 Protected Route Component

```typescript
// frontend/src/components/auth/ProtectedRoute.tsx

import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
}

export function ProtectedRoute({ children, requiredRoles = [] }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, hasRole, login } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      login();
    }
  }, [isLoading, isAuthenticated, login]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-700" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect to login
  }

  if (requiredRoles.length > 0 && !requiredRoles.some(hasRole)) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600">Access Denied</h1>
          <p className="text-gray-600 mt-2">
            You don't have permission to access this page.
          </p>
          <p className="text-gray-500 text-sm mt-1">
            Required roles: {requiredRoles.join(', ')}
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
```

### 7.4 API Client with Auth

```typescript
// frontend/src/lib/api.ts

import { getToken } from './auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      // Token expired, trigger re-login
      window.location.href = '/';
    }
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}
```

---

## 8. Docker Compose Configuration

### 8.1 Keycloak Service

```yaml
# docker/docker-compose.yml (addition)

services:
  keycloak:
    image: quay.io/keycloak/keycloak:23.0
    container_name: pea-keycloak
    environment:
      - KEYCLOAK_ADMIN=admin
      - KEYCLOAK_ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD:-admin123}
      - KC_DB=postgres
      - KC_DB_URL=jdbc:postgresql://timescaledb:5432/keycloak
      - KC_DB_USERNAME=postgres
      - KC_DB_PASSWORD=${POSTGRES_PASSWORD:-postgres}
      - KC_HOSTNAME_STRICT=false
      - KC_HTTP_ENABLED=true
      - KC_PROXY=edge
    command:
      - start-dev
      - --import-realm
    volumes:
      - ./keycloak/realm-export.json:/opt/keycloak/data/import/realm-export.json:ro
    ports:
      - "8080:8080"
    depends_on:
      - timescaledb
    networks:
      - pea-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8080/health/ready || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
```

### 8.2 Realm Import File

```json
// docker/keycloak/realm-export.json

{
  "realm": "pea-forecast",
  "enabled": true,
  "displayName": "PEA RE Forecast Platform",
  "users": [
    {
      "username": "admin",
      "email": "admin@pea.co.th",
      "enabled": true,
      "credentials": [
        {
          "type": "password",
          "value": "admin123",
          "temporary": true
        }
      ],
      "realmRoles": ["admin"]
    },
    {
      "username": "operator",
      "email": "operator@pea.co.th",
      "enabled": true,
      "credentials": [
        {
          "type": "password",
          "value": "operator123",
          "temporary": true
        }
      ],
      "realmRoles": ["operator"]
    },
    {
      "username": "analyst",
      "email": "analyst@pea.co.th",
      "enabled": true,
      "credentials": [
        {
          "type": "password",
          "value": "analyst123",
          "temporary": true
        }
      ],
      "realmRoles": ["analyst"]
    }
  ],
  "clients": [
    {
      "clientId": "pea-forecast-web",
      "publicClient": true,
      "standardFlowEnabled": true,
      "directAccessGrantsEnabled": true,
      "redirectUris": ["http://localhost:3000/*"],
      "webOrigins": ["http://localhost:3000"],
      "attributes": {
        "pkce.code.challenge.method": "S256"
      }
    }
  ],
  "roles": {
    "realm": [
      {"name": "admin", "composite": true, "composites": {"realm": ["operator", "analyst"]}},
      {"name": "operator", "composite": true, "composites": {"realm": ["viewer"]}},
      {"name": "analyst", "composite": true, "composites": {"realm": ["viewer"]}},
      {"name": "api"},
      {"name": "viewer"}
    ]
  }
}
```

---

## 9. Testing Requirements

### 9.1 Authentication Tests

```python
# backend/tests/unit/test_auth.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_protected_endpoint_without_token():
    """Verify endpoints reject requests without token."""
    client = TestClient(app)
    response = client.post("/api/v1/forecast/solar", json={})
    assert response.status_code == 403  # No credentials

def test_protected_endpoint_with_invalid_token():
    """Verify endpoints reject invalid tokens."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/forecast/solar",
        json={},
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401

def test_protected_endpoint_with_insufficient_role():
    """Verify endpoints reject users with insufficient roles."""
    # Create a valid token with only 'viewer' role
    # Attempt to access endpoint requiring 'operator' role
    # Assert 403 Forbidden
    pass

def test_audit_log_created():
    """Verify audit log entry created for each request."""
    # Make authenticated request
    # Query audit_log table
    # Assert entry exists with correct data
    pass
```

### 9.2 Integration Tests

```python
# backend/tests/integration/test_keycloak.py

import pytest
import httpx

KEYCLOAK_URL = "http://localhost:8080"
REALM = "pea-forecast"

@pytest.mark.integration
async def test_keycloak_realm_exists():
    """Verify Keycloak realm is configured."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{KEYCLOAK_URL}/realms/{REALM}/.well-known/openid-configuration"
        )
        assert response.status_code == 200
        config = response.json()
        assert config["issuer"] == f"{KEYCLOAK_URL}/realms/{REALM}"

@pytest.mark.integration
async def test_keycloak_login_flow():
    """Test complete login flow."""
    async with httpx.AsyncClient() as client:
        # Get token with password grant
        response = await client.post(
            f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "pea-forecast-web",
                "username": "admin",
                "password": "admin123"
            }
        )
        assert response.status_code == 200
        tokens = response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
```

---

## 10. Security Considerations

### 10.1 Token Security

- Use PKCE (Proof Key for Code Exchange) for SPA
- Store tokens in memory, not localStorage
- Implement automatic token refresh
- Clear tokens on logout

### 10.2 API Security

- Validate all JWTs on every request
- Check token expiration
- Verify token signature
- Implement rate limiting per user

### 10.3 Audit Compliance

- Log all authenticated requests
- Include user identity in logs
- Mask sensitive data (passwords, tokens)
- Retain logs per TOR 7.1.6

---

## 11. Migration Plan

### 11.1 Phase 1: Development

1. Add Keycloak to Docker Compose
2. Create realm configuration
3. Implement backend JWT validation
4. Add audit logging middleware

### 11.2 Phase 2: Frontend Integration

1. Install keycloak-js package
2. Implement AuthProvider
3. Add ProtectedRoute component
4. Update API client with auth headers

### 11.3 Phase 3: Testing

1. Write unit tests for auth components
2. Write integration tests with Keycloak
3. Test role-based access control
4. Verify audit log compliance

---

*Specification Version: 1.0.0*
*Last Updated: 2025-12-03*
