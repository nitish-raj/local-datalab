KUBE_CONTEXT ?= local-datalab

.PHONY: kube-info
kube-info:
	kubectl config use-context $(KUBE_CONTEXT)
	kubectl get ns
	kubectl get pods -A
	kubectl get cronjob -A

.PHONY: minikube-dashboard
minikube-dashboard:
	minikube dashboard -p $(KUBE_CONTEXT) --url

.PHONY: list-s3-buckets
list-s3-buckets:
	aws --endpoint-url=$(AWS_ENDPOINT_URL) s3 ls

.PHONY: port-forward
port-forward:
	nohup kubectl port-forward svc/airflow-api-server 8080:8080 -n airflow >/tmp/airflow-port-forward.log 2>&1 &
	nohup kubectl port-forward svc/localstack 4566:4566 -n data-lab >/tmp/localstack-port-forward.log 2>&1 &
	nohup kubectl port-forward svc/analytics-postgres 5432:5432 -n data-lab >/tmp/analytics-db-port-forward.log 2>&1 &
	disown %1 2>/dev/null || true
	disown %2 2>/dev/null || true
	disown %3 2>/dev/null || true

.PHONY: poststart
poststart:
	bash .devcontainer/poststart.sh

.PHONY: port-forward-manager
port-forward-manager:
	bash .devcontainer/poststart.sh

.PHONY: sync-dags
sync-dags:
	aws --endpoint-url=$(AWS_ENDPOINT_URL) s3 sync \
		./orchestrator/dags s3://$(AIRFLOW_DAGS_BUCKET)/dags \
		--exclude "*" --include "*.py" --delete
	aws --endpoint-url=$(AWS_ENDPOINT_URL) s3 sync \
		./src s3://$(AIRFLOW_DAGS_BUCKET)/dags \
		--exclude "*" --include "*.py"

.PHONY: sync-raw-data
sync-raw-data:
	aws --endpoint-url=$(AWS_ENDPOINT_URL) s3 sync \
		./orchestrator/data s3://$(RAW_SATELLITE_BUCKET) --delete

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
	PYTHONPATH=src python -m pytest tests/test_dags/ -v

.PHONY: test-plugins
test-plugins:
	PYTHONPATH=src python -m pytest tests/test_plugins/ -v

.PHONY: test-loaders
test-loaders:
	PYTHONPATH=src python -m pytest tests/test_loaders/ -v

.PHONY: lock-requirements
lock-requirements:
	uv pip compile requirements/base.in --no-deps --upgrade -o requirements/base.txt
	uv pip compile requirements/dev.in --no-deps --upgrade -o requirements/dev.txt

.PHONY: lint
lint:
	ruff check orchestrator src tests

.PHONY: format
format:
	ruff format orchestrator src tests

.PHONY: precommit-install
precommit-install:
	pre-commit install

.PHONY: precommit-run
precommit-run:
	pre-commit run --all-files

.PHONY: dbt-debug
dbt-debug:
	DBT_PROFILES_DIR=transform/profiles dbt --project-dir transform debug

.PHONY: dbt-run
dbt-run:
	DBT_PROFILES_DIR=transform/profiles dbt --project-dir transform run

.PHONY: dbt-test
dbt-test:
	DBT_PROFILES_DIR=transform/profiles dbt --project-dir transform test

.PHONY: sync-ndvi-postgres
sync-ndvi-postgres:
	PYTHONPATH=src python -m loaders.s3_to_postgres
