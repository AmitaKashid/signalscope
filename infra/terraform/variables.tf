variable "project_id" {
  description = "Google Cloud project ID."
  type        = string
}

variable "region" {
  description = "Google Cloud region for serverless services."
  type        = string
  default     = "europe-west3"
}

variable "environment" {
  description = "Deployment environment label."
  type        = string
  default     = "staging"
}

variable "backend_image" {
  description = "Immutable container image URI for the FastAPI backend."
  type        = string
}

variable "frontend_image" {
  description = "Immutable container image URI for the Next.js frontend."
  type        = string
}

variable "cors_origins" {
  description = "Allowed browser origins for the API."
  type        = list(string)
  default     = []
}

variable "data_bucket_name" {
  description = "Globally unique Cloud Storage bucket name for media and evaluation artifacts."
  type        = string
}

variable "create_cloud_sql" {
  description = "Whether to create a Cloud SQL PostgreSQL instance. This can incur costs."
  type        = bool
  default     = false
}

variable "cloud_sql_tier" {
  description = "Cloud SQL machine tier used only when create_cloud_sql is true."
  type        = string
  default     = "db-f1-micro"
}
