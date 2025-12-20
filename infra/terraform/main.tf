# Kubernetes Resources (created first)

resource "kubernetes_namespace_v1" "data_lab" {
  metadata {
    name = "data-lab"
  }
}

resource "kubernetes_namespace_v1" "airflow" {
  metadata {
    name = "airflow"
  }
}

resource "kubernetes_deployment_v1" "localstack" {
  metadata {
    name      = "localstack"
    namespace = kubernetes_namespace_v1.data_lab.metadata[0].name
    labels = {
      app = "localstack"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "localstack"
      }
    }

    template {
      metadata {
        labels = {
          app = "localstack"
        }
      }

      spec {
        container {
          name  = "localstack"
          image = "localstack/localstack:latest"

          env {
            name  = "SERVICES"
            value = "s3"
          }

          env {
            name  = "EDGE_PORT"
            value = "4566"
          }

          env {
            name  = "AWS_DEFAULT_REGION"
            value = var.aws_region
          }

          port {
            container_port = 4566
          }

          resources {
            limits = {
              cpu    = "1000m"
              memory = "1Gi"
            }
            requests = {
              cpu    = "250m"
              memory = "512Mi"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service_v1" "localstack" {
  metadata {
    name      = "localstack"
    namespace = kubernetes_namespace_v1.data_lab.metadata[0].name
    labels = {
      app = "localstack"
    }
  }

  spec {
    selector = {
      app = "localstack"
    }

    port {
      name        = "http"
      port        = 4566
      target_port = 4566
    }

    type = "ClusterIP"
  }
}

resource "helm_release" "airflow" {
  name       = "airflow"
  repository = "https://airflow.apache.org"
  chart      = "airflow"
  namespace  = kubernetes_namespace_v1.airflow.metadata[0].name
  version    = "1.17.0"
  cleanup_on_fail = true
  timeout    = 3600
  max_history = 1

  values = [
    file("${path.module}/../airflow-values.yaml")
  ]

  depends_on = [
    kubernetes_service_v1.localstack
  ]
}

# AWS Resources (depends on K8 resources)

# Wait for localstack to be ready
resource "time_sleep" "wait_for_localstack" {
  depends_on = [kubernetes_service_v1.localstack]
  create_duration = "30s"
}

resource "aws_s3_bucket" "raw_satellite" {
  bucket = "raw-satellite-data"

  depends_on = [
    time_sleep.wait_for_localstack
  ]
}

resource "aws_s3_bucket" "processed_aoi" {
  bucket = "processed-aoi-data"

  depends_on = [
    time_sleep.wait_for_localstack
  ]
}

resource "aws_s3_bucket" "field_timeseries" {
  bucket = "field-timeseries-data"

  depends_on = [
    time_sleep.wait_for_localstack
  ]
}