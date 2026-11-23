# Implantação e infraestrutura do Empreendedorismo Feminino na Bahia

## Escopo da entrega

A implantação suportada é **local**, na máquina do usuário. A camada de visualização adiciona um processo Python com dois serviços HTTP: API de dados e dashboard. Não são provisionados recursos de nuvem, banco de dados, domínio, contêineres ou hospedagem externa.

Por isso, **Terraform não é necessário nesta entrega**. A preparação e a inicialização são descritas por scripts de automação que devem acompanhar o código no repositório. A presença dos arquivos na pasta, por si só, não comprova seu versionamento em Git.

## Componentes e recursos

| Componente | Configuração padrão | Responsabilidade |
| --- | --- | --- |
| Python + ambiente virtual | `.venv`, dependências em `requirements.txt` | Executar a aplicação com dependências isoladas |
| API Flask | `127.0.0.1:8000`, variável `API_PORT` | Reler e validar a base tratada, entregar JSON |
| Dashboard Dash | `127.0.0.1:8050`, variável `PORT` | Consultar a API, aplicar filtros e apresentar indicadores |
| Fonte | CSV dentro do ZIP original ou caminho `DATA_FILE` | Conter os dados tratados disponíveis no momento da consulta |
| Configuração | `.env`, modelo `.env.example` | Definir portas, fonte e intervalos |

O iniciador mantém a API em uma thread e o dashboard no processo principal. As portas precisam ser distintas e estar livres. Os dados são lidos do disco e processados em memória; não foi realizado dimensionamento de hardware nem teste de capacidade para múltiplos usuários.

## Pré-requisitos

- Python disponível no terminal. O ambiente efetivamente validado foi Windows com Python **3.14.3**. Outras versões e sistemas não foram homologados nesta entrega.
- Acesso à internet para instalar as dependências na preparação inicial. Com o ambiente preparado e a base disponível, a execução local não depende de serviços externos.
- O arquivo `Dados_tratados/Entrega_Tecnica_Fase_2_Bahia.zip`, ou um CSV compatível configurado em `DATA_FILE`.
- Permissão de escrita na pasta do projeto e disponibilidade das duas portas locais.

## Preparação automatizada

Execute a partir da raiz do projeto:

```powershell
python scripts/preparar_ambiente.py
```

O script cria `.venv` se necessário, instala `requirements.txt` e copia `.env.example` para `.env` somente se este último não existir. Pode ser executado novamente e preserva a configuração existente. A instalação termina com erro se o download ou a instalação de dependências falhar. As faixas de versões estão em `requirements.txt`; elas não constituem um lockfile de versões exatas.

Como alternativa manual:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Configuração

| Variável | Padrão | Uso |
| --- | --- | --- |
| `API_PORT` | `8000` | Porta da API local |
| `PORT` | `8050` | Porta do dashboard |
| `API_BASE_URL` | `http://127.0.0.1:8000` | URL da API no modo de processos separados |
| `API_TIMEOUT_SECONDS` | `15` | Tempo de espera por leitura na chamada HTTP do dashboard |
| `DATA_FILE` | vazio | Vazio usa o ZIP; outro valor aponta para um CSV tratado |
| `REFRESH_SECONDS` | `60` | Atualização automática do painel; mínimo efetivo de 15 segundos |

No modo conjunto, `run.py` define a URL da API local de acordo com `API_PORT`. Mudanças no `.env` exigem reinício. Mudanças no conteúdo da fonte já configurada são reconhecidas na consulta seguinte. Não coloque `.venv` nem `.env` no Git; o `.gitignore` já os exclui.

## Inicialização e encerramento

Com o ambiente preparado, um comando inicia os dois serviços:

```powershell
.\.venv\Scripts\python.exe run.py
```

Abra **http://127.0.0.1:8050**. Se alterar `PORT`, ajuste o endereço. Use **Ctrl+C** no terminal para encerrar o dashboard e a API iniciados pelo comando. A checagem de portas evita iniciar uma nova instância sobre uma versão antiga em execução.

Para executar em terminais separados:

```powershell
# Terminal 1
.\.venv\Scripts\python.exe api.py
# Terminal 2
.\.venv\Scripts\python.exe app.py
```

