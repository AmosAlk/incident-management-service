variable "cluster_name" {
  description = "Name of the local Kubernetes cluster."
  type        = string
  default     = "incident-management"
}

variable "node_image" {
  description = "Pinned Kind Kubernetes node image."
  type        = string
  default     = "kindest/node:v1.35.0@sha256:452d707d4862f52530247495d180205e029056831160e22870e37e3f6c1ac31f"
}