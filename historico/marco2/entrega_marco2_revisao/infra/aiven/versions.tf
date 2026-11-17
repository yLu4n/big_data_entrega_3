terraform {
  required_version = ">= 1.10.0, < 2.0.0"

  required_providers {
    aiven = {
      source  = "aiven/aiven"
      version = "= 4.62.0"
    }
  }

  # Estado local pode conter a senha gerada pelo serviço. Nunca versioná-lo.
  backend "local" {
    path = "../../work/terraform-state/aiven.tfstate"
  }
}
