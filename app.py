import streamlit as st
from utils import set_locale
from db import init_db
from modules import pets, grupos, servicos, registro_servicos, consultas, fichaindividual, transporte, lembretes, financeiro    

# Deve ser a primeira chamada Streamlit
st.set_page_config(page_title="Vet Bicharada", layout="wide")

# Inicializações
set_locale()
init_db()

# Menu lateral apenas com dropdown
menu = st.sidebar.selectbox(
    "Selecione a página",
    [
        "Pets",
        "Grupos de Serviços",
        "Serviços",
        "Registro de Serviços",
        "Consultas & Edições",
        "Ficha Individual",
        "Transporte",
        "Lembretes",
        "Financeiro"
    ],
    key="menu_principal"
)

if menu == "Pets":
    pets.page()
elif menu == "Grupos de Serviços":
    grupos.page()
elif menu == "Serviços":
    servicos.page()
elif menu == "Registro de Serviços":
    registro_servicos.page()
elif menu == "Consultas & Edições":
    consultas.page()
elif menu == "Ficha Individual":
    fichaindividual.page()
elif menu == "Transporte":
    transporte.page()
elif menu == "Lembretes":
    lembretes.page()
elif menu == "Financeiro":
    financeiro.page()