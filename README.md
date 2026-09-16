# Personal Deal Intelligence (Streamlit)

Ferramenta **pessoal de inteligência de compras**.

> **Precisão > quantidade de resultados.**

O projeto não é um marketplace. Ele busca ofertas reais, mantém a identidade do produto consistente e **não inventa produtos, preços, cupons, cashback ou histórico**.

## O que faz

Você pode pesquisar em linguagem natural, por exemplo:

```text
Samsung Galaxy S25 256GB até R$ 4.000
```

O sistema:

1. Interpreta a intenção da busca (marca, modelo, capacidade, preço máximo etc.)
2. Consulta ofertas reais do Mercado Livre pela API oficial
3. Aplica matching estruturado para evitar variantes incompatíveis
4. Calcula o preço efetivo quando o frete está disponível
5. Registra observações reais de preço
6. Exibe histórico somente quando existem dados suficientes
7. Mostra cada oferta com **imagem, produto, loja, preço, frete, match e link da própria oferta**

## Stack

| Camada | Tecnologia |
|---|---|
| Interface | Streamlit |
| Linguagem | Python 3.10+ |
| Persistência | SQLite (MVP) |
| Provider | Mercado Livre — API oficial |
| Testes | pytest |

A arquitetura de providers permite adicionar outras fontes posteriormente, desde que exista uma fonte real e verificável.

## Estrutura

```text
.
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── src/
│   ├── domain/
│   │   ├── models.py
│   │   ├── parser.py
│   │   ├── matching.py
│   │   └── pricing.py
│   ├── providers/
│   │   ├── base.py
│   │   └── mercadolivre.py
│   ├── persistence/
│   │   ├── db.py
│   │   └── repository.py
│   └── services/
│       └── search_pipeline.py
└── tests/
    ├── test_parser.py
    ├── test_matching.py
    ├── test_pricing.py
    └── test_provider.py
```

## Instalação local

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Executar

```bash
streamlit run app.py
```

A aplicação ficará disponível localmente em `http://localhost:8501`.

## Testes

```bash
pytest -v
```

## Configuração

O uso básico não exige credenciais.

A busca utiliza o endpoint público do Mercado Livre. Caso seja necessário configurar um token oficial, use variável de ambiente ou o mecanismo de Secrets do Streamlit — nunca versione credenciais.

Exemplo de variável opcional:

```bash
export ML_ACCESS_TOKEN=seu-token
export PDI_DB_PATH=data/pdi.db
```

## Deploy no Streamlit Community Cloud

1. Abra o Streamlit Community Cloud
2. Crie um novo app
3. Selecione `edu-moraess/personal-deal-intelligence-streamlit`
4. Branch: `main`
5. Main file: `app.py`
6. Configure Secrets somente se algum provider exigir credencial
7. Faça o deploy

## Tratamento de erros do provider

A aplicação não transforma falhas de API em resultados fictícios:

| Situação | Status interno |
|---|---|
| 200 + ofertas | `AVAILABLE` |
| 403 | `UNAVAILABLE` |
| 401 | `AUTH_REQUIRED` |
| 429 | `RATE_LIMITED` |
| 5xx / timeout / rede | `ERROR` / `UNAVAILABLE` |

Quando o provider está indisponível, a interface informa o problema e não apresenta ofertas falsas.

## Matching de produto

O matching considera atributos relevantes da consulta para reduzir falsos positivos.

Exemplos:

| Consulta | Compatível | Incompatível |
|---|---|---|
| Galaxy S25 256GB | Galaxy S25 256GB | Galaxy S25 Ultra / S25+ / 128GB |
| RTX 5070 | RTX 5070 | RTX 5070 Ti |
| Monitor 27\" 165Hz | 27\" 165Hz | 24\" 165Hz |

A arquitetura também permite evoluir para identificadores reais como GTIN, SKU e MPN quando disponibilizados pelo provider.

## Histórico de preços

O histórico é formado a partir de **observações reais** das ofertas encontradas.

- Estatísticas de 7/30/90 dias só aparecem quando há dados suficientes.
- Observações duplicadas são controladas para evitar inflar artificialmente o histórico.
- Sem dados suficientes, o sistema informa **Histórico insuficiente**.
- Nenhuma curva ou série histórica artificial é criada.

### Limitação importante do SQLite

SQLite funciona para o MVP e para uso local. No Streamlit Community Cloud, o filesystem da aplicação não deve ser tratado como armazenamento persistente de longo prazo.

Para histórico e watchlist permanentes, a próxima evolução é migrar a camada `persistence` para PostgreSQL/Supabase ou outro banco persistente.

## Limitações atuais

- Provider real disponível atualmente: Mercado Livre.
- O endpoint público de busca normalmente não fornece frete numérico; em muitos casos só é possível identificar `free_shipping`.
- Cupons e cashback **não são aplicados** sem uma fonte verificável.
- Rate limits ou bloqueios do provider podem resultar em `403` ou `429`.

## Próxima fase

- Adicionar novos providers reais (Amazon, Magalu, KaBuM etc.)
- Evoluir Product Identity com GTIN/SKU/MPN
- Persistência PostgreSQL
- Alertas de preço
- Histórico mais robusto com coleta periódica
- Refinar ranking por aderência, preço efetivo e qualidade da oferta

## Segurança

- Não versionar API keys, tokens ou senhas.
- Segredos devem ficar em variáveis de ambiente ou Secrets.
- O projeto TypeScript original associado a este projeto continha credenciais em `.project-config.json`; se esse arquivo foi compartilhado publicamente, as credenciais devem ser rotacionadas.

## Licença

Uso pessoal. MIT.
