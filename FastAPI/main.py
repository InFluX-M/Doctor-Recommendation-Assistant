from fastapi import FastAPI
from pydantic import BaseModel
import logging
import redis
import json
from fastapi import FastAPI, UploadFile, File, Request
import shutil
import os
from SpeechRecognition.speech_recognition import SpeechToText

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level to INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Define the format of the logs
)

PATH = "SpeechRecognition/temp/"

logger = logging.getLogger(__name__)
app = FastAPI()
r = redis.Redis(host='redis', port=6379, db=0)

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

@app.post("/requests/text/{user_id}")
async def get_requests(user_id: str, request: Request):
    data = await request.json()
    return {"request": data.get('text'), "response": ["response3", "response4"]}

@app.post("/requests/voice/{user_id}")  
async def get_requests(user_id: str, file: UploadFile = File(...)): 
    path = f"{PATH}{user_id}/"
    os.makedirs(path, exist_ok=True)
    file_path = f"{path}{file.filename}"    

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = SpeechToText().recognizer(file_path, True)
    return {"request": text, "response": ["response1", "response2"]}