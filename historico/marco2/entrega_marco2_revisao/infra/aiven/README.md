# Infraestrutura Aiven em Terraform

Este diretório disponibiliza como código a infraestrutura de armazenamento utilizada: o serviço PostgreSQL Aiven `pg-3746e955`, no projeto `bigdatalkb`, cloud/região `do-nyc` e plano `developer-1`. O recurso `aiven_pg.projeto` declara seu provisionamento e permite gerenciar o serviço existente após a importação.

O serviço foi criado anteriormente pelo painel Aiven. Na verificação local de 20/10/2026, o estado já continha o vínculo correto `bigdatalkb/pg-3746e955`, com a região e o plano acima. Ainda é necessário executar um plano autenticado e revisar seu resultado para comprovar a correspondência atual entre código e infraestrutura. O arquivo `evidencias/terraform_validacao.json` na raiz da entrega registra a validação anterior, sem API; não comprova esse plano.

## Arquivos e limites

- `versions.tf`: Terraform >=1.10 e provedor Aiven fixado em 4.62.0; estado em `work/terraform-state` na raiz da entrega.
- `provider.tf` e `variables.tf`: autenticação por token sensível e efêmero e quatro parâmetros reais do serviço.
- `main.tf`: serviço PostgreSQL com projeto, nome, cloud/região e plano. `prevent_destroy` bloqueia destruições/substituições planejadas enquanto esse recurso continuar na configuração.
- `outputs.tf`: somente host, porta, banco, usuário e SSL; não expõe senha nem URI autenticada.
- `.terraform.lock.hcl`: versões e checksums do provedor. Deve ser versionado futuramente.
- `terraform.tfvars.example`: parâmetros públicos reais do serviço utilizado, sem token ou senha; copie para `terraform.tfvars` para usar diretamente a CLI.
- `imports.tf.example`: alternativa declarativa ao comando de importação.

O serviço Aiven administra os nós, armazenamento, rede e mecanismos de backup do produto. Esta configuração gerencia o serviço, e não declara máquinas virtuais ou buckets próprios que não existem no projeto. O banco `defaultdb` faz parte do serviço existente. Tabelas, índices, chaves e views do esquema `ef` continuam nos arquivos SQL, aplicados pelo carregador Python. Terraform não executa o ETL nem carrega os dados.

## Importar o serviço existente

1. No painel Aiven, obtenha o **nome do projeto**, **nome do serviço**, **código da cloud/região** e **identificador do plano atual**. Os dados de conexão PostgreSQL não revelam esses quatro valores com garantia.
2. Crie um token de API autorizado a consultar e gerenciar o serviço. Use o privilégio mínimo permitido pela conta. A senha de `avnadmin` não substitui esse token.
3. Instale Terraform e execute, a partir da raiz da entrega:

```powershell
./infra/aiven/importar_existente.ps1 -Projeto "bigdatalkb" -Servico "pg-3746e955" -Cloud "do-nyc" -Plano "developer-1"
```

O script solicita o token sem ecoá-lo, importa o recurso quando ainda não está vinculado e executa `plan`. Se o estado já contém o mesmo serviço, pula a importação; se contém outro vínculo no mesmo endereço, interrompe sem removê-lo. Ele não executa `apply`. Sem alterações, `plan -detailed-exitcode` retorna 0; alterações propostas retornam 2. Compare os parâmetros e a configuração importada até obter o resultado esperado. Não execute um plano que recrie, mova ou altere o plano do serviço sem revisar suas consequências.

A importação é equivalente a `terraform import aiven_pg.projeto PROJETO/SERVICO`, com variáveis corretas e token configurado. Ela adota o recurso no estado; não recria o serviço. Um posterior `apply` somente deve ocorrer após a revisão de um plano específico. Não há autorização implícita para migração de região, troca de plano, criação ou destruição de serviços nesta cópia de revisão.

## Provisionamento novo, se necessário no futuro

O mesmo recurso é uma declaração de provisionamento: com um nome novo e parâmetros reais, um plano pode propor criar outro serviço. Esse caminho **não foi executado** e não é o caminho de adoção do serviço que já contém os dados. Custos, limites da conta e compatibilidade do plano devem ser confirmados antes de aprovar qualquer criação. Após criar uma infraestrutura nova, configure o cliente com os outputs públicos e execute SQL/ETL/carga separadamente.

## Arquivos para o repositório

Versione os arquivos `.tf`, `.terraform.lock.hcl`, `.gitignore`, `terraform.tfvars.example`, `imports.tf.example`, `importar_existente.ps1` e este README, mantendo a estrutura `infra/aiven/`. A pasta contém a configuração publicável; o envio ao repositório permanece pendente por orientação do usuário. O projeto Aiven já existente é um pré-requisito e não é criado por esta configuração.

## Proteção do estado

O backend local cria estado em `work/terraform-state/aiven.tfstate`, fora dos arquivos publicáveis. A variável de API é `sensitive` e `ephemeral`; ainda assim, o provedor pode registrar a senha gerada do banco como atributo do recurso no estado. Proteja o estado com controle de acesso e criptografia no armazenamento utilizado. Não publique state, backups de state, arquivos de plano ou saída de `terraform show -json`.

Para uma equipe, configure posteriormente um backend remoto com autenticação, criptografia e controle de acesso. Esse armazenamento de estado não foi provisionado nesta revisão. Logs de depuração Terraform são desativados no iniciador para evitar a exposição de dados de autenticação.

Depois da importação, registre apenas uma síntese revisada: versão do Terraform/provedor, data, ID público do recurso e resultado do plano. Não anexe state ou plano bruto. Um resultado `validate` bem-sucedido não comprova que o serviço foi provisionado ou importado.

## Referências oficiais

- Recurso e formato de importação: https://registry.terraform.io/providers/aiven/aiven/latest/docs/resources/pg
- Provedor Aiven: https://registry.terraform.io/providers/aiven/aiven/latest/docs
- Importação: https://developer.hashicorp.com/terraform/language/import
- Dados sensíveis e variáveis efêmeras: https://developer.hashicorp.com/terraform/language/manage-sensitive-data
