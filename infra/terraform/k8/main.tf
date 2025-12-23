variable "kube_context" {
  type    = string
}

variable "data_lab_namespace" {
  type    = string
}

variable "airflow_namespace" {
  type    = string
}

variable "aws_region" {
  type    = string
}

provider "kubernetes" {
  config_path    = pathexpand("~/.kube/config")
  config_context = var.kube_context
}

provider "helm" {
  kubernetes = {
    config_path    = pathexpand("~/.kube/config")
    config_context = var.kube_context
  }
}

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
            name = "localstack-data"
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
  name       = "airflow"
  repository = "https://airflow.apache.org"
  chart      = "airflow"
  namespace  = kubernetes_namespace_v1.airflow.metadata[0].name
  version    = "1.18.0"
  cleanup_on_fail = true
  timeout    = 1800
  max_history = 1

  values = [
    file("${path.module}/../../airflow-values.yaml")
  ]

  depends_on = [
    kubernetes_service_v1.localstack
  ]
}