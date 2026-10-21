# Decisões técnicas e justificativas

## Dados e recorte

A fonte é a PNAD Contínua trimestral, atribuída ao IBGE pela documentação fornecida, com TXT posicionais do 1º e 2º trimestres de 2026. O layout SAS define as posições e os dicionários XLS definem os códigos e a disponibilidade das variáveis.

A equipe passou do recorte nacional inicialmente descrito para toda a Bahia (`UF=29`), incluindo Salvador (`Capital=29`). Esse recorte foi confirmado pelo usuário e é aplicado no ETL, nas verificações e na restrição do banco. Manter ambos os sexos e todas as posições na ocupação permite comparações entre empreendedoras e os demais ocupados. O filtro de ocupação é `VD4002=1`.

As 1.032.879 linhas originais resultaram em 464.457 ocupados no Brasil e 20.706 observações da Bahia após o recorte. Salvador tem 3.382 observações e já integra esse total. Não se somam Bahia e Salvador, nem se interpretam as observações de dois trimestres como pessoas distintas.

## Tratamento e volume

São selecionados 21 campos de origem para reduzir volume sem eliminar identificação amostral, peso, renda e perfil. A leitura em fluxo e a deduplicação em SQLite evitam carregar os 3,59 GB de TXT em memória. SQLite é somente área de trabalho; o banco de disponibilização é o PostgreSQL do Aiven. A exportação em Parquet preserva tipos e compacta a base; o CSV favorece inspeção e COPY para PostgreSQL.

Identificadores permanecem textuais para preservar zeros. Peso e renda usam Decimal e NUMERIC, evitando arredondamentos por ponto flutuante. Brancos opcionais viram NULL; renda ausente não vira zero. Códigos de ignorado são preservados quando válidos. Não se aplicaram imputação, subamostragem, agregação antecipada ou corte de rendas altas.

A chave pessoa-trimestre detecta repetições. Duplicatas idênticas são removidas; conteúdo diferente sob a mesma chave é retirado da base válida para revisão. SHA-256 da fonte e linha original permitem rastrear cada observação. Os artefatos tratados e o manifesto documentam a versão exata usada.

## Modelagem

Foi adotado um modelo relacional com tabela de observação no grão pessoa-trimestre, dimensão de fonte e dez dimensões de códigos. Os rótulos separados evitam repetição textual, enquanto chaves estrangeiras e CHECKs asseguram integridade. Não se afirma que há um cadastro de pessoas únicas no semestre.

As dimensões UF e capital contêm apenas o código 29 nesta versão. O banco contém 2 fontes e 47 códigos de referência, além das 20.706 observações. A chave composta inclui ano, trimestre, UPA, domicílio, painel, entrevista e ordem da pessoa. Há ainda unicidade por arquivo e linha, índices de consulta e restrição `UF=29`.

Views de Bahia e Salvador calculam os resumos na consulta. Soma de pesos estima totais; média de renda ponderada usa apenas as observações com renda informada no denominador. Não há uma view Brasil que apresente o recorte estadual como total nacional. Rendas são nominais, e erros padrão exigem tratamento adicional do desenho amostral.

## Infraestrutura

Aiven já hospeda o PostgreSQL em `defaultdb`, esquema `ef`. Terraform representa o serviço por `aiven_pg` e mantém o banco/tabelas SQL separados da camada de provisionamento. Essa separação evita misturar transformação de dados com criação de infraestrutura.

O serviço existente deve ser importado antes de qualquer apply. Criar um segundo serviço somente para demonstrar Terraform perderia a correspondência com a infraestrutura já utilizada e poderia gerar custos. Projeto, serviço, cloud/região e plano são variáveis obrigatórias sem valores inventados. O recurso não escolhe um plano pago por padrão.

O provedor está fixado e o lock traz checksums, favorecendo repetição da validação. `prevent_destroy` protege contra destruição/substituição planejada enquanto o recurso estiver na configuração, mas não substitui a revisão do plano nem impede ações diretas no painel.

## Segurança

Configurações públicas não contêm senha. Senhas e token chegam temporariamente por prompt/ambiente. O token de API é sensível/efêmero, e nenhum output expõe credenciais. Ainda assim, o state pode conter atributos sensíveis retornados pelo serviço; por isso ele é privado e excluído.

A evidência de TLS 1.3 comprova criptografia no carregamento histórico com `require`. Não se declara CA verificado, conta somente leitura criada ou credenciais rotacionadas. Essas melhorias dependem de configuração/autorização futura e são diferenciadas dos controles já implementados.

## Organização e estado desta revisão

O pacote organiza código, SQL, infraestrutura, documentação, dados e evidências em diretórios identificáveis. Ele é uma cópia de revisão construída fora do repositório. Nenhum commit, push, importação de infraestrutura, plan autenticado ou apply foi executado nesta etapa. A publicação futura deve acontecer somente após a revisão solicitada pelo usuário e o fechamento das pendências de infraestrutura.
