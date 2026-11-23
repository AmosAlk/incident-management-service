locals {
  kubeconfig_path = pathexpand(
    "~/.kube/${var.cluster_name}-kind"
  )
}

resource "kind_cluster" "platform" {
  name            = var.cluster_name
  node_image      = var.node_image
  wait_for_ready  = true
  kubeconfig_path = local.kubeconfig_path

  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    node {
      role = "control-plane"
    }

    node {
      role = "worker"
    }
  }
}