import streamlit as st
from db import get_connection
from utils import parsear_data, formatar_data
from datetime import date

def page():
    st.title("Cadastro de Pets")
    conn = get_connection(); c = conn.cursor()

    # Lista
    with st.expander("Ver Pets Cadastrados"):
        rows = c.execute("SELECT * FROM pets").fetchall()
        if rows:
            data = []
            for r in rows:
                row = dict(r)
                row["data_nasc_pet"] = formatar_data(row["data_nasc_pet"])
                row["data_nasc_tutor"] = row["data_nasc_tutor"]
                data.append(row)
            st.table(data)
        else:
            st.info("Nenhum pet cadastrado.")

    # Adicionar
    with st.form("add_pet", clear_on_submit=True):
        especie = st.selectbox("Espécie", ["Cães","Gatos","Pássaros","Coelhos","Roedores Menores","Outros"], index=0)
        nome = st.text_input("Nome do Pet")
        tutor = st.text_input("Nome do Tutor")
        telefone = st.text_input("Telefone do Tutor")
        email = st.text_input("Email do Tutor")
        data_nasc_pet = st.text_input("Data de nascimento do pet (DD/MM/YYYY)")
        months = [("01","Jan"),("02","Fev"),("03","Mar"),("04","Abr"),("05","Mai"),("06","Jun"),
                  ("07","Jul"),("08","Ago"),("09","Set"),("10","Out"),("11","Nov"),("12","Dez")]
        month = st.selectbox("Mês aniversário tutor", months, format_func=lambda x:x[1])
        day = st.number_input("Dia aniversário tutor",1,31,1)
        raca = st.text_input("Raça")
        porte = st.selectbox("Porte", ["MICRO","PEQUENO","MÉDIO","GRANDE","GIGANTE"])
        peso = st.number_input("Peso (kg)",0.0,1000.0,format="%.2f")
        autorizacao = st.selectbox("Autorização de imagem",["SIM","NAO"])
        pelagem = st.selectbox("Tipo de pelagem",["Curto","Médio","Longo","Arame"])
        agressividade = st.selectbox("Agressividade",["Sim","Nao"])
        mensalista = st.selectbox("Mensalista",["SIM","NAO"])
        observacoes = st.text_area("Observações")
        endereco = st.text_area("Endereço")
        if st.form_submit_button("Adicionar Pet"):
            try: iso = parsear_data(data_nasc_pet)
            except: st.error("Data inválida"); st.stop()
            tutor_str = f"{day:02d}/{month[0]}"
            c.execute("INSERT INTO pets (especie,nome,tutor,telefone,email,data_nasc_pet,data_nasc_tutor,raca,porte,peso,autorizacao_imagem,tipo_pelagem,agressividade,mensalista,observacoes,endereco) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (especie,nome,tutor,telefone,email,iso,tutor_str,raca,porte,peso,autorizacao,pelagem,agressividade,mensalista,observacoes,endereco))
            conn.commit(); st.success("Pet adicionado")

    # Edit/Delete
    pets = c.execute("SELECT id,nome FROM pets").fetchall()
    if pets:
        choices = {r["id"]:r["nome"] for r in pets}
        sel = st.selectbox("Editar/Excluir Pet", list(choices.keys()), format_func=lambda x:choices[x])
        pet = c.execute("SELECT * FROM pets WHERE id=?", (sel,)).fetchone()
        with st.form("edit_pet"):
            nome2 = st.text_input("Nome do Pet", pet["nome"])
            tutor2 = st.text_input("Nome do Tutor", pet["tutor"])
            data2 = st.text_input("Nascimento pet (DD/MM/YYYY)", formatar_data(pet["data_nasc_pet"]))
            # keep rest fields simplified...
            if st.form_submit_button("Salvar"):
                try: iso2 = parsear_data(data2)
                except: st.error("Data inválida"); st.stop()
                c.execute("UPDATE pets SET nome=?,tutor=?,data_nasc_pet=? WHERE id=?", (nome2,tutor2,iso2,sel))
                conn.commit(); st.success("Atualizado")
        if st.button("Excluir Pet"):
            c.execute("DELETE FROM pets WHERE id=?", (sel,))
            conn.commit(); st.success("Excluído")
