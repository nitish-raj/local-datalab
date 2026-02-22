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

resource "kubernetes_secret_v1" "analytics_db_credentials_data_lab" {
  metadata {
    name      = local.analytics_db_secret_name
    namespace = kubernetes_namespace_v1.data_lab.metadata[0].name
  }

  data = {
    ANALYTICS_DB_NAME     = var.analytics_db_name
    ANALYTICS_DB_USER     = var.analytics_db_user
    ANALYTICS_DB_PASSWORD = var.analytics_db_password
  }

  type = "Opaque"
}

resource "kubernetes_secret_v1" "analytics_db_credentials_airflow" {
  metadata {
    name      = local.analytics_db_secret_name
    namespace = kubernetes_namespace_v1.airflow.metadata[0].name
  }

  data = {
    ANALYTICS_DB_NAME     = var.analytics_db_name
    ANALYTICS_DB_USER     = var.analytics_db_user
    ANALYTICS_DB_PASSWORD = var.analytics_db_password
  }

  type = "Opaque"
}

resource "kubernetes_persistent_volume_claim_v1" "analytics_postgres" {
  metadata {
    name      = "analytics-postgres-pvc"
    namespace = kubernetes_namespace_v1.data_lab.metadata[0].name
  }
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "8Gi"
      }
    }
  }
}

resource "kubernetes_deployment_v1" "analytics_postgres" {
  metadata {
    name      = "analytics-postgres"
    namespace = kubernetes_namespace_v1.data_lab.metadata[0].name
    labels = {
      app = "analytics-postgres"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "analytics-postgres"
      }
    }

    template {
      metadata {
        labels = {
          app = "analytics-postgres"
        }
      }

      spec {
        volume {
          name = "analytics-postgres-data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim_v1.analytics_postgres.metadata[0].name
          }
        }

        container {
          name  = "analytics-postgres"
          image = "postgres:16-alpine"

          env {
            name = "POSTGRES_DB"
            value_from {
              secret_key_ref {
                name = local.analytics_db_secret_name
                key  = "ANALYTICS_DB_NAME"
              }
            }
          }

          env {
            name = "POSTGRES_USER"
            value_from {
              secret_key_ref {
                name = local.analytics_db_secret_name
                key  = "ANALYTICS_DB_USER"
              }
            }
          }

          env {
            name = "POSTGRES_PASSWORD"
            value_from {
              secret_key_ref {
                name = local.analytics_db_secret_name
                key  = "ANALYTICS_DB_PASSWORD"
              }
            }
          }

          port {
            container_port = 5432
          }

          resources {
            requests = {
              cpu    = "250m"
              memory = "512Mi"
            }
            limits = {
              cpu    = "1000m"
              memory = "1Gi"
            }
          }

          volume_mount {
            name       = "analytics-postgres-data"
            mount_path = "/var/lib/postgresql/data"
          }
        }
      }
    }
  }

  depends_on = [
    kubernetes_secret_v1.analytics_db_credentials_data_lab,
    kubernetes_persistent_volume_claim_v1.analytics_postgres
  ]
}

resource "kubernetes_service_v1" "analytics_postgres" {
  metadata {
    name      = "analytics-postgres"
    namespace = kubernetes_namespace_v1.data_lab.metadata[0].name
    labels = {
      app = "analytics-postgres"
    }
  }

  spec {
    selector = {
      app = "analytics-postgres"
    }

    port {
      name        = "postgres"
      port        = 5432
      target_port = 5432
    }

    type = "ClusterIP"
  }

  depends_on = [
    kubernetes_deployment_v1.analytics_postgres
  ]
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

          env {
            name  = "PERSISTENCE"
            value = "1"
          }

          port {
            container_port = 4566
          }

          resources {
            limits = {
              cpu    = "1"
              memory = "1Gi"
            }
            requests = {
              cpu    = "0.5"
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
      aws_access_key              = var.aws_access_key
      aws_secret_key              = var.aws_secret_key
      localstack_endpoint_url     = local.localstack_endpoint_url
      kube_context                = var.kube_context
      data_lab_namespace          = var.data_lab_namespace
      airflow_namespace           = var.airflow_namespace
      raw_satellite_bucket        = var.raw_satellite_bucket
      processed_aoi_bucket        = var.processed_aoi_bucket
      airflow_dags_bucket         = var.airflow_dags_bucket
      airflow_logs_bucket         = var.airflow_logs_bucket
      aws_credentials_secret_name = local.aws_credentials_secret_name
      analytics_db_host           = "analytics-postgres.${var.data_lab_namespace}.svc.cluster.local"
      analytics_db_port           = 5432
      analytics_db_secret_name    = local.analytics_db_secret_name
    })
  ]

  depends_on = [
    kubernetes_service_v1.analytics_postgres,
    kubernetes_service_v1.localstack,
    kubernetes_secret_v1.airflow_aws_credentials,
    kubernetes_secret_v1.analytics_db_credentials_airflow
  ]
}
