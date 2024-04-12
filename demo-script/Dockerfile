FROM python:3.9

RUN pip install SQLAlchemy httpx requests psycopg opentelemetry-distro opentelemetry-exporter-otlp
RUN opentelemetry-bootstrap -a install

COPY --chmod=755 wait.sh .
COPY main.py .
