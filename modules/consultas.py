import streamlit as st
from db import get_connection
from utils import parsear_data, formatar_data
from datetime import date

def page():
    st.title("Consultas & Edições")
    conn = get_connection()
    c = conn.cursor()

    tabs = st.tabs([
        "Pets",
        "Grupos",
        "Serviços",
        "Registros de Serviços"
    ])

    # --- Pets ---
    with tabs[0]:
        st.header("Editar Pet")
        pets = c.execute("SELECT id, nome FROM pets").fetchall()
        if not pets:
            st.info("Nenhum pet cadastrado.")
        else:
            pet_map = {r["id"]: r["nome"] for r in pets}
            sel_pet = st.selectbox(
                "Selecione Pet",
                list(pet_map.keys()),
                format_func=lambda x: pet_map[x],
                key="edit_pet_sel"
            )
            pet = c.execute("SELECT * FROM pets WHERE id=?", (sel_pet,)).fetchone()

            with st.form("edit_pet_form", clear_on_submit=True):
                ESPECIES = ["Cães","Gatos","Pássaros","Coelhos","Roedores Menores","Outros"]
                atual_especie = pet["especie"] if pet["especie"] in ESPECIES else "Cães"
                especie = st.selectbox(
                    "Espécie", ESPECIES,
                    index=ESPECIES.index(atual_especie),
                    key="edit_pet_especie"
                )
                nome = st.text_input("Nome do Pet", pet["nome"], key="edit_pet_nome")
                tutor = st.text_input("Nome do Tutor", pet["tutor"], key="edit_pet_tutor")
                telefone = st.text_input("Telefone do Tutor", pet["telefone"] or "", key="edit_pet_tel")
                email = st.text_input("Email do Tutor", pet["email"] or "", key="edit_pet_email")
                data_pet = st.text_input(
                    "Data de nascimento do pet (DD/MM/YYYY)",
                    formatar_data(pet["data_nasc_pet"]),
                    key="edit_pet_data_pet"
                )
                dm = (pet["data_nasc_tutor"] or "01/01").split("/")
                MONTHS = [
                    ("01","Jan"),("02","Fev"),("03","Mar"),("04","Abr"),
                    ("05","Mai"),("06","Jun"),("07","Jul"),("08","Ago"),
                    ("09","Set"),("10","Out"),("11","Nov"),("12","Dez")
                ]
                month_idx = next((i for i,(code,_) in enumerate(MONTHS) if code==dm[0]), 0)
                month = st.selectbox(
                    "Mês aniversário tutor", MONTHS,
                    index=month_idx,
                    format_func=lambda x: x[1],
                    key="edit_pet_month"
                )
                day = st.number_input(
                    "Dia aniversário tutor", 1, 31,
                    value=int(dm[1]) if dm[1].isdigit() else 1,
                    key="edit_pet_day"
                )
                raca = st.text_input("Raça", pet["raca"] or "", key="edit_pet_raca")
                PORTES = ["MICRO","PEQUENO","MÉDIO","GRANDE","GIGANTE"]
                p_idx = PORTES.index(pet["porte"]) if pet["porte"] in PORTES else 0
                porte = st.selectbox("Porte", PORTES, index=p_idx, key="edit_pet_porte")
                peso = st.number_input(
                    "Peso (kg)", min_value=0.0,
                    value=float(pet["peso"] or 0.0),
                    format="%.2f",
                    key="edit_pet_peso"
                )
                AUT = ["SIM","NAO"]
                a_idx = AUT.index(pet["autorizacao_imagem"]) if pet["autorizacao_imagem"] in AUT else 1
                autorizacao = st.selectbox("Autorização de imagem", AUT, index=a_idx, key="edit_pet_aut")
                PELE = ["Curto","Médio","Longo","Arame"]
                pel_idx = PELE.index(pet["tipo_pelagem"]) if pet["tipo_pelagem"] in PELE else 0
                pelagem = st.selectbox("Tipo de pelagem", PELE, index=pel_idx, key="edit_pet_pelagem")
                AG = ["Sim","Nao"]
                ag_idx = AG.index(pet["agressividade"]) if pet["agressividade"] in AG else 1
                agressividade = st.selectbox("Agressividade", AG, index=ag_idx, key="edit_pet_agress")
                MS = ["SIM","NAO"]
                mens_val = pet["mensalista"] or "NAO"
                mens_val = mens_val if mens_val in MS else "NAO"
                ms_idx = MS.index(mens_val)
                mensalista = st.selectbox("Mensalista", MS, index=ms_idx, key="edit_pet_mens")
                observacoes = st.text_area("Observações", pet["observacoes"] or "", key="edit_pet_obs")
                endereco = st.text_area("Endereço", pet["endereco"] or "", key="edit_pet_end")

                # <-- sem key aqui -->
                if st.form_submit_button("Salvar"):
                    try:
                        iso = parsear_data(data_pet)
                    except:
                        st.error("Formato de data inválido")
                        st.stop()
                    tutor_str = f"{day:02d}/{month[0]}"
                    c.execute("""
                        UPDATE pets
                        SET especie=?,nome=?,tutor=?,telefone=?,email=?,
                            data_nasc_pet=?,data_nasc_tutor=?,raca=?,porte=?,peso=?,
                            autorizacao_imagem=?,tipo_pelagem=?,agressividade=?,mensalista=?,
                            observacoes=?,endereco=?
                        WHERE id=?
                    """, (
                        especie, nome, tutor, telefone, email,
                        iso, tutor_str, raca, porte, peso,
                        autorizacao, pelagem, agressividade, mensalista,
                        observacoes, endereco, sel_pet
                    ))
                    conn.commit()
                    st.success("Pet atualizado!")

            if st.button("Excluir Pet", key="edit_pet_delete"):
                c.execute("DELETE FROM pets WHERE id=?", (sel_pet,))
                conn.commit()
                st.success("Pet excluído")

    # --- Grupos ---
    with tabs[1]:
        st.header("Editar Grupo")
        grupos = c.execute("SELECT id, nome FROM grupos").fetchall()
        if not grupos:
            st.info("Nenhum grupo cadastrado.")
        else:
            grp_map = {r["id"]: r["nome"] for r in grupos}
            sel_grp = st.selectbox(
                "Selecione Grupo", list(grp_map.keys()),
                format_func=lambda x: grp_map[x],
                key="edit_grp_sel"
            )
            grp = c.execute("SELECT * FROM grupos WHERE id=?", (sel_grp,)).fetchone()

            with st.form("edit_grp_form", clear_on_submit=True):
                nomeg = st.text_input("Nome do Grupo", grp["nome"], key="edit_grp_nome")
                if st.form_submit_button("Salvar"):
                    c.execute("UPDATE grupos SET nome=? WHERE id=?", (nomeg, sel_grp))
                    conn.commit()
                    st.success("Grupo atualizado")
            if st.button("Excluir Grupo", key="edit_grp_delete"):
                c.execute("DELETE FROM grupos WHERE id=?", (sel_grp,))
                conn.commit()
                st.success("Grupo excluído")

