PROJECT=local-datalab

.PHONY: kube-info
kube-info:
	kubectl config use-context local-datalab
	kubectl get ns
	kubectl get pods -A
	kubectl get cronjob -A

.PHONY: s3-buckets
s3-buckets:
	aws --endpoint-url=http://localhost:4566 s3 ls

.PHONY: port-forward
port-forward:
	kubectl port-forward svc/airflow-api-server 8080:8080 -n airflow >/tmp/airflow-port-forward.log 2>&1 &
	kubectl port-forward svc/localstack 4566:4566 -n data-lab >/tmp/localstack-port-forward.log 2>&1 &

.PHONY: sync-dags
sync-dags:
	aws --endpoint-url=http://127.0.0.1:4566 s3 sync \
		./airflow s3://airflow-dags/dags --delete

list-dags:
	aws --endpoint-url=http://127.0.0.1:4566 s3 ls s3://airflow-dags --recursive