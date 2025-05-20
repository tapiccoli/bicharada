import streamlit as st
from db import get_connection
from datetime import date

def page():
    st.title("Registro de Serviços")

    conn = get_connection()
    c    = conn.cursor()

    # — Migrações (se ainda não existirem)
    try:
        c.execute("ALTER TABLE servicos ADD COLUMN valor REAL DEFAULT 0")
        c.execute("ALTER TABLE servicos ADD COLUMN lembrete_dias INTEGER DEFAULT 0")
        conn.commit()
    except:
        pass

    st.header("Novo Registro de Serviço")

    # 1) Espécie
    ESPECIES = ["Cães","Gatos","Pássaros","Coelhos","Roedores Menores","Outros"]
    especie = st.selectbox("Espécie", ESPECIES, key="rs_especie")

    # 2) Pet
    pets = c.execute(
        "SELECT id, nome FROM pets WHERE especie = ? ORDER BY nome",
        (especie,)
    ).fetchall()
    pet_map = {r["id"]: r["nome"] for r in pets}
    pet_id = st.selectbox("Pet", list(pet_map), format_func=lambda x: pet_map[x], key="rs_pet")

    # 3) Grupo de Serviço
    grupos = c.execute("SELECT DISTINCT grupo FROM servicos ORDER BY grupo").fetchall()
    grupos = [g[0] for g in grupos]
    grupo  = st.selectbox("Grupo de Serviço", grupos, key="rs_grupo")

    # 4) Serviço (catálogo)
    catalogo = c.execute(
        "SELECT id, descricao, valor FROM servicos WHERE pet_id IS NULL AND grupo = ? ORDER BY descricao",
        (grupo,)
    ).fetchall()
    if not catalogo:
        st.warning("Não há serviços cadastrados neste grupo.")
        return

    catalogo_map = {r["id"]:(r["descricao"], r["valor"]) for r in catalogo}
    serv_id_cat = st.selectbox(
        "Serviço",
        list(catalogo_map),
        format_func=lambda sid: f"{catalogo_map[sid][0]} (R$ {catalogo_map[sid][1]:.2f})",
        key="rs_servico"
    )

    # 5) Data, valor editável, pago e dias de retorno
    data_serv   = st.date_input("Data do Serviço", value=date.today(), key="rs_data")
    valor_pad   = catalogo_map[serv_id_cat][1]
    valor       = st.number_input("Valor (R$)", min_value=0.0, value=valor_pad, format="%.2f", key="rs_valor")
    pago        = st.checkbox("Pago", value=False, key="rs_pago")
    dias_retorno= st.number_input("Dias de Retorno", min_value=0, value=0, step=1, key="rs_retorno")

    # 6) Registrar (botão normal)
    if st.button("Registrar Serviço", key="rs_submit"):
        # 6.1) Clona o serviço do catálogo em 'servicos' com pet_id e lembrete
        c.execute("""
            INSERT INTO servicos
              (pet_id, grupo, descricao, data_servico, lembrete_dias, valor)
            SELECT
              ?, grupo, descricao, ?, ?, valor
            FROM servicos
            WHERE id = ?
        """, (
            pet_id,
            data_serv.isoformat(),
            dias_retorno,
            serv_id_cat
        ))
        new_serv_id = c.lastrowid

        # 6.2) Insere no financeiro apontando para o clone
        c.execute(
            "INSERT INTO financeiro (servico_id, valor, pago) VALUES (?, ?, ?)",
            (new_serv_id, valor, int(pago))
        )

        conn.commit()
        st.success("Serviço registrado com sucesso!")

    # 7) Histórico imediato
    st.markdown("---")
    st.header("Histórico de Registros")
    rows = c.execute("""
        SELECT 
          f.id,
          p.nome      AS pet,
          s.descricao AS servico,
          s.lembrete_dias AS retorno,
          f.valor,
          f.pago
        FROM financeiro f
        JOIN servicos s ON f.servico_id = s.id
        JOIN pets    p ON s.pet_id      = p.id
        ORDER BY f.id DESC
    """).fetchall()

    if not rows:
        st.info("Nenhum registro encontrado.")
    else:
        tabela = []
        for r in rows:
            tabela.append({
                "ID":          r["id"],
                "Pet":         r["pet"],
                "Serviço":     r["servico"],
                "Retorno (d)": r["retorno"],
                "Valor (R$)":  f"{r['valor']:.2f}",
                "Pago":        "Sim" if r["pago"] else "Não"
            })
        st.table(tabela)
