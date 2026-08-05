FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
# PIP_EXTRA_ARGS reste vide par defaut (installation standard, verification
# TLS active). Ne sert qu'a contourner un proxy interceptant le TLS sur un
# reseau restreint (ex. environnement de developpement sandbox) :
# docker compose build --build-arg PIP_EXTRA_ARGS="--trusted-host pypi.org --trusted-host files.pythonhosted.org"
ARG PIP_EXTRA_ARGS=""
RUN pip install --no-cache-dir ${PIP_EXTRA_ARGS} -r requirements.txt

COPY common/ common/
COPY api_data/ api_data/

EXPOSE 8000
CMD ["uvicorn", "api_data.main:app", "--host", "0.0.0.0", "--port", "8000"]
