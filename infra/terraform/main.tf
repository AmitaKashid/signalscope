locals {
  service_name_prefix = "signalscope-${var.environment}"

  common_labels = {
    app         = "signalscope"
    environment = var.environment
    managed_by  = "terraform"
  }

  required_apis = toset([
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "sqladmin.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com"
  ])
}

resource "google_project_service" "required" {
  for_each           = local.required_apis
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "containers" {
  location      = var.region
  repository_id = "signalscope"
  description   = "SignalScope container images"
  format        = "DOCKER"

  depends_on = [google_project_service.required]
}

resource "google_storage_bucket" "data" {
  name                        = var.data_bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false
  labels                      = local.common_labels

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.required]
}

resource "google_service_account" "api" {
  account_id   = "${local.service_name_prefix}-api"
  display_name = "SignalScope API runtime"
}

resource "google_project_iam_member" "api_storage" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_metrics" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_cloud_run_v2_service" "api" {
  name     = "${local.service_name_prefix}-api"
  location = var.region
  labels   = local.common_labels

  template {
    service_account = google_service_account.api.email
    timeout         = "60s"

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    containers {
      image = var.backend_image

      ports {
        container_port = 8000
      }

      env {
        name  = "SIGNALSCOPE_ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "SIGNALSCOPE_CORS_ORIGINS"
        value = join(",", var.cors_origins)
      }

      env {
        name  = "SIGNALSCOPE_DATA_DIR"
        value = "data/demo"
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
        cpu_idle = true
      }

      startup_probe {
        http_get {
          path = "/readyz"
          port = 8000
        }
        failure_threshold     = 3
        period_seconds        = 10
        timeout_seconds       = 3
        initial_delay_seconds = 2
      }

      liveness_probe {
        http_get {
          path = "/healthz"
          port = 8000
        }
      }
    }
  }

  depends_on = [
    google_project_service.required,
    google_project_iam_member.api_storage,
    google_project_iam_member.api_logging,
    google_project_iam_member.api_metrics
  ]
}

resource "google_cloud_run_v2_service_iam_member" "api_public_invoker" {
  name     = google_cloud_run_v2_service.api.name
  location = google_cloud_run_v2_service.api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service" "web" {
  name     = "${local.service_name_prefix}-web"
  location = var.region
  labels   = local.common_labels

  template {
    timeout = "30s"

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    containers {
      image = var.frontend_image

      ports {
        container_port = 3000
      }

      env {
        name  = "SIGNALSCOPE_API_BASE_URL"
        value = google_cloud_run_v2_service.api.uri
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }
    }
  }

  depends_on = [google_project_service.required]
}

resource "google_cloud_run_v2_service_iam_member" "web_public_invoker" {
  name     = google_cloud_run_v2_service.web.name
  location = google_cloud_run_v2_service.web.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_sql_database_instance" "postgres" {
  count            = var.create_cloud_sql ? 1 : 0
  name             = "${local.service_name_prefix}-postgres"
  database_version = "POSTGRES_16"
  region           = var.region
  settings {
    tier              = var.cloud_sql_tier
    availability_type = "ZONAL"
    disk_autoresize   = true
    disk_size         = 10
    disk_type         = "PD_SSD"
    backup_configuration {
      enabled = true
    }
    ip_configuration {
      ipv4_enabled = true
    }
  }
  deletion_protection = true
  depends_on          = [google_project_service.required]
}
