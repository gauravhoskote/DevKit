from fastapi import APIRouter
from pydantic import BaseModel as bm1
from langchain_core.pydantic_v1 import BaseModel as bm2, Field
from langchain_aws import ChatBedrockConverse
from typing import List
from src.utils.json_utils import process_json, create_conversation_grouped
import json
from src.utils.utilities import object_to_dict, append_to_jsonl
from typing import List, Dict, Any
import os
from src.routes.JSONLVectorizer import JSONLVectorizer
from src.routes.BedrockQdrantQA import BedrockQdrantQA
import boto3
from src.routes.listpy import ll
import time
import pandas as pd
import traceback
import requests
import time
import logging
logging.getLogger("langchain_aws").setLevel(logging.ERROR)
logging.getLogger("httpx").disabled = True
import gc
from qdrant_client import QdrantClient, models
from typing import Callable, List


router = APIRouter()


region = "us-east-1"
s3 = boto3.client('s3', region_name=region)


def process_json(data: Dict) -> Dict:
    # Example logic — replace with yours
    data['processed'] = True
    return data




def load_checkpoint(checkpoint_file: str) -> dict:
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            return json.load(f)
    return {'last_index': -1}


def save_checkpoint(index: int, checkpoint_file: str):
    with open(checkpoint_file, 'w') as f:
        json.dump({'last_index': index}, f)


def handle_bucket(
    source_bucket: str,
    target_bucket: str,
    prefix: str = '',
    checkpoint_file: str = 'checkpoint.json'
):
    keys = list_all_json_keys(source_bucket, prefix)
    checkpoint = load_checkpoint(checkpoint_file)
    start_index = checkpoint['last_index'] + 1

    print(f"Resuming from index: {start_index} of {len(keys)} files")

    for i in range(start_index, len(keys)):
        key = keys[i]
        try:
            print(f"[{i}] Processing: s3://{source_bucket}/{key}")
            obj = s3.get_object(Bucket=source_bucket, Key=key)
            content = obj['Body'].read().decode('utf-8')
            data = json.loads(content)

            processed_data = process_json(data)

            output_key = f"processed/{key}" if not key.startswith("processed/") else key
            s3.put_object(
                Bucket=target_bucket,
                Key=output_key,
                Body=json.dumps(processed_data),
                ContentType='application/json'
            )

        except Exception as e:
            print(f"[ERROR] Failed at index {i}, key {key}: {e}")

        # Save checkpoint after each file
        save_checkpoint(i, checkpoint_file)

    print("✅ Finished all files.")

def list_mp3_files(bucket, prefix=""):
    paginator = s3.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)

    mp3_files = []
    for page in page_iterator:
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".mp3"):
                mp3_files.append(obj["Key"])
    return mp3_files

def start_transcription_job(job_name, media_uri, output_bucket):
    region = "us-east-1"
    transcribe = boto3.client("transcribe", region_name=region)
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": media_uri},
        MediaFormat="mp3",
        LanguageCode="en-US",
        OutputBucketName=output_bucket,
        Settings={
            "ShowSpeakerLabels": False,  # Not needed with channel identification
            "ChannelIdentification": True
        },
        ContentRedaction={
            "RedactionType": "PII",
            "RedactionOutput": "redacted"
        },
        # ModelSettings={
        #     "LanguageModelName": "general"
        # }
    )

@router.post("/ingest-transcripts")
def ingest_transcripts():
    input_bucket = "uopx-transcribe-call-audio-test" # This is in Manual account
    output_bucket = "call-transcript-poc-output"
    prefix = "call_recording"
    mp3_keys = list_mp3_files(input_bucket, prefix)
    print(f"Found {len(mp3_keys)} mp3 files.")
    print(mp3_keys)
    


    for idx, key in enumerate(mp3_keys):
        if idx >= 0:
            job_name = f"transcribe-{key.replace('call_recording/', '')[:-4]}"
            media_uri = f"s3://{input_bucket}/{key}"
            # print(f"Starting job: {job_name} for {key}")
            start_transcription_job(job_name, media_uri, output_bucket)

            if idx%10==0:
                print(f'Finished {idx} records!')

    return {"message": "The transcripts are being ingested"}


def list_json_files(bucket, prefix=""):
    paginator = s3.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)

    mp3_files = []
    for page in page_iterator:
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".json"):
                mp3_files.append(obj["Key"])
    return mp3_files


def load_json_from_s3(bucket_name, key, region='us-east-1'):
    s3 = boto3.client('s3', region_name=region)
    try:
        response = s3.get_object(Bucket=bucket_name, Key=key)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return None

