import streamlit as st
import urllib.parse
from datetime import date
from db import get_connection

def page():
    st.header("🚚 Transporte")

    conn = get_connection()
    c    = conn.cursor()

    # 1) Busca pets e endereços
    pets_lista = c.execute(
        "SELECT id, nome, endereco FROM pets ORDER BY nome"
    ).fetchall()
    nomes = ["Nenhum"] + [f"{p[1]} ({p[0]})" for p in pets_lista]
    if len(nomes) <= 1:
        st.warning("Cadastre ao menos um pet para usar o transporte.")
        return

    # 2) Seleção de até 6 animais e coleta de endereços
    enderecos = []
    pet_ids   = []
    for i in range(1, 7):
        col1, col2 = st.columns([2, 3])
        with col1:
            selecao = st.selectbox(f"Animal {i}", nomes, key=f"trans_pet_{i}")
        with col2:
            if selecao != "Nenhum":
                pid = int(selecao.split("(")[-1].replace(")", ""))
                endereco_bd = {str(p[0]): p[2] for p in pets_lista}.get(str(pid), "")
                endereco_edit = st.text_input(
                    f"Endereço {i}",
                    value=endereco_bd,
                    placeholder="Digite ou corrija",
                    key=f"trans_end_{i}"
                )
                if endereco_edit:
                    enderecos.append(endereco_edit)
                    pet_ids.append(pid)

    if not enderecos:
        st.info("Selecione pelo menos um pet para ver a rota.")
        return

    # 3) Gera rota no Google Maps (apenas link, não grava)
    clinic = "Rua Demétrio Moreira da Luz, 1251, Caxias do Sul - RS"
    pontos = [clinic] + enderecos + [clinic]
    rota_url = "https://www.google.com/maps/dir/" + "/".join(
        urllib.parse.quote(p) for p in pontos
    )
    st.markdown(
        f"<a href='{rota_url}' target='_blank'>🔗 Abrir rota no Google Maps</a>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    # 4) Distância e custos
    km_total = st.number_input(
        "Distância total da rota (km)",
        min_value=0.0,
        step=0.1,
        key="trans_km_total"
    )
    preco_km = st.number_input(
        "Valor por km rodado (R$)",
        value=4.00,
        min_value=0.0,
        step=0.1,
        key="trans_preco_km"
    )
    valor_total = km_total * preco_km
    st.markdown(f"**💰 Valor total estimado: R$ {valor_total:.2f}**")

    # 5) Divisor e valor individual
    max_divs = len(enderecos)
    divisor  = st.number_input(
        "Número de divisões",
        value=max_divs,
        min_value=1,
        max_value=max_divs,
        step=1,
        key="trans_divisor"
    )
    valor_individual = st.number_input(
        "Valor cobrado por animal",
        value=(valor_total/divisor if divisor else 0.0),
        step=0.1,
        key="trans_valor_ind"
    )

    # 6) Tipo de transporte
    tipo = st.selectbox(
        "Tipo de Transporte",
        ["Compartilhado", "Exclusivo"],
        index=0,
        key="trans_tipo"
    )

    # 7) Registrar no financeiro
    if st.button("Registrar Transporte", key="trans_registrar"):
        registros = 0
        for pid in pet_ids:
            descricao = f"Transporte {tipo} em {date.today().strftime('%d/%m/%Y')}"
            # cria um serviço genérico em grupo "Transporte"
            c.execute(
                "INSERT INTO servicos (pet_id, grupo, descricao, data_servico, lembrete_dias) "
                "VALUES (?, ?, ?, ?, 0)",
                (pid, "Transporte", descricao, date.today().isoformat())
            )
            serv_id = c.lastrowid
            # registra no financeiro como débito em aberto
            c.execute(
                "INSERT INTO financeiro (servico_id, valor, pago) VALUES (?, ?, 0)",
                (serv_id, valor_individual)
            )
            registros += 1

        conn.commit()
        st.success(f"{registros} registro(s) de transporte adicionados ao financeiro.")
