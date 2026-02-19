ARG AIRFLOW_VERSION
FROM apache/airflow:${AIRFLOW_VERSION}

COPY requirements/base.txt /tmp/requirements-base.txt

RUN pip install --no-cache-dir -r /tmp/requirements-base.txt
