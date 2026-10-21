# Segurança das informações

## Estratégia adotada

Há dois domínios de autenticação: a senha PostgreSQL autentica a carga e as consultas no banco; o token de API Aiven autentica o Terraform no plano de gerenciamento do serviço. Eles não são intercambiáveis. Os arquivos `config/postgres.*.json` contêm somente parâmetros sem senha. Não há token real nos arquivos Terraform, exemplos, README ou scripts desta revisão.

Os iniciadores PowerShell solicitam segredos com `Read-Host -AsSecureString`, transferem o valor temporariamente para a variável de ambiente necessária ao subprocesso e restauram a configuração anterior ao terminar. O texto precisa existir em memória para o cliente autenticar; `SecureString` não elimina essa necessidade. A senha não é gravada pelo iniciador em arquivo e não deve ser passada em uma URI autenticada na linha de comando ou em exemplos versionados.

Para Terraform, `aiven_api_token` é `sensitive` e `ephemeral` e chega por `TF_VAR_aiven_api_token`. `sensitive` esconde a exibição padrão; `ephemeral` evita persistir essa variável em planos/state. Isso não torna o estado inteiro seguro: `aiven_pg` pode trazer a senha gerada do banco como atributo calculado. Por isso, estado e planos são privados mesmo sem outputs de senha.

## Arquivos públicos e privados

Podem ser publicados: código, SQL, README, diagrama, configurações sem senha, Parquet/CSV públicos tratados, relatórios, hashes, `.terraform.lock.hcl` e evidências revisadas sem credenciais.

Não publicar: token, senha, `.env` real, chave privada, `terraform.tfvars`, `*.auto.tfvars`, state ou backup de state, arquivos de plano, `terraform show -json`, logs de depuração, diretório `.terraform`, ambientes virtuais e arquivos `.pgpass`/`pgpass.conf`. O `.gitignore` e o verificador estático desta revisão incluem essas categorias. Arquivos já rastreados anteriormente não são removidos do Git somente pela inclusão no `.gitignore`.

## TLS e acesso

A evidência histórica da carga no Aiven confirma TLS 1.3 com `sslmode=require`. Esse modo exige criptografia, mas não verifica o hostname com um certificado CA fornecido pela equipe. Quando o CA estiver disponível, o carregador aceita `verify-full` com `sslrootcert`. A implementação não afirma ter realizado essa validação de identidade.

O usuário `avnadmin` foi usado para a implantação existente. Para consumo pela aplicação, recomenda-se uma conta própria com somente os privilégios necessários, por exemplo leitura nas tabelas/views adequadas. Essa conta restrita e eventuais filtros de rede **não foram criados nem alterados nesta revisão**. A alteração de privilégios e da lista de IPs deve ser feita com uma sessão de gerenciamento autorizada, preservando o acesso da equipe.

## Verificação antes de publicar

```powershell
& ./.venv/Scripts/python.exe scripts/verificar_segredos.py --raiz . --saida evidencias/seguranca_revisao.json
```

O verificador relata arquivo, linha e classe de ocorrência, nunca o valor encontrado. Ele inspeciona arquivos de texto publicáveis e procura padrões de tokens, URI com senha, chaves privadas e valores literais em campos sensíveis. Não é uma certificação de ausência de segredos em binários, histórico remoto ou serviços externos. As evidências antigas foram reaproveitadas como registros históricos, com suas datas originais; não são provas de uma nova operação em 20/10/2026.

Ao publicar futuramente, revise também o histórico Git e os arquivos efetivamente preparados para commit. Se uma credencial real aparecer em histórico público, revogue-a/rotacione-a e trate o histórico segundo a política da equipe. Apagar o arquivo da versão atual, isoladamente, não invalida uma credencial já exposta. Esta revisão não declara que uma rotação foi realizada.

## Privilégios e estado do Terraform

Use um token com o menor escopo de gerenciamento que permita a importação do serviço. Não reutilize o token na aplicação. O estado local fica em `work/terraform-state`, excluído do pacote e do Git. Para colaboração, a equipe deverá escolher um backend de estado com criptografia, controle de acesso e bloqueio; essa infraestrutura de estado ainda não foi configurada.

Não publique saídas brutas de provedores para comprovar a atividade. Registre somente identificadores públicos, versões, data e um resumo do resultado de importação/plan. As evidências desta revisão indicam explicitamente quais verificações foram locais e quais operações ainda dependem do token Aiven.

## Fontes

- https://developer.hashicorp.com/terraform/language/manage-sensitive-data
- https://registry.terraform.io/providers/aiven/aiven/latest/docs/resources/pg
- Evidências de conexão do projeto em `evidencias/comparacao_integral_aiven.json` e `evidencias/carga_nuvem.json`.
