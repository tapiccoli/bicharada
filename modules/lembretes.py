import streamlit as st
from db import get_connection
from datetime import datetime, date, timedelta
from utils import parsear_data, formatar_data

def page():
    st.title("Lembretes")
    conn = get_connection()
    c = conn.cursor()

    rows = c.execute(
        "SELECT p.nome, s.descricao, s.data_servico, s.lembrete_dias"
        " FROM servicos s"
        " JOIN pets p ON s.pet_id=p.id"
    ).fetchall()

    lembretes = []
    for r in rows:
        # Attempt parse in DD/MM/YYYY, then ISO
        try:
            svc_iso = parsear_data(r['data_servico'])
            svc_date = datetime.fromisoformat(svc_iso).date()
        except:
            svc_date = date.fromisoformat(r['data_servico'])
        if date.today() >= svc_date + timedelta(days=r['lembrete_dias']):
            lembretes.append((r['nome'], r['descricao'], svc_date.strftime('%d/%m/%Y')))
    if lembretes:
        st.table(lembretes)
    else:
        st.info("Nenhum lembrete pendente.")
