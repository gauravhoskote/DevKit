import logging
import jwt
from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from src.utils.model.scopeDetails import ScopeDetails

class Authorize:
    def __getTokenAuthHeader__(self, request: Request):
        logging.debug("__getTokenAuthHeader__: Extracting token from header")
        auth = request.headers.get("Authorization")
        if not auth:
            raise HTTPException(status_code=401, detail="Authorization header is expected")

        parts = auth.split()
        if len(auth) == 36:  # UUID format check
            return auth
        elif parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Authorization header must start with Bearer")
        elif len(parts) == 1:
            raise HTTPException(status_code=401, detail="Invalid header, token not found")
        elif len(parts) > 2:
            raise HTTPException(status_code=401, detail='Authorization header must be in the form "Bearer token"')
        
        return parts[1]

    def __getTokenScopes__(self, bearerToken: str):
        logging.debug("__getTokenScopes__: Decoding token")
        decoded = jwt.decode(bearerToken, options={"verify_signature": False})
        logging.debug(f"Decoded token: {decoded}")
        return decoded.get("scope", "")

    def __parseScope__(self, scopePath: str):
        logging.debug("__parseScope__: Parsing scope")
        if scopePath:
            scopePathFormatted = "/" + scopePath.replace(":", "/")
            lastIndexOfDot = scopePathFormatted.rfind(".")
            if lastIndexOfDot != -1:
                method = scopePathFormatted[lastIndexOfDot + 1 :]
                prefixPath = scopePathFormatted[:lastIndexOfDot]
                return ScopeDetails(scopePath, prefixPath, method)
        return None

    def validateAuthorization(self, request: Request):
        return True

    def validateAzureAuthorization(self, request: Request, tenant_id: str, client_id: str):
        return True