Nesse caso, encerre cada terminal com Ctrl+C e mantenha `API_BASE_URL` coerente com a porta da API.

## Pipeline de validação local

Após preparar o ambiente, execute em sequência:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/validar_implantacao.py
```

A primeira etapa verifica conflitos entre dependências. A segunda verifica cálculos, filtros, exportação, contrato, mudanças na base e falha/recuperação da fonte com chamadas HTTP reais. A terceira executa `run.py` em portas temporárias, testa API, contrato e dashboard, solicita os seis indicadores por HTTP e encerra somente o processo criado pelo teste. Ela grava [validacao_implantacao.json](validacao_implantacao.json). Uma falha retorna código de saída diferente de zero.

Essas etapas são um **pipeline local executável**. Não há workflow de CI/CD configurado nem implantação pública automática nesta entrega.

## Atualização da base e da aplicação

Para atualizar dados, valide um CSV com o mesmo layout e faça a substituição atômica do arquivo configurado em `DATA_FILE`, mantendo cópia da versão anterior. A API relê o conteúdo na consulta seguinte. Ela não coleta divulgações do IBGE automaticamente.

Para atualizar código ou dependências, encerre a instância em execução, atualize os arquivos, execute a preparação se `requirements.txt` mudou, rode o pipeline de validação e reinicie `run.py`. Para reverter, restaure a versão anterior de código e dados que você tenha preservado; revalide o ambiente antes de reiniciar.

## Diagnóstico

| Sintoma | Verificação e ação |
| --- | --- |
| Porta ocupada | Encerre a instância antiga ou configure portas diferentes em `API_PORT` e `PORT` |
| API responde, mas não há dados | `/health` verifica apenas o processo; consulte `/api/v1/observacoes` e confira a fonte |
| HTTP 503 na rota de dados | Verifique existência, layout e valores do CSV ou integridade do ZIP |
| Dashboard informa falha na API | Confira se a API está ativa e se `API_BASE_URL` corresponde ao endereço correto no modo separado |
| Alteração no `.env` não aparece | Encerre e reinicie os serviços |
| Outra máquina não acessa o painel | A entrega escuta apenas no endereço local `127.0.0.1` |

## Versionamento e atendimento ao requisito

Os artefatos que devem entrar no repositório são `run.py`, `api.py`, `app.py`, `dataset.py`, `data_source.py`, `analytics.py`, `assets/`, `requirements.txt`, `.env.example`, `.gitignore`, `api/openapi.json`, `scripts/`, `tests/`, `README.md` e `docs/`. A fonte de dados também precisa estar disponível no clone ou ter um procedimento de obtenção documentado; no fluxo padrão, inclua o ZIP tratado usado pela API. Os microdados brutos não são necessários para executar a visualização.

**Repositório da entrega:** [yLu4n/big_data_entrega_3](https://github.com/yLu4n/big_data_entrega_3). A raiz contém a aplicação atual; os materiais da etapa anterior estão preservados em `historico/marco2`. Código, scripts de automação, contrato, testes, documentação e o ZIP tratado acompanham esta revisão. O histórico de commits do repositório identifica as versões publicadas.

A validação inicial foi feita em uma pasta sem Git. A evidência que acompanha esta revisão foi regenerada na cópia de trabalho do repositório; o campo `repositorio_git_detectado` confirma a detecção local do checkout, não substitui a conferência do commit na branch remota. A pasta original de edição pode continuar fora do Git; o checkout preparado para publicação é uma cópia separada.

| Exigência | Avaliação |
| --- | --- |
| Infraestrutura complementar, caso necessária | Não há recursos de nuvem adicionais no escopo local |
| Automação da preparação e da execução | Atendida por `scripts/preparar_ambiente.py` e `run.py` |
| Documentação de implantação | Atendida por este guia, referenciado no README |
| Versionamento dos artefatos no repositório | Artefatos incluídos nesta revisão; versões identificadas pelos commits do repositório acima |
| Terraform | Não aplicável ao escopo atual, que usa automação local |

Uma eventual hospedagem pública exigirá outro plano de implantação e infraestrutura adequada. Os comandos atuais servem ao escopo local; não foi validada operação pública ou em produção.
