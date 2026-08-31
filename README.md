# Assistente Inteligente para Controle Financeiro via WhatsApp

Projeto desenvolvido como Trabalho de Conclusão de Curso (TCC) com o objetivo de criar um assistente inteligente capaz de auxiliar no registro, organização e consulta de movimentações financeiras por meio do WhatsApp.

O sistema permite que o usuário envie mensagens em linguagem natural, como:

> "Paguei 120 reais de energia da empresa no Pix."

A mensagem é recebida pelo sistema, interpretada com auxílio de Inteligência Artificial e transformada em uma movimentação financeira estruturada. Os dados são armazenados em banco de dados e utilizados para atualizar automaticamente planilhas financeiras no Google Sheets.

---

## Funcionalidades

O assistente possui atualmente as seguintes funcionalidades:

- registro de entradas e saídas financeiras;
- interpretação de mensagens em linguagem natural;
- recebimento de comandos pelo WhatsApp;
- processamento e transcrição de mensagens de áudio;
- classificação das movimentações entre conta empresarial e pessoal;
- categorização das movimentações financeiras;
- registro de compras parceladas;
- distribuição automática das parcelas entre os meses correspondentes;
- aplicação de regras de fechamento de cartão;
- consulta de saldo mensal;
- consulta de valores de cartões;
- atualização automática das planilhas financeiras;
- geração de resumos mensais;
- resumo de despesas por categoria;
- resumo de despesas por forma de pagamento/cartão;
- criação e aplicação de regras personalizadas.

---

## Arquitetura do Sistema

De forma simplificada, o fluxo da aplicação ocorre da seguinte maneira:

```text
Usuário
   │
   ▼
WhatsApp
   │
   ▼
WhatsApp Cloud API
   │
   ▼
FastAPI / Webhook
   │
   ├──────────────► Transcrição de áudio
   │
   ▼
Interpretação da mensagem
   │
   ├── Comandos diretos
   ├── Regras cadastradas
   └── Inteligência Artificial
   │
   ▼
Processamento financeiro
   │
   ▼
Banco de Dados Turso
   │
   ▼
Geração dos relatórios
   │
   ▼
Google Sheets
```

O WhatsApp funciona como principal interface de interação com o usuário, enquanto o banco de dados mantém as informações estruturadas das movimentações.

As planilhas são utilizadas como uma forma visual de acompanhamento dos registros e dos resumos financeiros.

---

## Estrutura do Projeto

A aplicação está organizada em módulos para separar as diferentes responsabilidades do sistema.

```text
app/
├── __init__.py
├── db.py
├── finance.py
├── google_sheets.py
├── main.py
├── queries.py
├── reports.py
└── rules.py
```

### `app/main.py`

Ponto de entrada da aplicação e responsável pela coordenação do fluxo principal do assistente.

Principais responsabilidades:

- inicialização da aplicação FastAPI;
- verificação e recebimento do Webhook da WhatsApp Cloud API;
- envio de mensagens de resposta ao usuário;
- identificação de mensagens de texto e áudio;
- download e transcrição de mensagens de áudio;
- prevenção do processamento duplicado de eventos;
- interpretação de comandos diretos;
- envio de mensagens em linguagem natural para o modelo de IA;
- aplicação de regras previamente cadastradas;
- encaminhamento das solicitações para os módulos responsáveis por registros e consultas financeiras.

### `app/db.py`

Responsável pela configuração e criação da conexão com o banco de dados utilizado pela aplicação.

Principais responsabilidades:

- carregamento das variáveis de ambiente;
- obtenção da URL e do token de autenticação do Turso;
- configuração da conexão por meio da biblioteca `libsql_client`;
- disponibilização da conexão `db` para os demais módulos.

### `app/finance.py`

Responsável pela lógica de registro das movimentações financeiras e pelo tratamento de compras parceladas.

Principais responsabilidades:

- registro das transações no banco de dados;
- geração de identificadores únicos para compras;
- armazenamento das informações de parcelamento;
- cálculo do valor individual das parcelas;
- distribuição das parcelas entre meses subsequentes;
- utilização da regra de faturamento para cartões cadastrados;
- atualização da planilha correspondente ao mês da movimentação.

### `app/google_sheets.py`

Responsável pela integração da aplicação com o Google Sheets.

Principais responsabilidades:

- autenticação na API do Google por meio de uma conta de serviço;
- carregamento das credenciais através de variável de ambiente;
- conexão com as planilhas empresarial e pessoal;
- acesso às abas mensais;
- atualização das movimentações financeiras;
- atualização dos resumos por categoria;
- atualização dos resumos associados às formas de pagamento e cartões.

### `app/queries.py`

Responsável pelas consultas e pelos cálculos financeiros realizados sobre as movimentações armazenadas no banco de dados.

Principais responsabilidades:

- cálculo do total de entradas;
- cálculo do total de saídas;
- cálculo do saldo financeiro do mês corrente;
- consulta do valor associado a um cartão no mês corrente;
- filtragem das movimentações por conta e período;
- fornecimento dos resultados utilizados nas consultas realizadas pelo WhatsApp.

### `app/reports.py`

Responsável pela geração dos relatórios financeiros mensais e pelo tratamento do mês de referência das compras realizadas com cartão.

Principais responsabilidades:

- definição do mês de referência das compras de cartão a partir do fechamento;
- consulta das movimentações armazenadas no banco;
- separação dos registros por mês;
- separação das movimentações entre conta empresarial e pessoal;
- cálculo de entradas, saídas e saldo mensal;
- agrupamento das despesas por categoria;
- agrupamento das despesas por forma de pagamento/cartão;
- preparação dos dados das planilhas;
- atualização das abas mensais do Google Sheets.

### `app/rules.py`

