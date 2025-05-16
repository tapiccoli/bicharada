
import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import pandas as pd
import io
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

# Banco de dados
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()


# Criação da tabela de serviços
c.execute('''
CREATE TABLE IF NOT EXISTS servicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    intervalo_dias INTEGER,
    grupo TEXT,
    retorno_personalizado_id INTEGER
)''')

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
# — Criação das demais tabelas necessárias —
c.execute('''CREATE TABLE IF NOT EXISTS pets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    tutor TEXT,
    telefone TEXT,
    email TEXT,
    raca TEXT,
    porte TEXT,
    peso REAL,
    nascimento_pet DATE,
    nascimento_tutor DATE,
    autorizacao_imagem TEXT,
    tipo_pelagem TEXT,
    mensalista INTEGER,
    observacoes TEXT,
    endereco TEXT
)''' )
c.execute('''CREATE TABLE IF NOT EXISTS historico_servicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pet_id INTEGER,
    servico_id INTEGER,
    data DATE
)''' )
c.execute('''CREATE TABLE IF NOT EXISTS agendamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pet_id INTEGER,
    data DATE
)''' )
c.execute('''CREATE TABLE IF NOT EXISTS transporte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pet_id INTEGER,
    endereco TEXT,
    distancia_km REAL,
    preco REAL,
    data_registro TEXT
)''' )
c.execute('''CREATE TABLE IF NOT EXISTS transporte_compartilhado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endereco TEXT,
    distancia_km REAL,
    preco REAL,
    data_registro TEXT
)''' )
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


conn.commit()

# ——— Migração: adiciona coluna 'servicos' em agendamentos ———
try:
    c.execute("ALTER TABLE agendamentos ADD COLUMN servicos TEXT")
except sqlite3.OperationalError:
    # coluna já existe
    pass
conn.commit()

st.title("Sistema Tia Debora")

with st.sidebar:
    st.header("Menu")
    menu = st.radio("", ["Cadastro de Pet", "Cadastro de Serviço", "Grupos de Serviços", "Registro de Serviço", "Agendamento", "Hoje", "Lembretes", "Consulta e Edição", "Transporte", "Ficha Individual"], key="menu_principal")

try:
    c.execute("ALTER TABLE pets ADD COLUMN email TEXT")
except sqlite3.OperationalError:
    pass


# --- Cadastro de Pet ---
if menu == "Cadastro de Pet":
    st.header("Cadastrar novo pet")
    nome = st.text_input("Nome do pet")
    tutor = st.text_input("Nome do tutor")
    telefone = st.text_input("Telefone do tutor", placeholder="(DDD) 999999999")
    email = st.text_input("Email do tutor")
    nascimento_pet = st.date_input("Data de nascimento do pet", format="DD/MM/YYYY")
    nascimento_tutor = st.date_input("Data de nascimento do tutor", format="DD/MM/YYYY")
    raca = st.text_input("Raça")
    porte = st.selectbox("Porte", ["Pequeno", "Médio", "Grande"])
    peso = st.number_input("Peso (kg)", min_value=0.0)
    autorizacao_imagem = st.radio("Autorização de uso de imagem", ["Sim", "Não"])
    tipo_pelagem = st.selectbox("Tipo de pelagem", ["Curto", "Comprido", "Pelo de arame"])
    mensalista = st.checkbox("É mensalista?")
    observacoes = st.text_area("Observações")
    endereco = st.text_input("Endereço")
    if st.button("Salvar"):
        c.execute(
            "INSERT INTO pets (nome, tutor, telefone, email, raca, porte, peso, nascimento_pet, nascimento_tutor, autorizacao_imagem, tipo_pelagem, mensalista, observacoes, endereco) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (nome, tutor, telefone, email, raca, porte, peso, nascimento_pet.isoformat(), nascimento_tutor.isoformat(), autorizacao_imagem, tipo_pelagem, int(mensalista), observacoes, endereco)
        )
        conn.commit()
        st.success("Pet cadastrado com sucesso!")

# --- Grupos de Serviços ---
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

# --- Cadastro de Serviços ---
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

# --- Registro de Serviços ---
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

