FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
# Voir data-pipeline/api_data/Dockerfile pour le detail de PIP_EXTRA_ARGS
# (contournement reseau sandbox uniquement, vide par defaut).
ARG PIP_EXTRA_ARGS=""
RUN pip install --no-cache-dir ${PIP_EXTRA_ARGS} -r requirements.txt

COPY common/ common/
COPY api_ia/ api_ia/

EXPOSE 8000
CMD ["uvicorn", "api_ia.main:app", "--host", "0.0.0.0", "--port", "8000"]
