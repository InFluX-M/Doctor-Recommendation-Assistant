from fastapi import FastAPI
from pydantic import BaseModel
import logging
import redis
import json
from fastapi import FastAPI, UploadFile


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

@app.get("/specialties")
async def get_specialties():
    pass

@app.get("/specialties/{specialty}/{city}")
async def get_specialty(specialty: str, city: str):
    pass

@app.post("/requests/text")
async def get_requests(request: str):
    pass

@app.post("/requests/voice")
async def get_requests(file: UploadFile):
    pass
