import streamlit as st
from db import get_connection
from utils import formatar_data
from datetime import date

def page():
    st.title("Catálogo de Serviços")

    conn = get_connection()
    c = conn.cursor()

    # Migração: garante coluna 'valor' em 'servicos'
    try:
        c.execute("ALTER TABLE servicos ADD COLUMN valor REAL DEFAULT 0")
        conn.commit()
    except:
        pass

    st.header("Novo Serviço")
    with st.form("form_servico", clear_on_submit=True):
        # 1) Grupo de Serviço
        grupos = c.execute(
            "SELECT id, nome FROM grupos ORDER BY nome"
        ).fetchall()
        grupo_map = {r["id"]: r["nome"] for r in grupos}
        grupo_sel = st.selectbox(
            "Grupo de Serviço",
            list(grupo_map.keys()),
            format_func=lambda x: grupo_map[x],
            key="srv_grp"
        )

        # 2) Nome do Serviço
        nome = st.text_input("Nome do Serviço", key="srv_nome")

        # 3) Valor do Serviço
        valor = st.number_input(
            "Valor (R$)",
            min_value=0.0,
            value=0.0,
            format="%.2f",
            key="srv_valor"
        )

        # 4) Botão de salvar
        if st.form_submit_button("Salvar"):
            if not nome.strip():
                st.error("Informe o nome do serviço.")
            else:
                hoje_iso = date.today().isoformat()
                c.execute(
                    """
                    INSERT INTO servicos
                      (pet_id, grupo, descricao, data_servico, lembrete_dias, valor)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        None,
                        grupo_map[grupo_sel],
                        nome.strip(),
                        hoje_iso,
                        0,
                        valor
                    )
                )
                conn.commit()
                st.success("Serviço cadastrado com sucesso!")

    st.markdown("---")
    st.header("Serviços Cadastrados")
    rows = c.execute("""
        SELECT id, grupo, descricao, valor, data_servico
        FROM servicos
        ORDER BY grupo, descricao
    """).fetchall()

    if not rows:
        st.info("Nenhum serviço cadastrado.")
    else:
        tabela = []
        for r in rows:
            tabela.append({
                "ID":               r["id"],
                "Grupo":            r["grupo"],
                "Serviço":          r["descricao"],
                # duas casas decimais para valor
                "Valor (R$)":       f"{r['valor']:.2f}",
                "Data de Cadastro": formatar_data(r["data_servico"])
            })
        st.table(tabela)
