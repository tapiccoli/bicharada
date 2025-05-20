import streamlit as st
from db import get_connection
from utils import formatar_data

def page():
    st.title("Financeiro")

    conn = get_connection()
    c    = conn.cursor()

    tabs = st.tabs(["Em Aberto", "Quitados"])

    # ——— Aba “Em Aberto” ———
    with tabs[0]:
        st.subheader("Débitos em Aberto")

        # Busca só os registros em aberto
        rows = c.execute("""
            SELECT 
              f.id,
              s.data_servico AS data,
              p.nome         AS pet,
              s.descricao    AS servico,
              f.valor
            FROM financeiro f
            JOIN servicos s ON f.servico_id = s.id
            JOIN pets    p ON s.pet_id      = p.id
            WHERE f.pago = 0
            ORDER BY s.data_servico DESC
        """).fetchall()

        if not rows:
            st.info("Não há débitos em aberto.")
        else:
            # Prepara texto para cada opção
            options_aberto = {
                r["id"]: f'{formatar_data(r["data"])} – {r["pet"]} – {r["servico"]} (R$ {r["valor"]:.2f})'
                for r in rows
            }
            sel_ids = st.multiselect(
                "Selecione os débitos para marcar como pago:",
                options_aberto.keys(),
                format_func=lambda x: options_aberto[x],
                key="fin_multiselect_aberto"
            )

            if st.button("Marcar como pago", key="fin_pagar"):
                if not sel_ids:
                    st.warning("Selecione ao menos um registro para quitar.")
                else:
                    for _id in sel_ids:
                        c.execute("UPDATE financeiro SET pago = 1 WHERE id = ?", (_id,))
                    conn.commit()
                    st.success(f"{len(sel_ids)} registro(s) marcado(s) como pagos.")

    # ——— Aba “Quitados” ———
    with tabs[1]:
        st.subheader("Registros Quitados")

        rows = c.execute("""
            SELECT 
              f.id,
              s.data_servico AS data,
              p.nome         AS pet,
              s.descricao    AS servico,
              f.valor
            FROM financeiro f
            JOIN servicos s ON f.servico_id = s.id
            JOIN pets    p ON s.pet_id      = p.id
            WHERE f.pago = 1
            ORDER BY s.data_servico DESC
        """).fetchall()

        if not rows:
            st.info("Nenhum registro quitado.")
        else:
            data_quitado = []
            for r in rows:
                data_quitado.append({
                    "ID":          r["id"],
                    "Data":        formatar_data(r["data"]),
                    "Pet":         r["pet"],
                    "Serviço":     r["servico"],
                    "Valor (R$)":  r["valor"],
                })
            st.table(data_quitado)

            # Multiselect para reverter
            options_quitado = {
                r["id"]: f'{formatar_data(r["data"])} – {r["pet"]} – {r["servico"]} (R$ {r["valor"]:.2f})'
                for r in rows
            }
            sel_paid = st.multiselect(
                "Selecione os registros para reverter a Em Aberto:",
                options_quitado.keys(),
                format_func=lambda x: options_quitado[x],
                key="fin_multiselect_quitado"
            )

            if st.button("Reverter para Em Aberto", key="fin_reverter"):
                if not sel_paid:
                    st.warning("Selecione ao menos um registro para reverter.")
                else:
                    for _id in sel_paid:
                        c.execute("UPDATE financeiro SET pago = 0 WHERE id = ?", (_id,))
                    conn.commit()
                    st.success(f"{len(sel_paid)} registro(s) revertido(s) para Em Aberto.")
