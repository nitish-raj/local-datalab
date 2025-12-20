variable "aws_region" {
  type    = string
  default = "eu-central-1"
}

provider "aws" {
  region                      = var.aws_region
  access_key                  = "test"
  secret_key                  = "test"
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true

  endpoints {
    s3 = "http://localhost:4566"
  }
}

resource "aws_s3_bucket" "raw_satellite" {
  bucket = "raw-satellite-data"
}

resource "aws_s3_bucket" "processed_aoi" {
  bucket = "processed-aoi-data"
}

resource "aws_s3_bucket" "field_timeseries" {
  bucket = "field-timeseries-data"
}

resource "aws_s3_bucket" "airflow_dags" {
  bucket = "airflow-dags"
}