ARG AIRFLOW_VERSION=3.1.6
FROM apache/airflow:${AIRFLOW_VERSION}

COPY requirements/base.txt /tmp/requirements-base.txt

RUN pip install --no-cache-dir -r /tmp/requirements-base.txt
