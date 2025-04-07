
import logging

import jwt
from flask import abort, jsonify, make_response, request
from model.scopeDetails import ScopeDetails


class Authorize:
    def __getTokenAuthHeader__(self, request1):
        logging.debug("__getTokenAuthHeader__ : This is from __getTokenAuthHeader__")
        auth = request1.headers.get("Authorization", None)
        if not auth:
            abort(
                make_response(jsonify(message="Authorization header is expected"), 401)
            )
        parts = auth.split()
        if len(auth) == 36:  # UUID format check
            token = auth
        elif parts[0].lower() != "bearer":
            abort(
                make_response(
                    jsonify(message="Authorization header must start with Bearer"), 401
                )
            )
        elif len(parts) == 1:
            abort(
                make_response(jsonify(message="Invalid header, token not found"), 401)
            )
        elif len(parts) > 2:
            abort(
                make_response(
                    jsonify(
                        message='Authorization header must be in the form of "Bearer token"'
                    ),
                    401,
                )
            )
        else:
            token = parts[1]
        return token

    def __getTokenScopes__(self, bearerToken):
        logging.debug("__getTokenScopes__ : This is from __getTokenScopes__")
        decoded = jwt.decode(bearerToken, options={"verify_signature": False})
        logging.debug("__getTokenScopes__ : token decoded : " + str(decoded))
        scopes = decoded["scope"]
        return scopes

    def __parseScope__(self, scopePath):
        logging.debug("__getTokenScopes__ : This is from __getTokenScopes__")
        # scopePath = "api.uopx.io/api:iam-python:v1:testAuthValidation.GET"
        # scopePath = "api.st.uopx.io/public"
        if scopePath != "":
            scopePathPrefixWithOptionalMethod = "/" + scopePath.replace(":", "/")
            lastIndexOfDotSeparator = scopePathPrefixWithOptionalMethod.rfind(".")
            if lastIndexOfDotSeparator != -1:
                strScopeMethod = scopePathPrefixWithOptionalMethod[
                    lastIndexOfDotSeparator + 1 : len(scopePathPrefixWithOptionalMethod)
                ]
                prefixPath = scopePathPrefixWithOptionalMethod[
                    0:lastIndexOfDotSeparator
                ]
                return ScopeDetails(scopePath, prefixPath, strScopeMethod)

    def validateAuthorization(self, request1):
        logging.debug("validate_token_scopes : This is from validate_token_scopes")
        bearerToken = self.__getTokenAuthHeader__(request)
        logging.debug("testAuthValidation : token : " + str(bearerToken))
        if len(bearerToken) == 36: # UUID format check
            return True
        scopesStr = self.__getTokenScopes__(bearerToken)
        logging.debug("testAuthValidation : scopes :  " + str(scopesStr))
        if not scopesStr:
            abort(make_response(jsonify(message="Scopes are expected"), 401))
        else:
            logging.debug(type(scopesStr))
            logging.debug("reuest URL : " + str(request1.path))
            logging.debug("reuest URL : " + str(request1.method))
            scopes = scopesStr.split()
            for scope in scopes:
                logging.debug("scope :  " + str(scope))
                scopeDetails = self.__parseScope__(scope)
                logging.debug(
                    "scopeDetails.httpMethod :  " + str(scopeDetails.httpMethod)
                )
                logging.debug(
                    "scopeDetails.httpMethod :  " + str(scopeDetails.pathprefix)
                )
                if scopeDetails is not None and scopeDetails.httpMethod is not None:
                    if scopeDetails.httpMethod.endswith("/public") or scopeDetails.httpMethod.endswith("/all") or scopeDetails.httpMethod.endswith("/context"):
                        logging.debug("default scope :  " + str(scopeDetails.scopePath))
                        return True
                    elif (
                        scopeDetails.httpMethod.upper() == request1.method.upper()
                        and scopeDetails.pathprefix.endswith(request1.path)
                    ):
                        logging.debug(
                            "Matcheds scope :  " + str(scopeDetails.scopePath)
                        )
                        return True
        return False

    def validateAzureAuthorization(self, request1, tenant_id, client_id):
        logging.debug("validate_token_scopes : This is from validate_token_scopes")
        bearerToken = self.__getTokenAuthHeader__(request)
        logging.debug("testAuthValidation : token : " + str(bearerToken))
        decoded = jwt.decode(bearerToken, options={"verify_signature": False})
        logging.debug("__getTokenScopes__ : token decoded : " + str(decoded))
        audience = decoded["aud"]
        issuer = decoded["iss"]
        requestIssuer = "https://login.microsoftonline.com/"+ tenant_id + "/v2.0"

        if audience == client_id and issuer == requestIssuer:
            return True

        return False