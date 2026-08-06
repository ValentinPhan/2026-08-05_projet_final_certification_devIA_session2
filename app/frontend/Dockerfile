FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
# Voir data-pipeline/api_data/Dockerfile pour le detail de PIP_EXTRA_ARGS
# (contournement reseau sandbox uniquement, vide par defaut).
ARG PIP_EXTRA_ARGS=""
RUN pip install --no-cache-dir ${PIP_EXTRA_ARGS} -r requirements.txt

COPY frontend/ frontend/

EXPOSE 8501
# --server.address 0.0.0.0 : indispensable en conteneur, sinon Streamlit
# n'ecoute que sur localhost (injoignable depuis l'exterieur du conteneur).
CMD ["streamlit", "run", "frontend/main.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
