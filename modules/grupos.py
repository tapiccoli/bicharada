import streamlit as st
from db import get_connection

def page():
    st.title("Grupos de Serviços")
    conn = get_connection(); c = conn.cursor()
    # Add group
    with st.form("add_grupo", clear_on_submit=True):
        nome = st.text_input("Novo grupo")
        if st.form_submit_button("Adicionar"):
            if nome:
                c.execute("INSERT OR IGNORE INTO grupos (nome) VALUES (?)", (nome,))
                conn.commit()
                st.success("Grupo adicionado")
    # List and edit/delete
    rows = c.execute("SELECT id,nome FROM grupos").fetchall()
    if rows:
        data = {r["id"]: r["nome"] for r in rows}
        sel = st.selectbox("Selecionar grupo para editar/excluir", list(data.keys()), format_func=lambda x: data[x])
        novo = st.text_input("Nome do grupo", value=data[sel])
        col1, col2 = st.columns(2)
        if col1.button("Salvar alteração"):
            c.execute("UPDATE grupos SET nome=? WHERE id=?", (novo, sel))
            conn.commit()
            st.success("Alterado")
        if col2.button("Excluir grupo"):
            c.execute("DELETE FROM grupos WHERE id=?", (sel,))
            conn.commit()
            st.success("Excluído")
    else:
        st.info("Nenhum grupo cadastrado.")