# --- Serviços ---
    with tabs[2]:
        st.header("Serviços")
        # 1) Carrega todos os serviços
        rows = c.execute("""
            SELECT id, grupo, descricao, valor, data_servico
            FROM servicos
            ORDER BY grupo, descricao
        """).fetchall()

        if not rows:
            st.info("Nenhum serviço cadastrado.")
        else:
            # 2) Dropdown de seleção para editar
            svc_map = {
                r["id"]: f"{r['descricao']} (R$ {r['valor']:.2f})"
                for r in rows
            }
            sel_svc = st.selectbox(
                "Selecione Serviço",
                list(svc_map.keys()),
                format_func=lambda x: svc_map[x],
                key="edit_svc_sel"
            )
            svc = c.execute("SELECT * FROM servicos WHERE id=?", (sel_svc,)).fetchone()

            # 3) Formulário de edição
            with st.form("edit_svc_form", clear_on_submit=True):
                grupos = [g["nome"] for g in c.execute("SELECT nome FROM grupos").fetchall()]
                grp_idx = grupos.index(svc["grupo"]) if svc["grupo"] in grupos else 0
                grp_sel = st.selectbox("Grupo", grupos, index=grp_idx, key="edit_svc_grp")
                desc    = st.text_input("Nome do Serviço", svc["descricao"] or "", key="edit_svc_desc")
                valor   = st.number_input(
                            "Valor (R$)",
                            min_value=0.0,
                            value=float(svc["valor"] or 0.0),
                            format="%.2f",
                            key="edit_svc_valor"
                         )
                data_str = formatar_data(svc["data_servico"])
                data_serv = st.text_input("Data de Cadastro (DD/MM/YYYY)", data_str, key="edit_svc_date")

                if st.form_submit_button("Salvar"):
                    try:
                        iso = parsear_data(data_serv)
                    except:
                        st.error("Formato de data inválido (use DD/MM/YYYY).")
                        st.stop()
                    c.execute("""
                        UPDATE servicos
                          SET grupo=?, descricao=?, valor=?, data_servico=?
                        WHERE id=?
                    """, (grupos[grp_sel], desc.strip(), valor, iso, sel_svc))
                    conn.commit()
                    st.success("Serviço atualizado!")

            # 4) Botão de exclusão
            if st.button("Excluir Serviço", key="edit_svc_delete"):
                c.execute("DELETE FROM servicos WHERE id=?", (sel_svc,))
                conn.commit()
                st.success("Serviço excluído")

            # ────────────────────────────────────────
            # 5) Agora exibimos a tabela **abaixo** do formulário
            st.markdown("---")
            st.subheader("Serviços Cadastrados")
            tabela = []
            for r in rows:
                tabela.append({
                    "ID":               r["id"],
                    "Grupo":            r["grupo"],
                    "Serviço":          r["descricao"],
                    "Valor (R$)":       f"{r['valor']:.2f}",
                    "Data de Cadastro": formatar_data(r["data_servico"])
                })
            st.table(tabela)