# --- Agendamento ---
elif menu == "Agendamento":
    st.header("📅 Novo Agendamento")

    # 1) Escolha do pet e da data
    pets = c.execute("SELECT id, nome FROM pets ORDER BY nome").fetchall()
    pet_id, pet_nome = st.selectbox(
        "Pet",
        pets,
        format_func=lambda x: x[1],
        key="ag_pet"
    )
    data_ag = st.date_input("Data do agendamento", key="ag_data")

    # 2) Seleção múltipla de **grupos de serviço**
    grupos = [g[0] for g in c.execute("SELECT nome FROM grupos ORDER BY nome").fetchall()]
    grupos_selecionados = st.multiselect(
        "Grupos de serviços que serão realizados",
        grupos,
        key="ag_grupos"
    )

    # 3) Botão para salvar
    if st.button("Agendar", key="botao_agendar"):
        # converte lista de grupos em texto para gravar
        servs_str = "; ".join(grupos_selecionados)
        c.execute(
            "INSERT INTO agendamentos (pet_id, data, servicos) VALUES (?, ?, ?)",
            (pet_id, data_ag, servs_str)
        )
        conn.commit()
        st.success(f"Agendamento criado para **{pet_nome}** em **{data_ag}**.")

        # 4) Relatório rápido dos agendamentos atuais
        st.markdown("### 📋 Relatório de Agendamentos")
        ags = c.execute("""
            SELECT a.data, p.nome, a.servicos
              FROM agendamentos a
              JOIN pets p ON p.id = a.pet_id
             ORDER BY a.data DESC
        """).fetchall()
        for data_, pet_, grupos_ in ags:
            st.write(f"- **{data_}**  |  {pet_}  |  Grupos: {grupos_ or '–'}")

# --- Hoje ---
elif menu == "Hoje":
    from datetime import datetime

    st.header("⏰ Pendências de Hoje")

    # 1) Escolha do grupo
    grupos_existentes = [g[0] for g in c.execute("SELECT nome FROM grupos ORDER BY nome").fetchall()]
    grupo_escolhido = st.selectbox(
        "Selecione o grupo de serviço",
        grupos_existentes,
        key="hoje_grupo"
    )

    # 2) Carrega serviços e pets
    servicos_do_grupo = c.execute(
        "SELECT id, nome, intervalo_dias FROM servicos WHERE grupo = ?",
        (grupo_escolhido,)
    ).fetchall()
    pets_lista = c.execute(
        "SELECT id, nome FROM pets ORDER BY nome"
    ).fetchall()

    hoje = datetime.today().date()
    pendentes = []

    # 3) Para cada serviço e cada pet, verifica a última data
    for serv in servicos_do_grupo:
        serv_id, serv_nome, intervalo = serv
        # ignora serviços sem intervalo definido
        if intervalo is None:
            continue

        for pet in pets_lista:
            pet_id, pet_nome = pet

            # Busca a última data deste serviço para este pet
            ultima = c.execute(
                """
                SELECT MAX(data)
                  FROM historico_servicos
                 WHERE servico_id = ? AND pet_id = ?
                """,
                (serv_id, pet_id)
            ).fetchone()[0]

            if ultima:
                data_ultima = datetime.strptime(ultima, "%Y-%m-%d").date()
                dias_passados = (hoje - data_ultima).days
            else:
                # Se nunca foi feito, conta desde sempre
                dias_passados = None

            # Se já passou do intervalo, marca como pendente
            if dias_passados is not None and dias_passados >= intervalo:
                pendentes.append((pet_nome, serv_nome, dias_passados))

    # 4) Exibe resultados
    if pendentes:
        st.markdown("**Serviços pendentes:**")
        for pet_nome, serv_nome, dias in pendentes:
            st.write(f"- **{pet_nome}** → {serv_nome}: {dias} dias desde o último atendimento")
    else:
        st.success("Nenhum serviço pendente para hoje.")

# --- Transporte ---

# Inicialização da variável de transporte para controle de interface
if 'tipo_transporte' not in st.session_state:
    st.session_state['tipo_transporte'] = 'Exclusivo'

c.execute("""CREATE TABLE IF NOT EXISTS transporte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pet_id INTEGER,
    endereco TEXT,
    distancia_km REAL,
    preco REAL,
    data_registro TEXT
)""")
conn.commit()


# --- Criação e migração das tabelas ---
c.execute('''
CREATE TABLE IF NOT EXISTS historico_servicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pet_id INTEGER,
    servico_id INTEGER,
    data DATE
)''')

