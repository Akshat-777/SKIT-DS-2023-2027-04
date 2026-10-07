FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    EMBEDDING_DEVICE=cpu \
    EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2 \
    HF_HOME=/models/hf

WORKDIR /service
COPY embedding_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY embedding_service/app ./app
COPY embedding_service/client.py ./client.py

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
