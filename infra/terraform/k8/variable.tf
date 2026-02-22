variable "kube_context" {
  type = string
}

variable "data_lab_namespace" {
  type = string
}

variable "airflow_namespace" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "aws_access_key" {
  type = string
}

variable "aws_secret_key" {
  type = string
}

variable "raw_satellite_bucket" {
  type = string
}

variable "processed_aoi_bucket" {
  type = string
}

variable "airflow_dags_bucket" {
  type = string
}

variable "airflow_logs_bucket" {
  type = string
}

variable "analytics_db_name" {
  type = string
}

variable "analytics_db_user" {
  type = string
}

variable "analytics_db_password" {
  type = string
}