c.execute('''
CREATE TABLE IF NOT EXISTS agendamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pet_id INTEGER,
    data DATE
)''')
c.execute('''CREATE TABLE IF NOT EXISTS pets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    tutor TEXT,
    telefone TEXT,
    email TEXT,
    raca TEXT,
    porte TEXT,
    peso REAL,
    nascimento_pet DATE,
    nascimento_tutor DATE,
    autorizacao_imagem TEXT,
    tipo_pelagem TEXT,
    mensalista INTEGER,
    observacoes TEXT,
    endereco TEXT
)''')
c.execute("""CREATE TABLE IF NOT EXISTS transporte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pet_id INTEGER,
    endereco TEXT,
    distancia_km REAL,
    preco REAL,
    data_registro TEXT
)""")
c.execute("""CREATE TABLE IF NOT EXISTS transporte_compartilhado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endereco TEXT,
    distancia_km REAL,
    preco REAL,
    data_registro TEXT
)""")
conn.commit()


# --- Ficha Individual ---
if menu == "Ficha Individual":
    st.header("Ficha do Pet")
    pets = c.execute("SELECT id, nome, tutor FROM pets ORDER BY nome").fetchall()
    if pets:
        pet = st.selectbox("Selecione o pet", pets, format_func=lambda x: f"{x[1]} ({x[2]})")
        subtab = st.radio("Aba", ["Histórico", "Pagamentos Pendentes"])

        if subtab == "Histórico":
            st.subheader("📝 Histórico de Serviços e Transportes")
            historico_servicos = c.execute("""
                SELECT 'Serviço', s.nome, h.data
                FROM historico_servicos h
                JOIN servicos s ON h.servico_id = s.id
                WHERE h.pet_id = ?
                UNION
                SELECT 'Transporte', 'Transporte registrado', t.data_registro
                FROM transporte t
                WHERE t.pet_id = ?
                ORDER BY 3 DESC
            """, (pet[0], pet[0])).fetchall()

            for tipo, descricao, data in historico_servicos:
                st.markdown(f"📌 <b>{tipo}</b> — {descricao} <br><small>{datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m/%Y')}</small>", unsafe_allow_html=True)

            # Exportar histórico
            df_historico = pd.DataFrame(historico_servicos, columns=["Tipo", "Descrição", "Data"])
            colpdf, colexcel = st.columns(2)
            with colpdf:
                if st.button("📄 Exportar como PDF"):
                    buffer = io.BytesIO()
                    doc = SimpleDocTemplate(buffer, pagesize=letter)
                    elements = [Table([["Tipo", "Descrição", "Data"]] + df_historico.values.tolist())]
                    elements[0].setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.grey),
                        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                        ('ALIGN',(0,0),(-1,-1),'LEFT'),
                        ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0,0),(-1,0), 12),
                        ('BACKGROUND',(0,1),(-1,-1),colors.beige),
                        ('GRID', (0,0), (-1,-1), 1, colors.black),
                    ]))
                    doc.build(elements)
                    buffer.seek(0)
                    st.download_button("📥 Baixar PDF", buffer, file_name=f"historico_{pet[1].replace(' ', '_')}_{pet[2].replace(' ', '_')}.pdf")
            with colexcel:
                csv = df_historico.to_csv(index=False).encode('utf-8')
                st.download_button("📊 Baixar Excel", csv, file_name=f"historico_{pet[1].replace(' ', '_')}_{pet[2].replace(' ', '_')}.csv", mime="text/csv")
    elif subtab == "Pagamentos Pendentes":
            st.subheader("💸 Pagamentos Pendentes")
            pagamentos = c.execute("SELECT id, endereco, preco, data_registro FROM transporte WHERE pet_id = ? ORDER BY data_registro DESC", (pet[0],)).fetchall()
            agrupamento_pag = st.radio("Como deseja agrupar os pagamentos?", ["Por pet", "Por tutor"], horizontal=True)
            if agrupamento_pag == "Por tutor":
                tutor_map = dict(c.execute("SELECT id, tutor FROM pets"))
                pagamentos = [(tutor_map.get(pet[0], "Desconhecido"), end, preco, data) for transp_id, end, preco, data in pagamentos]
            else:
                pagamentos = [(pet[1], end, preco, data) for transp_id, end, preco, data in pagamentos]
            if pagamentos:
                for transp_id, end, preco, data in pagamentos:
                    cols = st.columns([5, 1])
                    with cols[0]:
                        st.markdown(f"📍 <b>Endereço:</b> {end}<br>💰 <b>Valor:</b> R$ {preco:.2f}<br>📅 <small>{datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m/%Y')}</small>", unsafe_allow_html=True)
                    with cols[1]:
                        if st.button("Marcar como pago", key=f"pago_{transp_id}"):
                            c.execute("UPDATE transporte SET preco = 0 WHERE id = ?", (transp_id,))
                            conn.commit()
                            st.experimental_rerun()
            else:
                st.info("Nenhum pagamento registrado para este pet.")
    else:
        st.warning("Nenhum pet cadastrado.")


