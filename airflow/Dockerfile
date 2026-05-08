FROM apache/airflow:2.10.0-python3.11

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow
COPY airflow/requirements.txt /tmp/airflow-requirements.txt
COPY python/requirements.txt /tmp/project-python-requirements.txt
RUN pip install --no-cache-dir -r /tmp/airflow-requirements.txt \
    && pip install --no-cache-dir -r /tmp/project-python-requirements.txt
