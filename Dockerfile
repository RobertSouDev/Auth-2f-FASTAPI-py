FROM python:3.12-slim

WORKDIR /app

RUN pip install pdm

COPY pyproject.toml ./

RUN pdm install

COPY app/ ./app/
COPY scripts/ ./scripts/

EXPOSE 8000

CMD ["pdm", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info", "--access-log"]

