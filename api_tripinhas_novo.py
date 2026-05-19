from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import requests
import pandas as pd
import os

app = FastAPI(title="API FinOps - Os Tripinhas", version="3.0")

DB_PATH = "finops.db"
CSV_PATH = "dataset (1).csv"

# ──── CONEXÃO ────
def db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ──── CARGA AUTOMÁTICA DO CSV ────
def inicializar_dados():
    if os.path.exists(CSV_PATH):
        try:
            print("⏳ Carregando dados do CSV...")
            df = pd.read_csv(CSV_PATH, sep=';', decimal=',', encoding='utf-8-sig')
            df.columns = [c.strip() for c in df.columns]
            conn = db_connection()
            df.to_sql("vendas", conn, if_exists="replace", index=False)
            conn.close()
            print(f"✅ Tabela 'vendas' pronta! {len(df)} registros carregados.")
        except Exception as e:
            print(f"❌ Erro ao carregar CSV: {e}")
    else:
        print(f"⚠️ Arquivo '{CSV_PATH}' não encontrado. Carregue via /upload_csv.")

inicializar_dados()

# ──── VERIFICAÇÃO DO OLLAMA ────
def ollama_esta_rodando() -> bool:
    try:
        r = requests.get("http://localhost:11434", timeout=3)
        return r.status_code == 200
    except Exception:
        return False

@app.get("/status_ollama", tags=["Inteligência Artificial"])
def status_ollama():
    if ollama_esta_rodando():
        return {"ollama": "✅ Rodando", "status": True}
    return {"ollama": "❌ Offline — abra o Ollama no seu PC", "status": False}

# ──── MODEL ────
class Pergunta(BaseModel):
    texto: str

# ──── UPLOAD CSV MANUAL ────
@app.post("/upload_csv", tags=["Dados"])
def upload_csv():
    try:
        if not os.path.exists(CSV_PATH):
            raise HTTPException(status_code=404, detail=f"Arquivo '{CSV_PATH}' não encontrado na pasta do projeto.")
        df = pd.read_csv(CSV_PATH, sep=';', decimal=',', encoding='utf-8-sig')
        df.columns = [c.strip() for c in df.columns]
        conn = db_connection()
        df.to_sql("vendas", conn, if_exists="replace", index=False)
        conn.close()
        return {"status": "✅ CSV carregado!", "linhas": len(df), "colunas": list(df.columns)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ──── LISTAR VENDAS ────
@app.get("/vendas", tags=["Dados"])
def listar_vendas(limite: int = 120):
    try:
        conn = db_connection()
        rows = conn.execute(f"SELECT * FROM vendas LIMIT {limite}").fetchall()
        conn.close()
        return {"vendas": [dict(r) for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Tabela 'vendas' não encontrada. Carregue o CSV primeiro.")

# ──── DASHBOARD ────
@app.get("/dashboard", tags=["Dashboard"])
def dashboard():
    try:
        conn = db_connection()
        total_vendas = conn.execute("SELECT SUM(Total_Vendas) FROM vendas").fetchone()[0] or 0
        total_lucro  = conn.execute("SELECT SUM(Lucro) FROM vendas").fetchone()[0] or 0
        total_pedidos = conn.execute("SELECT COUNT(*) FROM vendas").fetchone()[0] or 0

        por_categoria = conn.execute("""
            SELECT Categoria, SUM(Total_Vendas) as total, SUM(Lucro) as lucro
            FROM vendas GROUP BY Categoria ORDER BY total DESC
        """).fetchall()

        top_paises = conn.execute("""
            SELECT Pais, SUM(Total_Vendas) as total
            FROM vendas GROUP BY Pais ORDER BY total DESC LIMIT 10
        """).fetchall()

        conn.close()
        return {
            "resumo": {
                "total_vendas": round(total_vendas, 2),
                "total_lucro":  round(total_lucro, 2),
                "total_pedidos": total_pedidos
            },
            "por_categoria": [dict(r) for r in por_categoria],
            "top_paises":    [dict(r) for r in top_paises]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Tabela 'vendas' não encontrada. Carregue o CSV primeiro.")

# ──── IA — NL2SQL ────
@app.post("/perguntar", tags=["Inteligência Artificial"])
async def perguntar(pergunta: Pergunta):
    contexto = """
Você é um especialista em SQL para SQLite.
Converta a pergunta do usuário em um comando SQL válido.

Tabela: vendas
Colunas: ID_Pedido, Data_Pedido, ID_Cliente, Segmento, Regiao, Pais, Product_ID, Categoria, SubCategoria, Total_Vendas, Quantidade, Desconto, Lucro, Prioridade

REGRAS OBRIGATÓRIAS:
- Responda APENAS com o SQL puro.
- Sem explicações, sem markdown, sem ```.
- Use somente a tabela 'vendas'.
"""
    if not ollama_esta_rodando():
        raise HTTPException(status_code=503, detail="❌ Ollama não está rodando. Abra o Ollama no seu PC antes de usar a IA.")

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3:latest",
                "prompt": f"{contexto}\n\nPergunta: {pergunta.texto}\n\nSQL:",
                "stream": False
            },
            timeout=60
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Ollama não respondeu.")

        sql = response.json().get("response", "").strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()

        conn = db_connection()
        resultado = conn.execute(sql).fetchall()
        conn.close()

        return {
            "pergunta": pergunta.texto,
            "sql_gerado": sql,
            "total_resultados": len(resultado),
            "resposta": [dict(r) for r in resultado]
        }

    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="❌ Ollama não está rodando. Abra o Ollama primeiro.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
