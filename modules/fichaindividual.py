import streamlit as st
from db import get_connection
from utils import formatar_data
from datetime import date

def page():
    st.title("Ficha Individual")

    conn = get_connection()
    c = conn.cursor()

    # 1) Espécies fixas
    ESPECIES = ["Cães","Gatos","Pássaros","Coelhos","Roedores Menores","Outros"]
    especie = st.selectbox("Espécie", ESPECIES, index=0, key="fi_especie")

    # 2) Pets filtrados por espécie
    pets = c.execute(
        "SELECT id, nome FROM pets WHERE especie = ? ORDER BY nome",
        (especie,)
    ).fetchall()
    if not pets:
        st.info(f"Não há pets cadastrados em {especie}.")
        return

    pet_map = {r["id"]: r["nome"] for r in pets}
    sel = st.selectbox(
        "Pet",
        [None] + list(pet_map.keys()),
        format_func=lambda x: "Selecione um pet" if x is None else pet_map[x],
        index=0,
        key="fi_pet_sel"
    )
    if sel is None:
        return

    pet = c.execute("SELECT * FROM pets WHERE id=?", (sel,)).fetchone()

    # Cria as abas para cada seção
    tab_labels = [
        "Dados do Animal",
        "Dados do Tutor",
        "Lembretes",
        "Histórico de Serviços",
        "Histórico de Transporte",
        "Histórico Financeiro"
    ]
    tabs = st.tabs(tab_labels)

    # Dados do Animal
    with tabs[0]:
        st.subheader("Dados do Animal")
        st.write(f"**Nome:** {pet['nome']}")
        st.write(f"**Nascimento:** {formatar_data(pet['data_nasc_pet'])}")
        st.write(f"**Raça:** {pet['raca']}")
        st.write(f"**Porte:** {pet['porte']}")
        st.write(f"**Peso (kg):** {pet['peso']:.2f}")
        st.write(f"**Tipo de Pelagem:** {pet['tipo_pelagem']}")
        st.write(f"**Agressividade:** {pet['agressividade']}")
        st.write(f"**Mensalista:** {pet['mensalista']}")

    # Dados do Tutor
    with tabs[1]:
        st.subheader("Dados do Tutor")
        st.write(f"**Nome:** {pet['tutor']}")
        st.write(f"**Aniversário (Mês/Dia):** {pet['data_nasc_tutor']}")
        st.write(f"**Telefone:** {pet['telefone']}")
        st.write(f"**E-mail:** {pet['email']}")
        st.write(f"**Endereço:** {pet['endereco']}")
        st.write(f"**Autorização de Imagem:** {pet['autorizacao_imagem']}")

    # Lembretes
    with tabs[2]:
        st.subheader("Lembretes")
        today = date.today().isoformat()
        rows = c.execute("""
            SELECT descricao, data_servico, lembrete_dias
            FROM servicos
            WHERE pet_id=? 
              AND date(data_servico, '+' || lembrete_dias || ' days') < date(?)
        """, (sel, today)).fetchall()
        if not rows:
            st.write("Nenhum lembrete vencido.")
        else:
            for r in rows:
                st.write(f"- {r['descricao']} (vencido desde {formatar_data(r['data_servico'])})")

    # Histórico de Serviços
    with tabs[3]:
        st.subheader("Histórico de Serviços")
        rows = c.execute("""
            SELECT s.data_servico, s.descricao, f.valor, f.pago
            FROM financeiro f
            JOIN servicos s ON f.servico_id=s.id
            WHERE s.pet_id=? AND s.grupo<>'Transporte'
            ORDER BY s.data_servico DESC
        """, (sel,)).fetchall()
        if not rows:
            st.write("Nenhum serviço registrado.")
        else:
            for r in rows:
                status = "Pago" if r["pago"] else "Em aberto"
                st.write(f"- {formatar_data(r['data_servico'])}: {r['descricao']} (R$ {r['valor']:.2f}) — {status}")

    # Histórico de Transporte
    with tabs[4]:
        st.subheader("Histórico de Transporte")
        rows = c.execute("""
            SELECT
              s.data_servico,
              s.descricao,
              f.valor,
              f.pago
            FROM financeiro f
            JOIN servicos   s ON f.servico_id = s.id
            WHERE s.pet_id=? AND s.grupo='Transporte'
            ORDER BY s.data_servico DESC
        """, (sel,)).fetchall()

        if not rows:
            st.write("Nenhum transporte registrado.")
        else:
            for r in rows:
                status = "Pago" if r["pago"] else "Em aberto"
                st.write(
                    f"- {formatar_data(r['data_servico'])}: {r['descricao']} "
                    f"(R$ {r['valor']:.2f}) — {status}"
                )

    # Histórico Financeiro Geral
    with tabs[5]:
        st.subheader("Histórico Financeiro")
        rows = c.execute("""
            SELECT s.data_servico, s.descricao, f.valor, f.pago
            FROM financeiro f
            JOIN servicos s ON f.servico_id=s.id
            WHERE s.pet_id=?
            ORDER BY s.data_servico DESC
        """, (sel,)).fetchall()
        if not rows:
            st.write("Nenhum registro financeiro.")
        else:
            total_aberto = sum(r["valor"] for r in rows if r["pago"]==0)
            total_pago   = sum(r["valor"] for r in rows if r["pago"]==1)
            st.write(f"**Total em aberto: R$ {total_aberto:.2f}**  |  **Total pago: R$ {total_pago:.2f}**")
            for r in rows:
                status = "Pago" if r["pago"] else "Em aberto"
                st.write(f"- {formatar_data(r['data_servico'])}: {r['descricao']} (R$ {r['valor']:.2f}) — {status}")
