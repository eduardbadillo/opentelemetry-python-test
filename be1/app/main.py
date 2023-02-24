from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.logger import logger as fastapi_logger
import logging

logger = logging.getLogger("gunicorn.error")
fastapi_logger.handlers = logger.handlers
fastapi_logger.setLevel(logger.level)

app = FastAPI()


@app.on_event("startup")
async def startup():
    Instrumentator().instrument(app).expose(app)


@app.get("/")
def read_root():
    fastapi_logger.warn("Request to the BE1")
    logger.warn("Request to the BE1")
    logging.warn("REquest from be1")
    return {"Hello": "World BE1"}
