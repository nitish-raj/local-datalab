resource "aws_s3_bucket" "raw_satellite" {
  bucket = var.raw_satellite_bucket
}

resource "aws_s3_bucket" "processed_aoi" {
  bucket = var.processed_aoi_bucket
}

resource "aws_s3_bucket" "airflow_dags" {
  bucket = var.airflow_dags_bucket
}

resource "kubernetes_manifest" "airflow_dags_sync_cronjob" {
  depends_on = [
    aws_s3_bucket.airflow_dags
  ]
  manifest = yamldecode(
    templatefile("${path.module}/airflow-dags-sync.yaml.tmpl", {
      airflow_namespace           = var.airflow_namespace
      aws_region                  = var.aws_region
      localstack_endpoint_url     = local.localstack_endpoint_url
      airflow_dags_bucket         = var.airflow_dags_bucket
      aws_credentials_secret_name = local.aws_credentials_secret_name
    })
  )
}