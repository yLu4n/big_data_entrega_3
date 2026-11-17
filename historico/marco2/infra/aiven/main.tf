# Representação do serviço já existente. Importe-o antes de qualquer apply.
# O banco defaultdb é fornecido pelo serviço; o esquema ef é criado pelo SQL.
resource "aiven_pg" "projeto" {
  project      = var.project_name
  service_name = var.service_name
  cloud_name   = var.cloud_name
  plan         = var.plan

  lifecycle {
    prevent_destroy = true
  }
}
