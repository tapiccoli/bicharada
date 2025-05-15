import streamlit as st
import sqlite3
from datetime import datetime, timedelta

# Banco de dados
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

# Criação da tabela de grupos de serviços
c.execute('''CREATE TABLE IF NOT EXISTS grupos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE
)''')

# Insere grupos padrão se a tabela estiver vazia
if not c.execute("SELECT 1 FROM grupos LIMIT 1").fetchone():
    grupos_padrao = ["SANITÁRIO", "BANHO", "SAÚDE", "TRANSPORTE", "TOSA"]
    for grupo in grupos_padrao:
        c.execute("INSERT OR IGNORE INTO grupos (nome) VALUES (?)", (grupo,))
    conn.commit()

# Corrige bancos antigos que ainda não têm a coluna 'grupo' em servicos
try:
    c.execute("ALTER TABLE servicos ADD COLUMN grupo TEXT")
except sqlite3.OperationalError:
    pass
try:
    c.execute("ALTER TABLE servicos ADD COLUMN retorno_personalizado_id INTEGER")
except sqlite3.OperationalError:
    pass

# Corrige bancos antigos que ainda não têm a coluna 'peso'
try:
    c.execute("ALTER TABLE pets ADD COLUMN peso REAL")
except sqlite3.OperationalError:
    pass
try:
    c.execute("ALTER TABLE pets ADD COLUMN nascimento_pet DATE")
except sqlite3.OperationalError:
    pass
try:
    c.execute("ALTER TABLE pets ADD COLUMN nascimento_tutor DATE")
except sqlite3.OperationalError:
    pass
try:
    c.execute("ALTER TABLE pets ADD COLUMN autorizacao_imagem TEXT")
except sqlite3.OperationalError:
    pass
try:
    c.execute("ALTER TABLE pets ADD COLUMN tipo_pelagem TEXT")
except sqlite3.OperationalError:
    pass
try:
    c.execute("ALTER TABLE pets ADD COLUMN mensalista INTEGER")
except sqlite3.OperationalError:
    pass
try:
    c.execute("ALTER TABLE pets ADD COLUMN observacoes TEXT")
except sqlite3.OperationalError:
    pass

conn.commit()

st.title("Sistema de Agendamento e Rotinas para Petshop")

with st.sidebar:
    st.header("Menu")
    menu = st.radio("", ["Cadastro de Pet", "Cadastro de Serviço", "Grupos de Serviços", "Registro de Serviço", "Agendamento", "Hoje", "Lembretes", "Consulta e Edição", "Transporte"])

