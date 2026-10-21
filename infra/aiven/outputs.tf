# Somente informações públicas de conexão. Sem URI autenticada ou senha.
output "conexao_publica" {
  description = "Parâmetros sem senha para configurar o cliente PostgreSQL."
  value = {
    host    = aiven_pg.projeto.service_host
    port    = aiven_pg.projeto.service_port
    dbname  = "defaultdb"
    user    = "avnadmin"
    sslmode = "require"
  }
}
