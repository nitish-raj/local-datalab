variable "kube_context" {
  description = "Kubernetes context name"
  type        = string
  default     = "local-datalab"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "aws_access_key" {
  description = "AWS access key"
  type        = string
}

variable "aws_secret_key" {
  description = "AWS secret key"
  type        = string
}

variable "aws_endpoint" {
  description = "AWS S3 endpoint URL"
  type        = string
}

variable "raw_satellite_bucket" {
  description = "Raw satellite data bucket name"
  type        = string
}

variable "processed_aoi_bucket" {
  description = "Processed AOI data bucket name"
  type        = string
}

variable "airflow_dags_bucket" {
  description = "Airflow DAGs bucket name"
  type        = string
}

variable "airflow_logs_bucket" {
  description = "Airflow logs bucket name"
  type        = string
}

variable "data_lab_namespace" {
  description = "Kubernetes namespace for data lab services"
  type        = string
}

variable "airflow_namespace" {
  description = "Kubernetes namespace for Airflow"
  type        = string
}
