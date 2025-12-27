PROJECT=local-datalab

.PHONY: kube-info
kube-info:
	kubectl config use-context local-datalab
	kubectl get ns
	kubectl get pods -A
	kubectl get cronjob -A

.PHONY: list-s3-buckets
list-s3-buckets:
	aws --endpoint-url=http://localhost:4566 s3 ls

 .PHONY: port-forward
port-forward:
	nohup kubectl port-forward svc/airflow-api-server 8080:8080 -n airflow >/tmp/airflow-port-forward.log 2>&1 &
	nohup kubectl port-forward svc/localstack 4566:4566 -n data-lab >/tmp/localstack-port-forward.log 2>&1 &
	disown %1 2>/dev/null || true
	disown %2 2>/dev/null || true

.PHONY: port-forward-manager
port-forward-manager:
	bash .devcontainer/port-forward-manager.sh

.PHONY: sync-dags
sync-dags:
	aws --endpoint-url=http://127.0.0.1:4566 s3 sync \
		./airflow/dags s3://airflow-dags/dags --delete

.PHONY: list-dags
list-dags:
	aws --endpoint-url=http://127.0.0.1:4566 s3 ls s3://airflow-dags --recursive

.PHONY:show-raw-data
show-raw-data:
	aws --endpoint-url=http://127.0.0.1:4566 s3 ls s3://raw-satellite-data --recursive

.PHONY:show-processed-data
show-processed-data:
	aws --endpoint-url=http://127.0.0.1:4566 s3 ls s3://processed-aoi-data --recursive