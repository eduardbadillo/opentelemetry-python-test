from os import getenv

import requests
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry.instrumentation.logging import LoggingInstrumentor
import logging

from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
import aiohttp
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
import asyncio

logger_provider = LoggerProvider(
    resource=Resource.create(
        {
            "service.name": "api-gw",
        }
    ),
)
set_logger_provider(logger_provider)

exporter = OTLPLogExporter(endpoint="http://otel-collector:4317", insecure=True)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)

# Attach OTLP handler to root logger
logging.getLogger().addHandler(handler)


app = FastAPI()

async def fetch(url, session):
    async with session.get(url) as response:
        return await response.read()


@app.on_event("startup")
async def startup():
    Instrumentator().instrument(app).expose(app)


@app.get("/")
def read_root():
    logging.debug("Start API GW request")
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("foo"):
        # Do something
        logging.error("Hyderabad, we have a major problem.")
    requests.get(getenv("BE1_DSN")).json()
    requests.get(getenv("BE2_DSN")).json()
    requests.get(getenv("BE3_DSN")).json()
    logging.debug("Finish API GW request")
    return {"Hello": "World Main"}


@app.get("/async")
async def root_async():
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("async requests"):
        async with aiohttp.ClientSession() as session:
            tasks = [] 
            tasks.append(asyncio.ensure_future(fetch(getenv("BE1_DSN"), session)))
            tasks.append(asyncio.ensure_future(fetch(getenv("BE1_DSN"), session)))
            tasks.append(asyncio.ensure_future(fetch(getenv("BE2_DSN"), session)))
            tasks.append(asyncio.ensure_future(fetch(getenv("BE2_DSN"), session)))
            tasks.append(asyncio.ensure_future(fetch(getenv("BE3_DSN"), session)))
            tasks.append(asyncio.ensure_future(fetch(getenv("BE3_DSN"), session)))

            await asyncio.gather(*tasks)

    return {"Hello": "World Main ASync"}


@app.get("/be1")
def be1():
    return requests.get(getenv("BE1_DSN")).json()


@app.get("/be2")
def be2():
    return requests.get(getenv("BE2_DSN")).json()


@app.get("/be3")
def be3():
    return requests.get(getenv("BE3_DSN")).json()


provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)


LoggingInstrumentor().instrument(set_logging_format=True)
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()
AioHttpClientInstrumentor().instrument()
