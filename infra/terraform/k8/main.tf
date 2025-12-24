resource "kubernetes_namespace_v1" "data_lab" {
  metadata {
    name = var.data_lab_namespace
  }
}

resource "kubernetes_namespace_v1" "airflow" {
  metadata {
    name = var.airflow_namespace
  }
}

resource "kubernetes_secret_v1" "airflow_aws_credentials" {
  metadata {
    name      = local.aws_credentials_secret_name
    namespace = kubernetes_namespace_v1.airflow.metadata[0].name
  }

  data = {
    AWS_ACCESS_KEY_ID     = var.aws_access_key
    AWS_SECRET_ACCESS_KEY = var.aws_secret_key
  }

  type = "Opaque"
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
        volume {
          name = "localstack-data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim_v1.localstack.metadata[0].name
          }
        }

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

          volume_mount {
            name       = "localstack-data"
            mount_path = "/var/lib/localstack"
          }
        }
      }
    }
  }
}

resource "kubernetes_persistent_volume_claim_v1" "localstack" {
  metadata {
    name      = "localstack-pvc"
    namespace = kubernetes_namespace_v1.data_lab.metadata[0].name
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "2Gi"
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
  name            = "airflow"
  repository      = "https://airflow.apache.org"
  chart           = "airflow"
  namespace       = kubernetes_namespace_v1.airflow.metadata[0].name
  version         = "1.18.0"
  cleanup_on_fail = true
  timeout         = 1800
  max_history     = 1

  values = [
    templatefile("${path.module}/../../airflow-values.yaml", {
      aws_region                  = var.aws_region
      localstack_endpoint_url     = local.localstack_endpoint_url
      kube_context                = var.kube_context
      data_lab_namespace          = var.data_lab_namespace
      airflow_namespace           = var.airflow_namespace
      raw_satellite_bucket        = var.raw_satellite_bucket
      processed_aoi_bucket        = var.processed_aoi_bucket
      field_timeseries_bucket     = var.field_timeseries_bucket
      airflow_dags_bucket         = var.airflow_dags_bucket
      aws_credentials_secret_name = local.aws_credentials_secret_name
    })
  ]

  depends_on = [
    kubernetes_service_v1.localstack,
    kubernetes_secret_v1.airflow_aws_credentials
  ]
}
