import requests
from time import sleep
import httpx


from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

RequestsInstrumentor().instrument()
HTTPXClientInstrumentor().instrument()
SQLAlchemyInstrumentor().instrument(enable_commenter=True)


from sqlalchemy import create_engine, text
tracer = trace.get_tracer("tracer-demo")

with tracer.start_as_current_span("Demo script manual root span") as root_span:
    sync_engine = create_engine("postgresql+psycopg://world:world123@pgdb/world-db")

    with sync_engine.connect() as connection:
        result = connection.execute(text("select * from country"))
        for row in result:
            with tracer.start_as_current_span(f"Fetching data for {row[1]}") as root_span:
                r1 = requests.get("https://www.example.org")
                sleep(1)
                r2 = requests.get("https://www.example.org")

sleep(10)
