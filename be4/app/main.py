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
from opentelemetry.instrumentation.aio_pika import AioPikaInstrumentor
import asyncio 
import aio_pika

app = FastAPI()


@app.on_event("startup")
async def startup():
    Instrumentator().instrument(app).expose(app)


@app.get("/")
async def read_root():
    connection = await aio_pika.connect_robust(
        "amqp://user:bitnami@rabbitmq:5672/",
    )
    async with connection:
        routing_key = "test_queue"
        channel = await connection.channel()
        await channel.default_exchange.publish(
            aio_pika.Message(body=f"Hello {routing_key}".encode()),
            routing_key=routing_key,
        )
    return {"Hello": "World BE4"}


provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()
AioPikaInstrumentor().instrument()
