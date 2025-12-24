locals {
  localstack_endpoint_url     = "http://localstack.${var.data_lab_namespace}.svc.cluster.local:4566"
  aws_credentials_secret_name = "airflow-aws-credentials"
}