#  Registros de Serviços 
    with tabs[3]:
        st.header("Registros de Serviços")

        # 1) Filtro por grupo
        grupos = [r["grupo"] for r in c.execute("SELECT DISTINCT grupo FROM servicos").fetchall()]
        grupo_sel = st.selectbox("Filtrar por Grupo", grupos, key="filtro_reg_grp")

        # 2) Busca só registros deste grupo
        rows = c.execute("""
            SELECT 
              f.id,
              p.nome           AS pet,
              s.grupo          AS grupo,
              s.descricao      AS servico,
              s.data_servico   AS data,
              s.lembrete_dias  AS retorno,
              f.valor,
              f.pago
            FROM financeiro f
            JOIN servicos s ON f.servico_id = s.id
            JOIN pets    p ON s.pet_id      = p.id
            WHERE s.grupo = ?
            ORDER BY f.id DESC
        """, (grupo_sel,)).fetchall()

        if not rows:
            st.info(f"Não há registros em “{grupo_sel}”.")
        else:
            opts = {
                r["id"]: f'{formatar_data(r["data"])} – {r["pet"]} – {r["servico"]}'
                for r in rows
            }
            sel = st.selectbox("Selecione registro", list(opts), format_func=lambda x: opts[x], key="edit_rec_sel")
            rec = next(r for r in rows if r["id"] == sel)

            with st.form("edit_rec_form", clear_on_submit=True):
                st.markdown(f"**Pet:** {rec['pet']}")
                st.markdown(f"**Serviço:** {rec['servico']}")
                data_str = formatar_data(rec["data"])
                new_data = st.text_input("Data (DD/MM/YYYY)", data_str, key="edit_rec_data")
                new_ret  = st.number_input("Dias de Retorno", min_value=0, value=rec["retorno"], key="edit_rec_retorno")
                new_val  = st.number_input("Valor (R$)", min_value=0.0, value=rec["valor"], format="%.2f", key="edit_rec_valor")
                pago_idx = 1 if rec["pago"] else 0
                new_pago = st.selectbox("Pago", ["Não","Sim"], index=pago_idx, key="edit_rec_pago")

                if st.form_submit_button("Salvar"):
                    iso = parsear_data(new_data)
                    c.execute("UPDATE servicos   SET data_servico=?, lembrete_dias=? WHERE id=?", (iso, new_ret, sel))
                    c.execute("UPDATE financeiro SET valor=?, pago=?         WHERE id=?", (new_val, 1 if new_pago=="Sim" else 0, sel))
                    conn.commit()
                    st.success("Registro atualizado!")

            if st.button("Excluir Registro", key="edit_rec_delete"):
                c.execute("DELETE FROM financeiro WHERE id=?", (sel,))
                c.execute("DELETE FROM servicos   WHERE id=?", (sel,))
                conn.commit()
                st.success("Registro excluído!")