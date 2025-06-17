from fastapi import APIRouter
from pydantic import BaseModel as bm1
from langchain_core.pydantic_v1 import BaseModel as bm2, Field
from langchain_aws import ChatBedrockConverse
from langchain_aws.retrievers import AmazonKnowledgeBasesRetriever
from botocore.client import Config
from langchain.chains import RetrievalQA
import json
from src.utils.utilities import object_to_dict, append_to_jsonl
from typing import List, Dict, Any
import os
import boto3
import time
import pandas as pd
import traceback
import requests
import time
import logging
import gc
from qdrant_client import QdrantClient, models
from typing import Callable, List
from pydantic import BaseModel

router = APIRouter()


class SamplePostBody(BaseModel):
    message : str

@router.post("/post")
def post_api(request:SamplePostBody):
    return {"rq_body": f"{request.message}"}

@router.get("/get")
def get_api():
    return {'response': 'Sample GET Response'}