elif menu == "Consulta e Edição":
    st.header("📋 Consulta e Edição")

    # Cria as 4 sub-abas
    consultas = st.tabs([
        "🐾 Pets",
        "🛠 Serviços",
        "📅 Agendamentos",
        "📜 Histórico de Serviços"
    ])

    # ----------------------- Pets -----------------------
    with consultas[0]:
        st.subheader("🖊 Editar / 🗑️ Excluir Pet")

        pets_lista = c.execute(
            "SELECT id, nome FROM pets ORDER BY nome"
        ).fetchall()
        if not pets_lista:
            st.warning("Nenhum pet cadastrado.")
        else:
            opções = {f"{p[1]} ({p[0]})": p[0] for p in pets_lista}
            escolha = st.selectbox("Selecione o pet", list(opções.keys()), key="edit_pet_select")
            pet_id = opções[escolha]

            # Carrega dados
            row = c.execute("""
                SELECT nome, tutor, telefone, email, raca, porte, peso,
                       nascimento_pet, nascimento_tutor, autorizacao_imagem,
                       tipo_pelagem, mensalista, observacoes, endereco
                  FROM pets WHERE id = ?
            """, (pet_id,)).fetchone()

            (nome, tutor, telefone, email, raca, porte, peso,
             nasc_pet, nasc_tut, auth_img, tipo_pel, mensalista,
             obs, endereco) = row

            # Campos editáveis
            novo_nome     = st.text_input("Nome", value=nome, key="edit_nome")
            novo_tutor    = st.text_input("Tutor", value=tutor, key="edit_tutor")
            novo_telefone = st.text_input("Telefone", value=telefone, key="edit_telefone")
            novo_email    = st.text_input("Email", value=email, key="edit_email")
            novo_raca     = st.text_input("Raça", value=raca, key="edit_raca")
            novo_porte    = st.text_input("Porte", value=porte, key="edit_porte")
            novo_peso     = st.number_input("Peso (kg)", value=peso or 0.0, step=0.1, key="edit_peso")
            novo_nasc_pet = st.date_input("Nascimento do pet", value=nasc_pet, key="edit_nasc_pet")
            novo_nasc_tut = st.date_input("Nascimento do tutor", value=nasc_tut, key="edit_nasc_tut")
            novo_auth     = st.selectbox("Autorização de imagem", ["Sim", "Não"], index=0 if auth_img=="Sim" else 1, key="edit_auth_img")
            novo_tipo_pel = st.text_input("Tipo de pelagem", value=tipo_pel, key="edit_tipo_pel")
            novo_mensal   = st.checkbox("Mensalista", value=bool(mensalista), key="edit_mensalista")
            novo_obs      = st.text_area("Observações", value=obs, key="edit_obs")
            novo_endereco = st.text_input("Endereço", value=endereco or "", key="edit_endereco")

            st.markdown("---")
            col_salvar, col_excluir = st.columns(2)
            with col_salvar:
                if st.button("💾 Salvar alterações", key="botao_salvar_pet"):
                    c.execute("""
                        UPDATE pets SET
                          nome              = ?,
                          tutor             = ?,
                          telefone          = ?,
                          email             = ?,
                          raca              = ?,
                          porte             = ?,
                          peso              = ?,
                          nascimento_pet    = ?,
                          nascimento_tutor  = ?,
                          autorizacao_imagem= ?,
                          tipo_pelagem      = ?,
                          mensalista        = ?,
                          observacoes       = ?,
                          endereco          = ?
                        WHERE id = ?
                    """, (
                        novo_nome, novo_tutor, novo_telefone, novo_email,
                        novo_raca, novo_porte, novo_peso,
                        novo_nasc_pet, novo_nasc_tut,
                        novo_auth, novo_tipo_pel,
                        int(novo_mensal), novo_obs, novo_endereco,
                        pet_id
                    ))
                    conn.commit()
                    st.success("Pet atualizado com sucesso!")
            with col_excluir:
                if st.button("🗑️ Excluir pet", key="botao_excluir_pet"):
                    c.execute("DELETE FROM pets WHERE id = ?", (pet_id,))
                    conn.commit()
                    st.warning("Pet excluído com sucesso!")
                    st.experimental_rerun()

    # --------------------- Serviços ---------------------
    with consultas[1]:
        st.subheader("🔧 Editar / 🗑️ Excluir Serviços")

        grupos_exist = [g[0] for g in c.execute("SELECT nome FROM grupos").fetchall()]
        filtro_grupo = st.selectbox(
            "Grupo",
            grupos_exist,
            key="consulta_filtro_grupo"
        )

        servs = c.execute(
            "SELECT id, nome, intervalo_dias FROM servicos WHERE grupo = ?",
            (filtro_grupo,)
        ).fetchall()

        if servs:
            serv_id, serv_nome, serv_int = st.selectbox(
                "Serviço",
                servs,
                format_func=lambda x: x[1],
                key="consulta_select_servico"
            )
            novo_nome_s = st.text_input(
                "Nome do serviço",
                value=serv_nome,
                key="consulta_edit_nome_servico"
            )
            novo_int_s = st.number_input(
                "Intervalo (dias)",
                min_value=1,
                value=serv_int,
                key="consulta_edit_intervalo_servico"
            )
            novo_grp_s = st.selectbox(
                "Grupo",
                grupos_exist,
                index=grupos_exist.index(filtro_grupo),
                key="consulta_edit_grupo_servico"
            )

            col_sv, col_del = st.columns(2)
            with col_sv:
                if st.button("💾 Salvar serviço", key="consulta_salvar_servico"):
                    c.execute("""
                        UPDATE servicos
                           SET nome = ?, intervalo_dias = ?, grupo = ?
                         WHERE id = ?
                    """, (novo_nome_s, novo_int_s, novo_grp_s, serv_id))
                    conn.commit()
                    st.success("Serviço atualizado!")
            with col_del:
                if st.button("🗑️ Excluir serviço", key="consulta_excluir_servico"):
                    c.execute("DELETE FROM servicos WHERE id = ?", (serv_id,))
                    conn.commit()
                    st.warning("Serviço excluído!")
                    st.experimental_rerun()
        else:
            st.info("Nenhum serviço cadastrado neste grupo.")

    # -------------------- Agendamentos --------------------
    with consultas[2]:
        st.subheader("📆 Editar / 🗑️ Excluir Agendamentos")

        ags = c.execute("""
            SELECT a.id, p.nome, a.data
              FROM agendamentos a
              JOIN pets p ON a.pet_id = p.id
             ORDER BY a.data DESC
        """).fetchall()

        if ags:
            ag_id, pet_nome, ag_data = st.selectbox(
                "Agendamento",
                ags,
                format_func=lambda x: f"{x[1]} em {x[2]}",
                key="consulta_select_agendamento"
            )
            pets_all = c.execute("SELECT id, nome FROM pets").fetchall()
            pet_ids = [p[0] for p in pets_all]
            pet_sel = st.selectbox(
                "Pet",
                pets_all,
                index=pet_ids.index(
                    c.execute("SELECT pet_id FROM agendamentos WHERE id = ?", (ag_id,)).fetchone()[0]
                ),
                format_func=lambda x: x[1],
                key="consulta_edit_ag_pet"
            )
            data_sel = st.date_input(
                "Data",
                value=datetime.strptime(ag_data, "%Y-%m-%d"),
                key="consulta_edit_ag_data"
            )

            col_sv2, col_del2 = st.columns(2)
            with col_sv2:
                if st.button("💾 Salvar agendamento", key="consulta_salvar_ag"):
                    c.execute("""
                        UPDATE agendamentos
                           SET pet_id = ?, data = ?
                         WHERE id = ?
                    """, (pet_sel[0], data_sel, ag_id))
                    conn.commit()
                    st.success("Agendamento atualizado!")
            with col_del2:
                if st.button("🗑️ Excluir agendamento", key="consulta_excluir_ag"):
                    c.execute("DELETE FROM agendamentos WHERE id = ?", (ag_id,))
                    conn.commit()
                    st.warning("Agendamento excluído!")
                    st.experimental_rerun()
        else:
            st.info("Nenhum agendamento cadastrado.")

    # --------------- Histórico de Serviços ---------------
    with consultas[3]:
        st.subheader("📜 Editar / 🗑️ Excluir Histórico de Serviços")

        pets_all = c.execute("SELECT id, nome FROM pets").fetchall()
        pet_filter = st.selectbox(
            "Filtrar por pet",
            pets_all,
            format_func=lambda x: x[1],
            key="consulta_hist_pet"
        )
        regs = c.execute("""
            SELECT h.id, s.nome, h.data
              FROM historico_servicos h
              JOIN servicos s ON h.servico_id = s.id
             WHERE h.pet_id = ?
             ORDER BY h.data DESC
        """, (pet_filter[0],)).fetchall()

        if regs:
            reg_id, serv_nome2, data2 = st.selectbox(
                "Registro",
                regs,
                format_func=lambda x: f"{x[1]} em {x[2]}",
                key="consulta_select_historico"
            )
            data_edit2 = st.date_input(
                "Data de realização",
                value=datetime.strptime(data2, "%Y-%m-%d"),
                key="consulta_edit_historico_data"
            )

            col_sv3, col_del3 = st.columns(2)
            with col_sv3:
                if st.button("💾 Salvar histórico", key="consulta_salvar_historico"):
                    c.execute("""
                        UPDATE historico_servicos
                           SET data = ?
                         WHERE id = ?
                    """, (data_edit2, reg_id))
                    conn.commit()
                    st.success("Histórico atualizado!")
            with col_del3:
                if st.button("🗑️ Excluir histórico", key="consulta_excluir_historico"):
                    c.execute("DELETE FROM historico_servicos WHERE id = ?", (reg_id,))
                    conn.commit()
                    st.warning("Histórico excluído!")
                    st.experimental_rerun()
        else:
            st.info("Nenhum histórico para este pet.")

