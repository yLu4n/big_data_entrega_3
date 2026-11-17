# Decisões técnicas e aprendizados da entrega 3

## Arquitetura implementada

O fluxo é **base tratada → API REST Flask → dashboard Plotly Dash**. A API centraliza leitura e validação; o dashboard consulta a API por HTTP e calcula os indicadores com as funções de `analytics.py`. Python permite reutilizar as regras estatísticas e manter uma única linguagem. A origem pode ser o CSV do pacote original ou um arquivo compatível indicado por `DATA_FILE`.

A execução local foi escolhida para permitir avaliação sem serviço de hospedagem, banco externo ou credenciais. `scripts/preparar_ambiente.py` automatiza o ambiente e `run.py` inicia os dois serviços. Terraform não é necessário para esse escopo. Não há hospedagem pública nem workflow de CI/CD implementados.

## Atualização e desempenho

A API relê a fonte em cada requisição, sem cache. O painel consulta na troca de filtros, atualização manual e intervalo de 60 segundos. Um snapshot por renderização mantém os cartões e gráficos consistentes. Apenas 14 variáveis analíticas são transferidas, sem identificadores domiciliares.

A resposta completa é adequada ao volume atual de 20.706 observações, mas leituras e transferências se repetem. Não foi realizado teste de carga ou dimensionamento para múltiplos usuários. Cache com invalidação quando a fonte mudar e endpoints que entreguem resultados agregados são **melhorias futuras**, não funcionalidades implementadas.

## Confiabilidade

O cliente valida status HTTP e conteúdo, possui limites de espera e não substitui uma API indisponível por dados locais. O dashboard retira os indicadores na falha e recupera os resultados quando uma atualização seguinte é bem-sucedida. A fonte deve ser atualizada por substituição atômica para evitar leitura de gravação incompleta.

Os testes executam a API real em portas temporárias e verificam atualização do arquivo, contrato, falha e recuperação, filtros e exportação. `scripts/validar_implantacao.py` também inicia o processo conjunto e solicita os seis indicadores ao dashboard por HTTP.

## Decisões estatísticas

As estimativas usam V1028. Empreendedores são empregadores e trabalhadores por conta própria, VD4009 = 8 ou 9. Renda ausente não vira zero; denominadores usam respostas válidas. Um trimestre por vez evita somar observações que podem corresponder à mesma pessoa em períodos distintos. As rendas são habituais nominais do trabalho principal.

As diferenças de sexo e raça/cor são descritivas e não demonstram causalidade. Não há erros padrão do desenho amostral ou deflacionamento. A base contém somente ocupados e não mede desemprego. Os indicadores dialogam com ODS 5 e ODS 18, mas não são indicadores oficiais de monitoramento dos objetivos.

## Aprendizados e evolução

Uma API consultada com frequência torna atualizações da fonte visíveis, mas não incorpora novas divulgações do IBGE automaticamente. A aquisição e o tratamento de novos períodos continuam sendo uma etapa anterior à disponibilização dos dados. Automatizar essa etapa, implementar agregações na API e avaliar a incerteza amostral são evoluções que dependem de trabalho adicional.

Os materiais da etapa anterior foram preservados em `historico/marco2/`; suas instruções não são dependências da aplicação atual.
