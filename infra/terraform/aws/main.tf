 provider "aws" {
   region                      = var.aws_region
   access_key                  = var.aws_access_key
   secret_key                  = var.aws_secret_key
   s3_use_path_style           = true
   skip_credentials_validation = true
   skip_requesting_account_id  = true
   skip_metadata_api_check     = true

   endpoints {
     s3 = var.aws_endpoint
   }
 }

provider "kubernetes" {
   config_path    = pathexpand("~/.kube/config")
   config_context = "local-datalab"
 }

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

variable "field_timeseries_bucket" {
  description = "Field timeseries data bucket name"
  type        = string
}

variable "airflow_dags_bucket" {
  description = "Airflow DAGs bucket name"
  type        = string
}

resource "aws_s3_bucket" "raw_satellite" {
  bucket = var.raw_satellite_bucket
}

resource "aws_s3_bucket" "processed_aoi" {
  bucket = var.processed_aoi_bucket
}

resource "aws_s3_bucket" "field_timeseries" {
  bucket = var.field_timeseries_bucket
}

resource "aws_s3_bucket" "airflow_dags" {
   bucket = var.airflow_dags_bucket
}

resource "kubernetes_manifest" "airflow_dags_sync_cronjob" {
   depends_on = [
     aws_s3_bucket.airflow_dags
   ]
   manifest = yamldecode(
     file("${path.module}/../k8/airflow-dags-sync.yaml")
   )
 }