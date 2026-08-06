FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
# Voir data-pipeline/api_data/Dockerfile pour le detail de PIP_EXTRA_ARGS
# (contournement reseau sandbox uniquement, vide par defaut).
ARG PIP_EXTRA_ARGS=""
RUN pip install --no-cache-dir ${PIP_EXTRA_ARGS} -r backend/requirements.txt

COPY backend/ backend/

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
