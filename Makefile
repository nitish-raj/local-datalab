.PHONY: kube-info
kube-info:
	kubectl config use-context $(KUBE_CONTEXT)
	kubectl get ns
	kubectl get pods -A
	kubectl get cronjob -A

.PHONY: list-s3-buckets
list-s3-buckets:
	aws --endpoint-url=$(AWS_ENDPOINT_URL) s3 ls

.PHONY: port-forward
port-forward:
	nohup kubectl port-forward svc/airflow-api-server 8080:8080 -n airflow >/tmp/airflow-port-forward.log 2>&1 &
	nohup kubectl port-forward svc/localstack 4566:4566 -n data-lab >/tmp/localstack-port-forward.log 2>&1 &
	disown %1 2>/dev/null || true
	disown %2 2>/dev/null || true

.PHONY: poststart
poststart:
	bash .devcontainer/poststart.sh

.PHONY: sync-dags
sync-dags:
	aws --endpoint-url=$(AWS_ENDPOINT_URL) s3 sync \
		./airflow/dags s3://$(AIRFLOW_DAGS_BUCKET)/dags \
		--exclude "*" --include "*.py" --delete

.PHONY: sync-raw-data
sync-raw-data:
	aws --endpoint-url=$(AWS_ENDPOINT_URL) s3 sync \
		./airflow/data s3://$(RAW_SATELLITE_BUCKET) --delete

.PHONY: list-dags
list-dags:
	aws --endpoint-url=$(AWS_ENDPOINT_URL) s3 ls s3://$(AIRFLOW_DAGS_BUCKET) --recursive

.PHONY:show-raw-data
show-raw-data:
	aws --endpoint-url=$(AWS_ENDPOINT_URL) s3 ls s3://$(RAW_SATELLITE_BUCKET) --recursive

.PHONY:show-processed-data
show-processed-data:
	aws --endpoint-url=$(AWS_ENDPOINT_URL) s3 ls s3://$(PROCESSED_AOI_BUCKET) --recursive

.PHONY:delete-processed-data
delete-processed-data:
	aws --endpoint-url=$(AWS_ENDPOINT_URL) s3 rm s3://$(PROCESSED_AOI_BUCKET) --recursive

.PHONY: show-dag-log
show-dag-log:
	aws --endpoint-url=$(AWS_ENDPOINT_URL) s3 ls s3://$(AIRFLOW_LOGS_BUCKET) --recursive

.PHONY: test-dags
test-dags:
	python -m pytest airflow/tests/test_dags/ -v

.PHONY: test-plugins
test-plugins:
	python -m pytest airflow/tests/test_plugins/ -v
