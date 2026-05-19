import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8001"

st.set_page_config(
    page_title="Os Tripinhas — FinOps Dashboard",
    page_icon="🐾",
    layout="wide"
)

st.title("🐾 Os Tripinhas — Painel FinOps com IA")

menu = st.sidebar.selectbox(
    "Menu",
    ["Dashboard", "Carregar CSV", "Perguntar IA", "Ver Vendas"]
)

# DASHBOARD
if menu == "Dashboard":
    st.subheader("📊 Dashboard")

    try:
        res = requests.get(f"{API_URL}/dashboard")
        data = res.json()

        resumo = data["resumo"]

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Vendas", resumo["total_vendas"])
        col2.metric("Lucro", resumo["total_lucro"])
        col3.metric("Pedidos", resumo["total_pedidos"])

    except Exception as e:
        st.error(e)

# CSV
elif menu == "Carregar CSV":

    if st.button("Carregar CSV"):
        res = requests.post(f"{API_URL}/upload_csv")
        st.write(res.json())

# IA
elif menu == "Perguntar IA":

    pergunta = st.text_input("Pergunta")

    if st.button("Enviar"):
        res = requests.post(
            f"{API_URL}/perguntar",
            json={"texto": pergunta}
        )

        data = res.json()

        st.write("SQL:")
        st.code(data.get("sql_gerado", ""))

        st.write(data.get("resposta", []))

# VENDAS
elif menu == "Ver Vendas":

    res = requests.get(f"{API_URL}/vendas")
    data = res.json()

    df = pd.DataFrame(data["vendas"])

    st.dataframe(df)
