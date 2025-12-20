PROJECT=local-datalab

.PHONY: kube-info
kube-info:
	kubectl config use-context local-datalab
	kubectl get ns
	kubectl get pods -A

.PHONY: airflow-url
airflow-url:
	minikube service airflow-webserver -n airflow --url

.PHONY: s3-buckets
s3-buckets:
	AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test aws --endpoint-url=http://localhost:4566 s3 ls
