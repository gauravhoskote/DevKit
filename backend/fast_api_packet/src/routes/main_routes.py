from fastapi import APIRouter

router = APIRouter()

@router.get("/resume")
def read_root():
    return {"message": "Hello, Resume!"}



