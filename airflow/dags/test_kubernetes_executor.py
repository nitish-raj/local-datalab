from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="test_kubernetes_executor",
    start_date=datetime(2025, 12, 1),
    catchup=False,
    tags=["debug", "k8s"],
) as dag:
    t1 = BashOperator(
        task_id="print_pod_info",
        bash_command="echo HOSTNAME=$HOSTNAME && env | sort && sleep 60",
    )
