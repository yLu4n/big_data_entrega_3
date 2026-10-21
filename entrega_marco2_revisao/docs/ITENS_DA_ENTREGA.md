# Mapeamento da atividade complementar do Marco 2

Documento de referência: `LUAN VICTOR CORTES DOS SANTOS CHAGAS BORGES - Documento sem título.pdf`, páginas 1 a 4, fornecido pelo usuário. A instrução atual do usuário é preparar os itens **sem modificar o repositório por enquanto**.

| Exigência | Onde está preparada | Situação real |
|---|---|---|
| 4. Arquivos Terraform representando a infraestrutura | `infra/aiven/*.tf`, lock, exemplos e instruções | Código local validado; importação e plan autenticado pendentes do token e metadados do painel |
| 5. Credenciais fora do repositório público e estratégia documentada | `.gitignore`, `docs/SEGURANCA.md`, iniciadores e verificador | Controles locais preparados e inspeção estática executada; não é certificação de histórico remoto |
| 6. Organização de artefatos no Git | Estrutura da cópia de revisão, pronta para comparação posterior | Publicação deliberadamente não executada; repositório original preservado |
| 7. README com fonte, base, período e características | Introdução, dados e origem do README | Documentado |
| 7. Problemas, decisões, transformações e justificativas | README e `docs/DECISOES_TECNICAS.md` | Documentado |
| 7. Estrutura e representação do modelo | README, `docs/modelagem.mmd`, SQL e dicionário JSON | Documentado |
| 7. Serviços, recursos e tecnologias | README e `infra/aiven/README.md` | Existente e pretendido diferenciados |
| 7. Ferramentas, dependências e sequência de execução | README, requirements e scripts | Documentado |
| 8. Justificativa da escolha tecnológica | `docs/DECISOES_TECNICAS.md` | Documentado |
| 9. Processo completo e camada de dados pronta | Base tratada, SQL, carga/evidências Aiven e nova documentação | Carga histórica comprovada em 14/10/2026; Terraform ainda sem adoção autenticada |

## O que falta para declarar a infraestrutura gerida por Terraform

1. Obter token da API com autorização adequada e preencher os quatro parâmetros reais do serviço.
2. Executar a importação do serviço existente em um estado protegido.
3. Revisar o plano autenticado e ajustar a declaração às características reais. Um validate não garante plano sem mudanças.
4. Guardar uma síntese revisada do resultado, sem state, token ou senhas.
5. Depois da revisão do usuário, incorporar os arquivos ao repositório e publicar a versão final.

Não foram criadas evidências artificiais de provisionamento. O serviço foi criado anteriormente e a infraestrutura ainda não foi importada pelo Terraform nesta revisão. Os dados continuam acompanhados dos registros históricos da carga anterior, e não de uma alegação de nova carga.