@router.get("/process")
def load_data(cp: int):
    bucket = "call-transcript-poc-output"
    json_keys = list_json_files(bucket=bucket)
    # print("KEYSSSS")
    # print(json_keys)

    llist = ll
    # print('THIS IS LL')
    # print(llist)

    df = pd.read_csv("src/static/voice_agg.csv")
    checkpoint=cp
    start_time = time.time()

    for idx, kk in enumerate(json_keys):
        if idx >= checkpoint:
            try:
                key = kk.replace('redacted-transcribe-', '')[:32]
                # print(key)
                match = df[df['media_server_ixn_guid'] == key]
                if match.empty:
                    continue
                # print(f"Records for '{key}':")
                # print(match.iloc[0]['interaction_month'])

                #  metadata creation
                metadata = {}
                metadata['source'] = f"s3://{bucket}/{kk}"
                metadata['interaction_month'] = match.iloc[0]['interaction_month']
                metadata['media_server_ixn_guid'] = str(match.iloc[0]['media_server_ixn_guid'])
                metadata['interaction_id'] = str(match.iloc[0]['interaction_id'])
                metadata['interaction_direction'] = str(match.iloc[0]['interaction_direction'])
                metadata['agent_interaction_type'] = str(match.iloc[0]['agent_interaction_type'])
                metadata['degree_level'] = str(match.iloc[0]['degree_level'])
                metadata['manual_acc_s3_path'] = str(match.iloc[0]['s3_path'])
                metadata['category_name'] = str(match.iloc[0]['category_name'])
                metadata['college_name'] = str(match.iloc[0]['college_name'])
                metadata['channel_group'] = str(match.iloc[0]['channel_group'])
                
                llm = ChatBedrockConverse(
                        model="anthropic.claude-3-5-sonnet-20240620-v1:0",
                        temperature=0,
                        max_tokens=None,
                        region_name='us-east-1'
                    )

                structured_llm = llm.with_structured_output(QAPairList, include_raw=True)
                data = load_json_from_s3(bucket_name=bucket, key=kk,  )
                # print(data)
                transcripts = data.get('results').get('audio_segments')
                conversation = create_conversation_grouped(transcripts=transcripts)
                # print(conversation)
                response = structured_llm.invoke(f""" 
                                            Refer to the conversation below between consellor and student:
                                            
                                            {conversation}

                                            Give me the important highlights of this conversation in QAPairList format that can be used for the knowledge base.
                                            In places where you don't have an explicit question being asked. create one to represent the information given by the 
                                            Academic counsellor. Keep the questions concise and to the point.
                                        """)
                qa_list = object_to_dict(response.get('parsed').qa_pair_list)
                # print(qa_list)
                for qa in qa_list:
                    qa['metadata'] = metadata
                vectorizer = JSONLVectorizer(model_name="mixedbread-ai/mxbai-embed-large-v1")
                vectorizer.upload_to_qdrant(qa_list)
            except Exception as e:
                print(f'Error occured at index = {idx}')
                traceback.print_exc()
        gc.collect()
        elapsed_time = time.time() - start_time
        hrs, rem = divmod(elapsed_time, 3600)
        mins, secs = divmod(rem, 60)
        print(f"File {idx+1} processed - Elapsed time: {int(hrs):02}:{int(mins):02}:{int(secs):02}")

    return {'response': 'All ok'}




def get_query_response(llm, vectorizer, query):
    embed_fn = lambda text: vectorizer.generate_embeddings(text).tolist()
    qa = BedrockQdrantQA(
    qdrant_host="vector-db.st.uopx.io",
    collection_name="sample-poc",
    embed_fn=embed_fn,
    llm=llm)
    response = qa.answer(query)
    return {'query': query, 'response': response.content}