Responsável pelo mecanismo de regras personalizadas do assistente.

Principais responsabilidades:

- armazenamento de regras definidas pelo usuário;
- consulta das regras existentes;
- atualização de regras previamente cadastradas;
- identificação de padrões presentes nas mensagens;
- aplicação automática do tipo de conta e da categoria associados ao padrão identificado.

Um exemplo de regra é:

```text
aprender: enel = empresa / energia
```

Após o cadastro dessa regra, uma mensagem contendo o termo `enel` pode utilizar automaticamente a conta `empresa` e a categoria `energia`.

---

## Processamento de uma Movimentação

Quando uma mensagem financeira é enviada pelo usuário, o fluxo básico é:

1. o WhatsApp encaminha a mensagem para o Webhook da aplicação;
2. o sistema identifica se o conteúdo recebido é texto ou áudio;
3. mensagens de áudio são transcritas;
4. comandos conhecidos são identificados diretamente;
5. mensagens em linguagem natural podem ser interpretadas com auxílio do modelo de IA;
6. regras personalizadas previamente cadastradas podem complementar a classificação;
7. os dados da movimentação são estruturados;
8. a transação é armazenada no banco de dados;
9. o relatório do mês correspondente é atualizado;
10. o usuário recebe uma confirmação pelo WhatsApp.

---

## Compras Parceladas

Para compras parceladas, o sistema divide o valor total pela quantidade de parcelas informada.

Por exemplo:

```text
Comprei 900 reais de mercadoria para empresa
no Santander parcelado em 3 vezes.
```

O sistema pode gerar:

```text
Parcela 1/3 → R$ 300,00
Parcela 2/3 → R$ 300,00
Parcela 3/3 → R$ 300,00
```

As parcelas são associadas por um identificador único da compra e distribuídas entre os respectivos meses.

Quando a forma de pagamento corresponde a um cartão cadastrado, o sistema também considera o dia de fechamento para determinar o mês inicial de referência da compra.

---

## Regras Personalizadas

O assistente permite cadastrar associações específicas para melhorar a classificação das movimentações.

Exemplo:

```text
aprender: enel = empresa / energia
```

Uma mensagem posterior como:

```text
Paguei 150 reais para Enel no Pix
```

pode utilizar a regra armazenada para classificar a movimentação como:

```text
Conta: Empresa
Categoria: Energia
Forma de pagamento: Pix
Valor: R$ 150,00
```

---

## Relatórios Financeiros

As movimentações armazenadas no banco são utilizadas para atualizar planilhas separadas para controle empresarial e pessoal.

Cada mês possui informações como:

- total de entradas;
- total de saídas;
- saldo;
- data da movimentação;
- tipo de movimento;
- categoria;
- forma de pagamento;
- descrição;
- valor;
- parcela atual;
- total de parcelas.

Também são gerados resumos de despesas por categoria e por forma de pagamento/cartão.

---

## Tecnologias Utilizadas

O projeto utiliza as seguintes tecnologias:

- **Python** — linguagem principal da aplicação;
- **FastAPI** — criação do servidor e dos endpoints do Webhook;
- **WhatsApp Cloud API** — comunicação entre o usuário e o assistente;
- **OpenAI API** — interpretação de linguagem natural e transcrição de áudio;
- **Turso / libSQL** — armazenamento das informações financeiras;
- **Google Sheets API** — atualização das planilhas financeiras;
- **gspread** — integração entre Python e Google Sheets;
- **Render** — hospedagem da aplicação;
- **Git e GitHub** — versionamento e armazenamento do código-fonte.

---

## Variáveis de Ambiente

Por segurança, credenciais e tokens utilizados pela aplicação não devem ser armazenados diretamente no código-fonte.

Entre as configurações utilizadas pelo projeto estão:

```env
OPENAI_API_KEY=
WHATSAPP_TOKEN=
TURSO_DATABASE_URL=
TURSO_AUTH_TOKEN=
GOOGLE_CREDENTIALS_JSON=
```

Configurações adicionais da implantação também podem ser transferidas para variáveis de ambiente.

> **Importante:** arquivos `.env`, chaves de API, tokens de autenticação e credenciais de contas de serviço não devem ser enviados para repositórios públicos.

---

## Execução

Após configurar o ambiente Python e instalar as dependências do projeto, a aplicação FastAPI pode ser iniciada com um servidor ASGI.

Exemplo:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Para o funcionamento completo, também é necessário configurar:

- banco de dados Turso;
- credenciais da Google API;
- planilhas do Google Sheets;
- WhatsApp Cloud API;
- OpenAI API;
- variáveis de ambiente necessárias.

---

## Objetivo Acadêmico

Este projeto foi desenvolvido como Trabalho de Conclusão de Curso e busca demonstrar a aplicação de técnicas de automação e processamento de linguagem natural no controle financeiro.

A proposta consiste em reduzir a necessidade de preenchimento manual de planilhas, permitindo que movimentações financeiras sejam registradas através de uma interface de comunicação já utilizada no cotidiano.

O sistema integra processamento de linguagem natural, APIs, banco de dados em nuvem e geração automatizada de informações financeiras.

---

## Possíveis Trabalhos Futuros

Como possibilidades de evolução do projeto, podem ser consideradas:

- geração de gráficos financeiros;
- relatórios financeiros mais avançados;
- consultas por períodos personalizados;
- alertas de despesas e vencimentos;
- definição de limites de gastos por categoria;
- ampliação dos mecanismos de autenticação;
- suporte a múltiplos usuários;
- aprimoramento da categorização automática;
- melhorias de desempenho para maiores volumes de movimentações.

---

## Autor

Projeto desenvolvido como Trabalho de Conclusão de Curso em Engenharia de Telecomunicações.
