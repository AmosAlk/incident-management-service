output "cluster_name" {
  description = "Name of the Kubernetes cluster."
  value       = kind_cluster.platform.name
}

output "kubeconfig_path" {
  description = "Path to the kubeconfig generated for the cluster."
  value       = local.kubeconfig_path
}