@router.get("/query-static-dataset")
def query_kb():
    llm = ChatBedrockConverse(
        model="anthropic.claude-3-5-sonnet-20240620-v1:0",
        temperature=0,
        max_tokens=None,
        region_name='us-east-1'
    )
    vectorizer = JSONLVectorizer(model_name="mixedbread-ai/mxbai-embed-large-v1")
    dataset = ["How do I set up payment from my employer?", "Where do I get the documents I need for reimbursement?", "When will my grade be posted so I can get reimbursed?", "What do I need to submit my voucher?", "How do I find my e-books?", "What can I do with e-books on the BibliU platform?", "How can I accelerate my program?", "What counts as attendance for online and campus students?", "How do I participate in class discussions?", "How should I communicate with my teachers and classmates?", "I'm having difficulty installing Microsoft Office 365.", "How many days must I participate per week?", "How do I access my classroom?", "How do I check if my transcripts have arrived?", "How can I see if my credits have been applied to my academic plan?", "Where can I find updates about my academic plan in the student portal?", "What should I do if my transcripts haven't been sent to WIN?", "Do you have all my transcripts?", "How many credits will transfer to my program?", "How do I log into my email?", "I was told 5-7 business days for any  excess funds to release but I saw on my account where it has Jul 10th as a date as well. I wanted to get clarity", "How much will my disbursement be?", "What is the process for releasing excess funds, and how does attendance affect it?", "Will my excess funds be released on the same day as class funds, since I have already posted in the first week discussion for attendance?", "Why did the policy change regarding the distribution of excess funds?", "Is there a way to opt in to receive my excess funds in a lump sum?", "Where can I track my excess funds?", "How can I handle the change in getting extra money for my school supplies and internet?", "How are disbursements sent or scheduled (DBC)?", "How do I check the status of my financial aid?", "What should I do if I haven't heard from the finance department about my financial aid?", "Where can I find the contact information for the finance department in the student portal?", "What does my financial aid cover?", "What is the basic process for receiving financial aid at College U?", "Who can I contact for help and support?", "What resources are available in the University Library?", "How can I ask for specific documents or articles from the University Library?", "How do I accept my loans?", "I applied for loans and trying to figure out how to get my loan?", "What type of device do I need to take online classes?", "What are the minimum hardware requirements for attending classes and completing coursework?", "Can I use a Chromebook for my classes?", "Can I use a tablet (like an iPad) to complete coursework?", "Can I use a mobile phone to access my courses?", "What functions may not work properly on a Chromebook?", "Are there limitations to using an iPad or Android tablet for online learning?", "Can I complete my classes using my cell phone?", "Will I be able to take proctored exams or use test-taking software on my device?", "What functions may not work properly on a Chromebook?", "Are there limitations to using an iPad or Android tablet for online learning?", "Can I access all features of the Student Portal or LMS on a mobile device?", "Will I be able to take proctored exams or use test-taking software on my device?", "What should I do if my device doesn’t meet the requirements?", "Does the university sell laptops?", "Does the university issue a computer?", "Who can I contact if I’m not sure whether my device will work?", "What additional steps do I need to complete for financial aid?", "The instructor said to download and then select track changes, which I did. I'm not seeing feedback. Are you able to help?", "What are Learning Teams, and how do I work with my team?", "Is there anything I can do to reduce my costs?", "How do I install Microsoft Office on my computer?", "How do I use Blackboard to access my course materials?", "What should I do on my first day of class?", "How do I download and understand the course syllabus?", "Getting Started After Registration", "I just registered—what should I do next?", "How do I log in to my student portal or learning platform for the first time?", "When will I get access to my classes?", "Where do I find my class schedule?", "How do I know what books or materials I need for class?", "Is there a checklist to help me prepare for the start of the term?", "Do I need to complete new student orientation?", "How do I access orientation, and how long does it take?", "What is covered in new student orientation?", "What should I know before my first day of class?", "Is there anything I can do to reduce my time to complete?", "Is there anything I can do to reduce the number of courses I need to complete?", "Who can I contact if I’m feeling overwhelmed or unsure where to start?", "Are there student communities or groups I can join?", "Can I talk to someone to help me get organized or set up a study plan?", "When does my first course start?", "How do I complete orienation?  Do I have to complete orienation?", "How do I access orienation.", "What should I do to get ready for my first day at College U?", "What is Prior Learning and Alternative Credits?", "Who can help me decide which classes to take at Sophia?", "How can Prior Learning and Alternative Credits help me finish my program faster?", "I forgot my password.", "How do scholarships work?", "Is there anything I can do to reduce my costs?", "Can I get an ID to show that I'm in school?", "What resources are in the Student Resources Guide?", "How can I join Facebook Events to connect with other students and alumni?", "What is my first assignment?", "How do I submit assignments in the online classroom?", "How do I upload a document in the online classroom or Blackboard?", "Who do I contact if I need support?", "What kind of computer do I need for my classes?", "How do I install Microsoft Office 365?", "What should I do if I have trouble setting up Microsoft Office 365?", "What are some good time management tips for students?", "How can I use my phone's calendar to manage my schedule?", "What should I do if I fall behind on my schoolwork?", "What credits can be transferred?", "What help can I get at the Center for Writing Excellence?", "How does SafeAssign help stop plagiarism?", "What help does the Center for Math Excellence offer to students?"]
    result = []
    for datapt in dataset:
        result.append(get_query_response(llm=llm, vectorizer=vectorizer, query=datapt))
    
    return result





@router.get("/get_all_pts")
def get_all_data_pts():
    client = QdrantClient(url = "https://vector-db.st.uopx.io", prefix="dfs-context", port=None, api_key="58ce41feac32a28d")
    result = []
    offset = 0
    while True:
        resp = client.scroll(
            collection_name="sample-poc",
            limit=100,
            offset=offset, 
            with_payload=True,
            with_vectors=False,
        )
        if resp[1] != None:
            print(resp[1])
            reslist  = object_to_dict(resp[0])
            offset = resp[1]
            result = result + reslist
        else:
            print(resp[1])
            reslist  = object_to_dict(resp[0])
            offset = resp[1]
            result = result + reslist
            break
    
    with open("src/static/qa_pairs.jsonl", "w") as f:
        for item in result:
            f.write(json.dumps(item) + "\n")
    print(result)
    return {}


@router.get("/get_something")
def get_all_data_pts():
    return 'This is something'