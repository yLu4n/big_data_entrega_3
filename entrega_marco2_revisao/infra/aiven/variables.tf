variable "aiven_api_token" {
  description = "Token de API Aiven fornecido somente durante a execução por TF_VAR_aiven_api_token. Não é a senha PostgreSQL."
  type        = string
  sensitive   = true
  ephemeral   = true
}

variable "project_name" {
  description = "Nome exato do projeto no painel Aiven. Não inferir a partir do host."
  type        = string
  validation {
    condition     = trimspace(var.project_name) != "" && !startswith(var.project_name, "PREENCHA")
    error_message = "Informe o nome real do projeto Aiven."
  }
}

variable "service_name" {
  description = "Nome exato do serviço PostgreSQL existente no painel Aiven."
  type        = string
  validation {
    condition     = trimspace(var.service_name) != "" && !startswith(var.service_name, "PREENCHA")
    error_message = "Informe o nome real do serviço existente."
  }
}

variable "cloud_name" {
  description = "Código de cloud/região real do serviço, obtido no Aiven."
  type        = string
  validation {
    condition     = trimspace(var.cloud_name) != "" && !startswith(var.cloud_name, "PREENCHA")
    error_message = "Informe a cloud/região real; este modelo não escolhe uma região nova."
  }
}

variable "plan" {
  description = "Identificador do plano atual no Aiven. Não há plano pago definido por padrão."
  type        = string
  validation {
    condition     = trimspace(var.plan) != "" && !startswith(var.plan, "PREENCHA")
    error_message = "Informe o identificador real do plano atual do serviço."
  }
}
