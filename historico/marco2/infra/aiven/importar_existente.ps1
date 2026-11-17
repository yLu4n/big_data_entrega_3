param(
 [Parameter(Mandatory=$true)][string]$Projeto,
 [Parameter(Mandatory=$true)][string]$Servico,
 [Parameter(Mandatory=$true)][string]$Cloud,
 [Parameter(Mandatory=$true)][string]$Plano
)
$ErrorActionPreference='Stop'
foreach ($nomeParametro in @('Projeto','Servico','Cloud','Plano')) {
 $valorParametro=Get-Variable -Name $nomeParametro -ValueOnly
 if ([string]::IsNullOrWhiteSpace($valorParametro) -or $valorParametro -match '://|[\\/@?#\s]') {
  throw "Parametro $nomeParametro invalido: use o identificador exibido no painel Aiven, sem URI, senha, espacos ou barras. Projeto e Servico formam PROJETO/SERVICO."
 }
}
if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) { throw 'Instale Terraform 1.10 ou superior antes de continuar.' }
$secret=Read-Host 'Token de API Aiven (nao e a senha PostgreSQL)' -AsSecureString
$names=@('TF_VAR_aiven_api_token','TF_VAR_project_name','TF_VAR_service_name','TF_VAR_cloud_name','TF_VAR_plan','TF_LOG','TF_LOG_PATH')
$previous=@{}
foreach ($name in $names) { $previous[$name]=[Environment]::GetEnvironmentVariable($name,'Process') }
try {
 $env:TF_VAR_aiven_api_token=[System.Net.NetworkCredential]::new('', $secret).Password
 $env:TF_VAR_project_name=$Projeto
 $env:TF_VAR_service_name=$Servico
 $env:TF_VAR_cloud_name=$Cloud
 $env:TF_VAR_plan=$Plano
 $env:TF_LOG=$null
 $env:TF_LOG_PATH=$null
 & terraform "-chdir=$PSScriptRoot" init -input=false
 if ($LASTEXITCODE -ne 0) { throw 'Falha no terraform init.' }
 & terraform "-chdir=$PSScriptRoot" validate
 if ($LASTEXITCODE -ne 0) { throw 'Falha no terraform validate.' }
 $recursos=@(& terraform "-chdir=$PSScriptRoot" state list)
 if ($LASTEXITCODE -ne 0) { throw 'Falha ao consultar o estado. Nenhuma importacao ou apply foi executado.' }
 if ($recursos -contains 'aiven_pg.projeto') {
  # O estado pode conter senhas calculadas pelo provider. Nunca exibir seu conteudo.
  $estadoJson=& terraform "-chdir=$PSScriptRoot" state pull 2>$null
  if ($LASTEXITCODE -ne 0) { throw 'Falha ao verificar o vinculo existente no estado.' }
  $estado=($estadoJson -join "`n") | ConvertFrom-Json
  $vinculos=@($estado.resources | Where-Object {
   $_.mode -eq 'managed' -and $_.type -eq 'aiven_pg' -and $_.name -eq 'projeto' -and -not $_.module
  } | ForEach-Object { $_.instances } | Where-Object { -not $_.deposed })
  if ($vinculos.Count -ne 1 -or $vinculos[0].attributes.id -ne "$Projeto/$Servico") {
   throw 'O endereco aiven_pg.projeto ja esta vinculado a outro servico ou possui estado inesperado. Revise o estado antes de continuar; nenhum vinculo foi removido e nenhum apply foi executado.'
  }
  Write-Host 'O servico correto ja esta importado. Continuando para o plano.'
 } else {
  & terraform "-chdir=$PSScriptRoot" import -input=false aiven_pg.projeto "$Projeto/$Servico"
  if ($LASTEXITCODE -ne 0) { throw 'Falha na importacao. Nenhum apply foi executado.' }
 }
 & terraform "-chdir=$PSScriptRoot" plan -input=false -detailed-exitcode
 $planResult=$LASTEXITCODE
 if ($planResult -eq 1) { throw 'Falha no terraform plan.' }
 if ($planResult -eq 2) { Write-Warning 'O plano contem diferencas. Revise projeto, nome, cloud, plano e configuracoes do recurso. Este script nao executa apply.' }
 if ($planResult -eq 0) { Write-Host 'Importacao e plano sem alteracoes concluidos. Proteja o state; nao publique seu conteudo.' }
} finally {
 foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name,$previous[$name],'Process') }
 $secret.Dispose()
}
