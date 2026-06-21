output "api_url" {
  description = "Public URL of the SignalScope API."
  value       = google_cloud_run_v2_service.api.uri
}

output "web_url" {
  description = "Public URL of the SignalScope frontend."
  value       = google_cloud_run_v2_service.web.uri
}

output "artifact_registry_repository" {
  description = "Docker Artifact Registry repository."
  value       = google_artifact_registry_repository.containers.name
}

output "data_bucket" {
  description = "Cloud Storage bucket used for media and evaluation artifacts."
  value       = google_storage_bucket.data.name
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL connection name, when a database instance was requested."
  value       = try(google_sql_database_instance.postgres[0].connection_name, null)
}
