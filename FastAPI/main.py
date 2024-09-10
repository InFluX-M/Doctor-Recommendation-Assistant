from fastapi import FastAPI, Depends
from pydantic import BaseModel
import logging
import redis
import json
from fastapi import FastAPI, UploadFile, File, Request
import shutil
import os
from SpeechRecognition.speech_recognition import SpeechToText
from NLU.NLU import ONNXBertNERPredictor
from typing import List, Tuple
from Search.search import AsyncSearch
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level to INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Define the format of the logs
)

PATH = "SpeechRecognition/temp/"

logger = logging.getLogger(__name__)
logger.info("Application started")
r = redis.Redis(host='redis', port=6379, db=0)
logger.info("Connected to Redis")

model_metadata_path = './NLU/model_metadata.json'
onnx_model_path = './NLU/model.onnx'
nlu = ONNXBertNERPredictor(model_metadata_path, onnx_model_path)
logger.info("NLU model loaded")

class History(BaseModel):
    request: str
    response: List[Tuple[str, str]]
    response_time: float
    
class RequestModel(BaseModel):
    request: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    search = AsyncSearch()
    await search.initialize()
    app.state.search = search
    yield
    await search.close()

app = FastAPI(lifespan=lifespan)

async def get_es_client() -> AsyncSearch:
    return app.state.search

@app.post("/users/{user_id}")
async def add_history(user_id: str, history: History):
    logger.info(f"Adding history for user {user_id}")
    r.rpush(f'user:{user_id}:history', json.dumps(history.model_dump()))
    logger.info(f"History added for user {user_id}")
    return {"user": user_id, "history": history}

@app.put("/users/{user_id}")
async def delete_history(user_id: str):
    logger.info(f"Deleting history for user {user_id}")
    items = r.lrange(f'user:{user_id}:history', 0, -1)
    r.delete(f'user:{user_id}:history')
    logger.info(f"History deleted for user {user_id}")
    return {"user": user_id, "deleted": ([json.loads(item) for item in items])}
    
@app.get("/users/{user_id}")
async def get_history(user_id: str):
    logger.info(f"Getting history for user {user_id}")
    data = r.lrange(f'user:{user_id}:history', 0, -1)
    logger.info(f"History retrieved for user {user_id}")
    return {"history": ([json.loads(item) for item in data])}

@app.get("/specialties/{specialty}/{city}")
async def get_specialty(specialty: str, city: str):
    logger.info(f"Getting doctors for specialty {specialty} in city {city}")
    example = {"specialty": specialty, "city": city, "doctors": ["doctor1", "doctor2"]}
    logger.info(f"Got doctors for specialty {specialty} in city {city}")
    return example

@app.post("/requests/text/{user_id}")
async def get_requests(user_id: str, body: RequestModel):
    logger.info(f"Getting text request for user {user_id}")
    res = nlu.predict(body.request)
    history = History (
        request=res['request'],
        response=res["response"], 
        response_time=res['prediction_time_in_seconds']
    )
    r.rpush(f'user:{user_id}:history', json.dumps(history.model_dump()))
    logger.info(f"Got text request for user {user_id}")
    return res

@app.post("/requests/voice/{user_id}")  
async def get_requests(user_id: str, file: UploadFile = File(...), search: AsyncSearch = Depends(get_es_client)): 
    logger.info(f"Getting voice request for user {user_id}")
    path = f"{PATH}{user_id}/"
    os.makedirs(path, exist_ok=True)
    file_path = f"{path}{file.filename}"    

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = SpeechToText().recognizer(file_path, True)
    pred = nlu.predict(text)
    history = History (
        request=pred['request'],
        response=pred["response"], 
        response_time=pred['prediction_time_in_seconds']
    )
    r.rpush(f'user:{user_id}:history', json.dumps(history.model_dump()))
    logger.info(f"Got voice request for user {user_id}")
    
    logger.info(f"Pred {pred}")

    keyword = {}
    tmp = pred['response']
    for word, tag in tmp:
        if tag == 'O':
            continue
        elif 'loc' in tag:
            try:
                keyword['loc'].append(word)
            except KeyError:
                keyword['loc'] = [word]
        else:
            key = tag.split('-')[1]
            try:
                keyword[key] = ' '.join([keyword[key], word])
            except KeyError:
                keyword[key] = word

    res = await search.query(keyword) 
    logger.info(f"Res {res}")
    urls = [(doctor['display_name'], 'https://www.paziresh24.com' + doctor['url']) for doctor in res]
    return urls