if menu == "Cadastro de Pet":
    st.header("Cadastrar novo pet")
    nome = st.text_input("Nome do pet")
    tutor = st.text_input("Nome do tutor")
    nascimento_pet = st.date_input("Data de nascimento do pet", format="DD/MM/YYYY")
    nascimento_tutor = st.date_input("Data de nascimento do tutor", format="DD/MM/YYYY")
    raca = st.text_input("Raça")
    porte = st.selectbox("Porte", ["Pequeno", "Médio", "Grande"])
    peso = st.number_input("Peso (kg)", min_value=0.0, step=0.1)
    autorizacao_imagem = st.radio("Autorização de uso de imagem", ["Sim", "Não"])
    tipo_pelagem = st.selectbox("Tipo de pelagem", ["Curto", "Comprido", "Pelo de arame"])
    mensalista = st.checkbox("É mensalista?")
    observacoes = st.text_area("Observações")
    if st.button("Salvar"):
        c.execute("""
            INSERT INTO pets (nome, tutor, raca, porte, peso, nascimento_pet, nascimento_tutor, autorizacao_imagem, tipo_pelagem, mensalista, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (nome, tutor, raca, porte, peso, nascimento_pet, nascimento_tutor, autorizacao_imagem, tipo_pelagem, int(mensalista), observacoes))
        conn.commit()
        st.success("Pet cadastrado com sucesso!")

elif menu == "Grupos de Serviços":
    st.header("Gerenciar grupos de serviços")
    grupos = c.execute("SELECT id, nome FROM grupos ORDER BY nome").fetchall()
    st.subheader("Grupos existentes")
    for grupo in grupos:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text(grupo[1])
        with col2:
            if st.button("Excluir", key=f"del_grupo_{grupo[0]}"):
                c.execute("DELETE FROM grupos WHERE id = ?", (grupo[0],))
                c.execute("UPDATE servicos SET grupo = NULL WHERE grupo = ?", (grupo[1],))
                conn.commit()
                st.warning(f"Grupo '{grupo[1]}' removido e desvinculado dos serviços.")
    novo_grupo = st.text_input("Adicionar novo grupo de serviço")
    if st.button("Adicionar grupo") and novo_grupo:
        try:
            c.execute("INSERT INTO grupos (nome) VALUES (?)", (novo_grupo.strip(),))
            conn.commit()
            st.success(f"Grupo '{novo_grupo}' adicionado com sucesso!")
            st.rerun()
        except sqlite3.IntegrityError:
            st.error("Esse grupo já existe.")

elif menu == "Cadastro de Serviço":
    st.header("Cadastrar novo serviço de rotina")
    nome_servico = st.text_input("Nome do serviço")
    grupos_existentes = [g[0] for g in c.execute("SELECT nome FROM grupos ORDER BY nome").fetchall()]
    grupo = st.selectbox("Grupo do serviço", sorted(grupos_existentes) if grupos_existentes else ["Nenhum grupo disponível"])
    intervalo = st.number_input("Intervalo em dias para repetição (coloque 0 para serviços que não se repetem)", min_value=0)
    retorno_id = None
    servicos_disponiveis = c.execute("SELECT id, nome FROM servicos WHERE grupo = 'SAÚDE'").fetchall()
    if grupo == "SAÚDE":
        servicos_do_grupo = c.execute("SELECT id, nome FROM servicos WHERE grupo = ? ORDER BY nome", (grupo,)).fetchall()
        
        nomes_servicos = [s[1] for s in servicos_do_grupo if s[1] != nome_servico]
        if nomes_servicos:
            retorno_nome = st.selectbox("Próximo serviço na sequência (ex: vacina de 10 semanas)", ["Nenhum"] + nomes_servicos)
            if retorno_nome != "Nenhum":
                retorno_id = [s[0] for s in servicos_do_grupo if s[1] == retorno_nome][0]
    if st.button("Salvar serviço"):
        c.execute("INSERT INTO servicos (nome, intervalo_dias, grupo, retorno_personalizado_id) VALUES (?, NULLIF(?, 0), ?, ?)", (nome_servico, intervalo, grupo, retorno_id))
        conn.commit()
        st.success("Serviço cadastrado!")

elif menu == "Registro de Serviço":
    st.header("Registrar serviço realizado")
    pets = c.execute("SELECT id, nome FROM pets").fetchall()
    if pets:
        pet = st.selectbox("Selecione o pet", pets, format_func=lambda x: x[1])
        grupos_existentes = [g[0] for g in c.execute("SELECT nome FROM grupos ORDER BY nome").fetchall()]
        grupo_selecionado = st.selectbox("Selecione o grupo de serviço", grupos_existentes if grupos_existentes else ["Nenhum grupo disponível"])
        servicos = c.execute("SELECT id, nome FROM servicos WHERE grupo = ?", (grupo_selecionado,)).fetchall()
        if servicos:
            servico = st.selectbox("Serviço realizado", servicos, format_func=lambda x: x[1])
            data_realizacao = st.date_input("Data de realização", datetime.today(), format="DD/MM/YYYY")
            repetir = st.checkbox("Repetir este serviço?")
            dias_retorno = None
            if repetir:
                dias_retorno = st.number_input("Número de dias para repetir este serviço", min_value=1, step=1)
            if st.button("Registrar"):
                c.execute("INSERT INTO historico_servicos (pet_id, servico_id, data) VALUES (?, ?, ?)", (pet[0], servico[0], data_realizacao))
                conn.commit()
                st.success("Serviço registrado!")
                # Checar se tem retorno personalizado
                retorno_personalizado = c.execute("SELECT retorno_personalizado_id FROM servicos WHERE id = ?", (servico[0],)).fetchone()
                if retorno_personalizado and retorno_personalizado[0]:
                    dias = c.execute("SELECT intervalo_dias FROM servicos WHERE id = ?", (servico[0],)).fetchone()[0]
                    if dias:
                        data_retorno = data_realizacao + timedelta(days=dias)
                        c.execute("INSERT INTO agendamentos (pet_id, data) VALUES (?, ?)", (pet[0], data_retorno))
                        conn.commit()
                        nome_retorno = c.execute("SELECT nome FROM servicos WHERE id = ?", (retorno_personalizado[0],)).fetchone()[0]
                        st.info(f"Agendamento futuro: {nome_retorno} em {data_retorno.strftime('%d/%m/%Y')}")
                if repetir and dias_retorno:
                    proxima_data = data_realizacao + timedelta(days=int(dias_retorno))
                    c.execute("INSERT INTO agendamentos (pet_id, data) VALUES (?, ?)", (pet[0], proxima_data))
                    conn.commit()
                    st.info(f"Próxima repetição agendada para {proxima_data.strftime('%d/%m/%Y')}")
        else:
            st.warning("Não há serviços cadastrados neste grupo.")
    else:
        st.warning("Cadastre ao menos um pet antes de registrar.")

elif menu == "Agendamento":
    st.header("Agendar banho ou serviço")
    pets = c.execute("SELECT id, nome FROM pets").fetchall()
    if pets:
        pet = st.selectbox("Selecione o pet para agendamento", pets, format_func=lambda x: x[1])
        data_agendamento = st.date_input("Data do agendamento", datetime.today(), format="DD/MM/YYYY")
        if st.button("Agendar"):
            c.execute("INSERT INTO agendamentos (pet_id, data) VALUES (?, ?)", (pet[0], data_agendamento))
            conn.commit()
            st.success("Agendamento salvo!")
    else:
        st.warning("Cadastre pets antes de agendar.")

elif menu == "Lembretes":
    st.header("Lembretes de serviços vencidos para pets NÃO agendados")
    hoje = datetime.today().date()

    servicos_disponiveis = c.execute("SELECT id, nome FROM servicos").fetchall()
    servico_escolhido = st.selectbox("Selecione o serviço para verificar pendências", servicos_disponiveis, format_func=lambda x: x[1])

    if servico_escolhido:
        servico_id = servico_escolhido[0]
        nome_servico = servico_escolhido[1]
        intervalo_dias = c.execute("SELECT intervalo_dias FROM servicos WHERE id = ?", (servico_id,)).fetchone()[0]

        pets = c.execute("SELECT id, nome FROM pets").fetchall()
        agendados_hoje_ids = [r[0] for r in c.execute("SELECT pet_id FROM agendamentos WHERE data = ?", (hoje,)).fetchall()]

        vencimentos = []

        for pet in pets:
            if pet[0] not in agendados_hoje_ids:
                ultimo = c.execute("SELECT MAX(data) FROM historico_servicos WHERE pet_id = ? AND servico_id = ?", (pet[0], servico_id)).fetchone()[0]
                if ultimo:
                    ultimo_data = datetime.strptime(ultimo, "%Y-%m-%d").date()
                    dias_passados = (hoje - ultimo_data).days
                    atraso = dias_passados - intervalo_dias
                    if atraso > 0:
                        vencimentos.append((pet[1], atraso))

        if vencimentos:
            vencimentos.sort(key=lambda x: x[1], reverse=True)
            for nome_pet, dias in vencimentos:
                if dias >= 7:
                    st.error(f"🐶 {nome_pet} - {nome_servico} ({dias} dias de atraso)")
                elif dias >= 3:
                    st.warning(f"🐶 {nome_pet} - {nome_servico} ({dias} dias de atraso)")
                else:
                    st.info(f"🐶 {nome_pet} - {nome_servico} ({dias} dias de atraso)")
        else:
            st.success("Nenhum pet está com este serviço vencido sem estar agendado.")

elif menu == "Hoje":
    st.header("Agenda de hoje com rotinas sugeridas")
    hoje = datetime.today().date()
    agendados = c.execute("SELECT a.id, p.nome, p.id FROM agendamentos a JOIN pets p ON a.pet_id = p.id WHERE a.data = ?", (hoje,)).fetchall()
    servicos = c.execute("SELECT id, nome, intervalo_dias FROM servicos").fetchall()
    if agendados:
        for ag in agendados:
            st.subheader(f"🐶 {ag[1]}")
            texto_rotinas = []
            for serv in servicos:
                ultimo = c.execute("SELECT MAX(data) FROM historico_servicos WHERE pet_id = ? AND servico_id = ?", (ag[2], serv[0])).fetchone()[0]
                if ultimo:
                    ultimo_data = datetime.strptime(ultimo, "%Y-%m-%d").date()
                    dias_passados = (hoje - ultimo_data).days
                    if dias_passados >= serv[2]:
                        texto_rotinas.append(f"{serv[1]} ({dias_passados - serv[2]} dias)")
            if texto_rotinas:
                st.warning("\n".join(texto_rotinas))
            else:
                st.info("Nenhuma rotina pendente para hoje.")
    else:
        st.success("Nenhum pet agendado para hoje.")

elif menu == "Transporte":
    st.header("Cadastro de transporte")
    c.execute("""CREATE TABLE IF NOT EXISTS transporte (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pet_id INTEGER,
        endereco TEXT,
        distancia_km REAL,
        preco REAL,
        data_registro TEXT
    )""")
    conn.commit()

    pets = c.execute("SELECT id, nome, tutor FROM pets").fetchall()
    if pets:
        pet = st.selectbox("Selecione o pet para transporte", pets, format_func=lambda x: f"{x[1]} ({x[2]})")
        endereco = st.text_input("Endereço de busca ou entrega")
        if st.button("Calcular distância e preço"):
            endereco_petshop = "Rua Demétrio Moreira da Luz, 1251, Caxias do Sul - RS"
            base_url = "https://www.google.com/maps/dir/"
            import urllib.parse
            endereco_petshop_encoded = urllib.parse.quote(endereco_petshop)
            endereco_encoded = urllib.parse.quote(endereco)
            url = f"{base_url}{endereco_petshop_encoded}/{endereco_encoded}"
            st.markdown(f"[Abrir rota no Google Maps]({url})")
            st.info("Copie a distância (em km) mostrada no Google Maps e insira abaixo.")

        distancia = st.number_input("Distância em km (copiada do Google Maps)", min_value=0.0, step=0.1)
        preco = distancia * 1.30
        st.write(f"💰 Preço estimado: R$ {preco:.2f}")

        if st.button("Salvar transporte") and endereco:
            hoje = datetime.today().strftime("%Y-%m-%d")
            c.execute("INSERT INTO transporte (pet_id, endereco, distancia_km, preco, data_registro) VALUES (?, ?, ?, ?, ?)",
                      (pet[0], endereco, distancia, preco, hoje))
            conn.commit()
            st.success("Transporte registrado com sucesso!")

        st.subheader("Registros de Transporte")
        registros = c.execute("""
            SELECT t.data_registro, p.nome, t.endereco, t.distancia_km, t.preco
            FROM transporte t
            JOIN pets p ON t.pet_id = p.id
            ORDER BY t.data_registro DESC
        """).fetchall()
        if registros:
            for reg in registros:
                st.markdown(
    f"**🐾 {reg[1]}** - {reg[0]}  \n"
    f"📍 {reg[2]}  \n"
    f"📏 {reg[3]:.1f} km - 💰 R$ {reg[4]:.2f}"
)


                st.markdown("---")
    else:
        st.warning("Cadastre pets antes de usar transporte.")

elif menu == "Consulta e Edição":
    st.header("Consultar e editar registros")
    tab = st.radio("Escolha", ["Pets", "Serviços", "Agendamentos", "Histórico de Serviços"])

    if tab == "Pets":
        pets = c.execute("SELECT id, nome FROM pets").fetchall()
        if pets:
            pet = st.selectbox("Selecione o pet", pets, format_func=lambda x: x[1])
            dados = c.execute("SELECT nome, tutor, raca, porte, peso, nascimento_pet, nascimento_tutor, autorizacao_imagem, tipo_pelagem, mensalista, observacoes FROM pets WHERE id = ?", (pet[0],)).fetchone()
            nome_edit = st.text_input("Nome", value=dados[0])
            tutor_edit = st.text_input("Tutor", value=dados[1])
            raca_edit = st.text_input("Raça", value=dados[2])
            porte_edit = st.selectbox("Porte", ["Pequeno", "Médio", "Grande"], index=["Pequeno", "Médio", "Grande"].index(dados[3]))
            peso_edit = st.number_input("Peso (kg)", min_value=0.0, step=0.1, value=dados[4])
            nascimento_pet_edit = st.date_input("Data de nascimento do pet", value=datetime.strptime(dados[5], "%Y-%m-%d"), format="DD/MM/YYYY")
            nascimento_tutor_edit = st.date_input("Data de nascimento do tutor", value=datetime.strptime(dados[6], "%Y-%m-%d"), format="DD/MM/YYYY")
            autorizacao_edit = st.radio("Autorização de uso de imagem", ["Sim", "Não"], index=["Sim", "Não"].index(dados[7]))
            pelagem_edit = st.selectbox("Tipo de pelagem", ["Curto", "Comprido", "Pelo de arame"], index=["Curto", "Comprido", "Pelo de arame"].index(dados[8]))
            mensalista_edit = st.checkbox("É mensalista?", value=bool(dados[9]))
            observacoes_edit = st.text_area("Observações", value=dados[10])
            if st.button("Salvar alterações"):
                c.execute("""
                    UPDATE pets
                    SET nome = ?, tutor = ?, raca = ?, porte = ?, peso = ?, nascimento_pet = ?, nascimento_tutor = ?, autorizacao_imagem = ?, tipo_pelagem = ?, mensalista = ?, observacoes = ?
                    WHERE id = ?
                """, (nome_edit, tutor_edit, raca_edit, porte_edit, peso_edit, nascimento_pet_edit, nascimento_tutor_edit, autorizacao_edit, pelagem_edit, int(mensalista_edit), observacoes_edit, pet[0]))
                conn.commit()
                st.success("Pet atualizado com sucesso!")
                

    elif tab == "Serviços":
        grupos_existentes = [g[0] for g in c.execute("SELECT nome FROM grupos ORDER BY nome").fetchall()]
        grupo_filtro = st.selectbox("Selecione o grupo de serviço", grupos_existentes if grupos_existentes else ["Nenhum grupo disponível"])
        servicos = c.execute("SELECT id, nome FROM servicos WHERE grupo = ?", (grupo_filtro,)).fetchall()
        if servicos:
            serv = st.selectbox("Selecione o serviço", servicos, format_func=lambda x: x[1])
            dados = c.execute("SELECT nome, intervalo_dias, grupo FROM servicos WHERE id = ?", (serv[0],)).fetchone()
            nome_edit = st.text_input("Nome do serviço", value=dados[0])
            intervalo_edit = st.number_input("Intervalo (dias)", min_value=1, value=dados[1])
            grupo_edit = st.selectbox("Grupo do serviço", grupos_existentes if grupos_existentes else ["Nenhum grupo disponível"], index=grupos_existentes.index(dados[2]) if dados[2] in grupos_existentes else 0)
            if st.button("Salvar alterações"):
                c.execute("UPDATE servicos SET nome = ?, intervalo_dias = ?, grupo = ? WHERE id = ?", (nome_edit, intervalo_edit, grupo_edit, serv[0]))
                conn.commit()
                st.success("Serviço atualizado com sucesso!")

    elif tab == "Agendamentos":
        ags = c.execute("SELECT a.id, p.nome, a.data FROM agendamentos a JOIN pets p ON a.pet_id = p.id ORDER BY a.data DESC").fetchall()
        if ags:
            ag = st.selectbox("Selecione o agendamento", ags, format_func=lambda x: f"{x[1]} em {datetime.strptime(x[2], '%Y-%m-%d').strftime('%d/%m/%Y')}")
            pets = c.execute("SELECT id, nome FROM pets").fetchall()
            pet_id_original = c.execute("SELECT pet_id FROM agendamentos WHERE id = ?", (ag[0],)).fetchone()[0]
            pet_edit = st.selectbox("Pet", pets, format_func=lambda x: x[1], index=[p[0] for p in pets].index(pet_id_original))
            data_edit = st.date_input("Data do agendamento", value=datetime.strptime(ag[2], "%Y-%m-%d"), format="DD/MM/YYYY")
            if st.button("Salvar alterações do agendamento"):
                c.execute("UPDATE agendamentos SET pet_id = ?, data = ? WHERE id = ?", (pet_edit[0], data_edit, ag[0]))
                conn.commit()
                st.success("Agendamento atualizado com sucesso!")
            if st.checkbox("Deseja realmente excluir este agendamento?"):
                if st.button("Confirmar exclusão"):
                    c.execute("DELETE FROM agendamentos WHERE id = ?", (ag[0],))
                    conn.commit()
                    st.warning("Agendamento excluído com sucesso!")

    elif tab == "Histórico de Serviços":
        pets_disponiveis = c.execute("SELECT id, nome FROM pets").fetchall()
        if pets_disponiveis:
            pet_selecionado = st.selectbox("Selecione o pet para filtrar os registros", pets_disponiveis, format_func=lambda x: x[1])
            registros = c.execute("""
                SELECT h.id, p.nome, s.nome, h.data
                FROM historico_servicos h
                JOIN pets p ON h.pet_id = p.id
                JOIN servicos s ON h.servico_id = s.id
                WHERE h.pet_id = ?
                ORDER BY h.data DESC
            """, (pet_selecionado[0],)).fetchall()
            if registros:
                reg = st.selectbox("Selecione o registro de serviço", registros, format_func=lambda x: f"{x[1]} - {x[2]} em {datetime.strptime(x[3], '%Y-%m-%d').strftime('%d/%m/%y')}")
            pets = c.execute("SELECT id, nome FROM pets").fetchall()
            servicos = c.execute("SELECT id, nome FROM servicos").fetchall()
            pet_id = c.execute("SELECT pet_id FROM historico_servicos WHERE id = ?", (reg[0],)).fetchone()[0]
            pet_edit = st.selectbox("Pet", pets, format_func=lambda x: x[1], index=[p[0] for p in pets].index(pet_id))
            servico_id = c.execute("SELECT servico_id FROM historico_servicos WHERE id = ?", (reg[0],)).fetchone()[0]
            servico_edit = st.selectbox("Serviço", servicos, format_func=lambda x: x[1], index=[s[0] for s in servicos].index(servico_id))
            data_edit = st.date_input("Data de realização", value=datetime.strptime(reg[3], "%Y-%m-%d"), format="DD/MM/YYYY")
            if st.button("Salvar alterações do serviço"):
                c.execute("UPDATE historico_servicos SET pet_id = ?, servico_id = ?, data = ? WHERE id = ?", (pet_edit[0], servico_edit[0], data_edit, reg[0]))
                conn.commit()
                st.success("Registro de serviço atualizado com sucesso!")
            if st.checkbox("Deseja realmente excluir este registro de serviço?"):
                if st.button("Confirmar exclusão"):
                    c.execute("DELETE FROM historico_servicos WHERE id = ?", (reg[0],))
                    conn.commit()
                    st.warning("Registro de serviço excluído com sucesso!")
