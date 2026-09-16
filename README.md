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

## Mercado Livre e Access Token

A integração usa a API oficial do Mercado Livre. Embora alguns endpoints tenham funcionado sem autenticação em versões anteriores da API, **não devemos depender desse comportamento**. O projeto já aceita `ML_ACCESS_TOKEN` e o passa ao endpoint de busca.

O Mercado Livre documenta que respostas `401/403` podem ocorrer por ausência, expiração, permissões ou bloqueio do token/IP. Para o deploy, configure um Access Token oficial válido nos Secrets do Streamlit.

### Streamlit Community Cloud

Em **Settings → Secrets**, adicione:

```toml
ML_ACCESS_TOKEN = "SEU_ACCESS_TOKEN"
```

Nunca coloque esse token no código ou no GitHub.

### Ambiente local

```bash
export ML_ACCESS_TOKEN=seu-token
export PDI_DB_PATH=data/pdi.db
```

Depois reinicie o Streamlit e faça uma nova busca.

> Para uso pessoal, o token deve ser tratado como segredo. Se o token expirar, for revogado ou retornar `403`, gere/renove um token oficial e atualize o Secret.

## Deploy no Streamlit Community Cloud

1. Abra o Streamlit Community Cloud
2. Selecione `edu-moraess/personal-deal-intelligence-streamlit`
3. Branch: `main`
4. Main file: `app.py`
5. Em **Settings → Secrets**, configure `ML_ACCESS_TOKEN`
6. Salve os Secrets
7. Faça **Reboot app**

A aplicação não apresenta resultados fictícios quando a API está indisponível.

## Tratamento de erros do provider

| Situação | Status interno |
|---|---|
| 200 + ofertas | `AVAILABLE` |
| 401 | `AUTH_REQUIRED` |
| 403 | `UNAVAILABLE` com orientação para configurar/validar o token |
| 429 | `RATE_LIMITED` |
| 5xx / timeout / rede | `ERROR` / `UNAVAILABLE` |

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
- Rate limits, bloqueios ou problemas de autenticação do provider podem resultar em `403` ou `429`.

## Próxima fase

- Adicionar novos providers reais (Amazon, Magalu, KaBuM etc.)
- Evoluir Product Identity com GTIN/SKU/MPN
- Persistência PostgreSQL
- Alertas de preço
- Histórico mais robusto com coleta periódica
- Refinar ranking por aderência, preço efetivo e qualidade da oferta

## Segurança

- Não versionar API keys, tokens ou senhas.
- Segredos devem ficar em variáveis de ambiente ou Streamlit Secrets.
- O projeto TypeScript original associado a este projeto continha credenciais em `.project-config.json`; se esse arquivo foi compartilhado publicamente, as credenciais devem ser rotacionadas.

## Licença

Uso pessoal. MIT.
