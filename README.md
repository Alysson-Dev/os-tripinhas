# Os Tripinhas — FinOps Dashboard com IA

Projeto em Python com **FastAPI** (backend) e **Streamlit** (frontend) para análise de vendas (FinOps), com suporte a perguntas em linguagem natural convertidas para SQL via **Ollama**.

## Estrutura

- `api_tripinhas_novo.py`: API FastAPI com endpoints de dados, dashboard e NL2SQL.
- `app_tripinhas.py`: Interface Streamlit para visualizar métricas e consultar dados.
- `dataset (1).csv`: Base de vendas usada para carregar a tabela `vendas`.
- `finops.db`: Banco SQLite local (gerado/atualizado pela API).

## Funcionalidades

- Carga de CSV para SQLite
- Endpoint de listagem de vendas
- Endpoint de dashboard (total de vendas, lucro e pedidos)
- Perguntas em linguagem natural via modelo local no Ollama (`llama3:latest`)
- Interface web com Streamlit

## Requisitos

- Python 3.10+
- Ollama instalado e em execução (para funcionalidade de IA)

## Como executar

### 1) Instalar dependências

```bash
pip install fastapi uvicorn streamlit requests pandas pydantic
```

### 2) Subir a API

```bash
uvicorn api_tripinhas_novo:app --host 0.0.0.0 --port 8001 --reload
```

### 3) Subir o app Streamlit

```bash
streamlit run app_tripinhas.py --server.port 8501
```

## Endpoints principais

- `GET /dashboard`
- `GET /vendas`
- `POST /upload_csv`
- `POST /perguntar`
- `GET /status_ollama`

## Observações

- O app Streamlit está configurado para consumir a API em `http://127.0.0.1:8001`.
- O endpoint `/perguntar` exige o Ollama ativo em `http://localhost:11434`.
