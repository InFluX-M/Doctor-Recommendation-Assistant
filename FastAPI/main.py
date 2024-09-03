from fastapi import FastAPI
from pydantic import BaseModel
import logging
import redis
import json
from fastapi import FastAPI, UploadFile, File, Request
import shutil
import os
import sys

module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)

from SpeechRecognition.speech_recognition import SpeechToText

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level to INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Define the format of the logs
)

logger = logging.getLogger(__name__)

app = FastAPI()

# Connect to Redis
r = redis.Redis(host='localhost', port=6380, db=0)

class History(BaseModel):
    request: str
    response: list[str]

@app.post("/users/{user_id}")
async def add_history(user_id: str, history: History):
    r.rpush(f'user:{user_id}:history', json.dumps(history.model_dump()))
    return {"user": user_id, "history": history}

@app.put("/users/{user_id}")
async def delete_history(user_id: str):
    items = r.lrange(f'user:{user_id}:history', 0, -1)
    r.delete(f'user:{user_id}:history')
    return {"user": user_id, "deleted": ([json.loads(item) for item in items])}
    
@app.get("/users/{user_id}")
async def get_history(user_id: str):
    data = r.lrange(f'user:{user_id}:history', 0, -1)
    return {"history": ([json.loads(item) for item in data])}

@app.get("/specialties/{specialty}/{city}")
async def get_specialty(specialty: str, city: str):
    example = {"specialty": specialty, "city": city, "doctors": ["doctor1", "doctor2"]}
    return example

@app.post("/requests/text/{request}")
async def get_requests(request: str):
    example = {"request": "example", "response": ["response3", "response4"]}
    return example

@app.post("/requests/text")
async def get_requests(request: Request):
    # Extract the JSON data from the request
    data = await request.json()
    text = data.get('text')

    # Example response
    example = {"request": text, "response": ["response3", "response4"]}
    return example


@app.post("/requests/voice")
async def get_requests(file: UploadFile = File(...)):
    # Define the directory where you want to save the uploaded file
    upload_directory = "uploaded_files/"
    os.makedirs(upload_directory, exist_ok=True)  # Ensure the directory exists

    # Define the file path
    file_path = os.path.join(upload_directory, file.filename)

    # Save the uploaded file to the specified path
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Perform speech-to-text conversion
    speech_recognition = SpeechToText()
    text1 = speech_recognition.recognizer(file_path, True)
    text2 = speech_recognition.parallel_recognize(file_path)
    
    logger.info(f"Converted speech to text: {text1}")
    logger.info(f"Converted speech to text: {text2}")
    
    # Example response after saving the file
    response_example = {"request": "example", "response": ["response1", "response2"], "file_path": file_path}
    return response_example