# --- Transporte ---
elif menu == "Transporte":
    st.header("🚚 Transporte")

    # Busca lista de pets e endereços
    pets_lista = c.execute(
        "SELECT id, nome, endereco FROM pets ORDER BY nome"
    ).fetchall()
    nomes = ["Nenhum"] + [f"{p[1]} ({p[0]})" for p in pets_lista]

    if len(nomes) <= 1:
        st.warning("Cadastre ao menos um pet para usar o transporte.")
    else:
        # Seleção de até 6 animais e coleta de endereços
        enderecos = []
        for i in range(1, 7):
            col1, col2 = st.columns([2, 3])
            with col1:
                selecao = st.selectbox(f"Animal {i}", nomes, key=f"trans_pet_{i}")
            with col2:
                if selecao != "Nenhum":
                    pet_id = int(selecao.split("(")[-1].replace(")", ""))
                    endereco_bd = {
                        str(p[0]): p[2] for p in pets_lista
                    }.get(str(pet_id), "")
                    endereco_edit = st.text_input(
                        f"Endereço {i}",
                        value=endereco_bd,
                        placeholder="Digite ou corrija",
                        key=f"trans_end_{i}"
                    )
                    if endereco_edit:
                        enderecos.append(endereco_edit)

        # Se houver ao menos um endereço, monta rota e cálculos
        if enderecos:
            clinic = "Rua Demétrio Moreira da Luz, 1251, Caxias do Sul - RS"
            pontos = [clinic] + enderecos + [clinic]
            rota = "https://www.google.com/maps/dir/" + "/".join(
                urllib.parse.quote(p) for p in pontos
            )
            st.markdown(f"<a href='{rota}' target='_blank'>🔗 Abrir rota no Google Maps</a>", unsafe_allow_html=True)
            st.markdown("---")

            # Entrada de km e valor por km
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

            # Novo campo: divisor editável
            max_divs = len(enderecos)
            divisor = st.number_input(
                "Número de divisões",
                value=max_divs,
                min_value=1,
                max_value=max_divs,
                step=1,
                key="trans_divisor"
            )

            # Cálculo e edição do valor individual
            valor_sugerido = (valor_total / divisor) if divisor else 0.0
            valor_individual = st.number_input(
                "Valor cobrado por animal",
                value=valor_sugerido,
                step=0.1,
                key="trans_valor_ind"
            )