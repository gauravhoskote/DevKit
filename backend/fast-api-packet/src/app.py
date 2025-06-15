from fastapi import FastAPI, Request
from src.routes.main_routes import router as main_router
import logging
from typing import List
from src.utils.authorize import Authorize
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Response, status

logging.basicConfig(level=logging.INFO)

app = FastAPI()
app.include_router(main_router, prefix="/api/domain")
is_ready = True



# Excluded paths for authorization
excluded_paths = [
    "/health", 
    "/healthz/fail", 
    "/healthz/ready", 
    "/healthz/live",
    "/docs",
]

azure_ad_paths = []


@app.middleware("http")
async def authorize_request(request: Request, call_next):
    if "health" not in request.url.path:
        logging.info(f"Request path: {request.url.path}")

    # CORS preflight check
    if request.method.lower() == "options":
        return await call_next(request)

    # Skip authorization for excluded paths
    if any(path in request.url.path for path in excluded_paths):
        return await call_next(request)
    
    # Authorization code
    # authorizeObject = Authorize()
    # mocking auth
    authorized = True
    if any(path in request.url.path for path in azure_ad_paths):
        logging.info('Azure AD auth done for this path')
        # authorized = authorizeObject.validateAzureAuthorization(request, azure_app_tenant_id, azure_app_client_id)
    else:
        logging.info('Normal auth done for this path')
        # authorized = authorizeObject.validateAuthorization(request)

    if not authorized:
        logging.warning("Unauthorized access attempted: %s", request.url)
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
    logging.info("REQUEST CALLED!!!!")
    return await call_next(request)


@app.post("/healthz/fail")
def fail():
    global is_ready
    print("fail hook invoked")
    is_ready = False
    return {"message": "fail success"}


@app.get("/healthz/ready")
def ready(response: Response):
    if is_ready:
        return {"message": "ready"}
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"message": "not ready"}


@app.get("/healthz/live")
def live():
    return {"message": "live"}
