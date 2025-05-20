import sqlite3
import streamlit as st
from pathlib import Path

DB_PATH = Path(__file__).parent / "database.db"

@st.cache_resource
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Criação e migração da tabela pets
    c.execute("""
    CREATE TABLE IF NOT EXISTS pets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        especie TEXT,
        nome TEXT,
        tutor TEXT,
        telefone TEXT,
        email TEXT,
        data_nasc_pet TEXT,
        data_nasc_tutor TEXT,
        raca TEXT,
        porte TEXT,
        peso REAL,
        autorizacao_imagem TEXT,
        tipo_pelagem TEXT,
        agressividade TEXT,
        observacoes TEXT,
        endereco TEXT
    )""")
    # Adiciona colunas novas em bancos existentes
    for col in ["especie","telefone","email","data_nasc_pet","data_nasc_tutor",
                "raca","porte","peso","autorizacao_imagem","tipo_pelagem",
                "agressividade","observacoes","endereco"]:
        try:
            c.execute(f"ALTER TABLE pets ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass

        try:
            c.execute("ALTER TABLE servicos ADD COLUMN rota TEXT")
        except sqlite3.OperationalError:
                pass

    # Tabelas auxiliares
    c.execute("""
    CREATE TABLE IF NOT EXISTS grupos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS servicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pet_id INTEGER,
        grupo TEXT,
        descricao TEXT,
        data_servico TEXT,
        lembrete_dias INTEGER,
        retorno_personalizado_id INTEGER,
        FOREIGN KEY(pet_id) REFERENCES pets(id)
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS financeiro (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        servico_id INTEGER,
        valor REAL,
        pago INTEGER DEFAULT 0,
        FOREIGN KEY(servico_id) REFERENCES servicos(id)
    )""")
    
    
        # Cria tabela servicos…
    c.execute("""CREATE TABLE IF NOT EXISTS servicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pet_id INTEGER,
        grupo TEXT,
        descricao TEXT,
        data_servico TEXT,
        lembrete_dias INTEGER,
        retorno_personalizado_id INTEGER,
        FOREIGN KEY(pet_id) REFERENCES pets(id)
    )""")

    # Migração das colunas existentes…
    for col_def in [
        ("pet_id", "INTEGER"),  ("grupo", "TEXT"),  ("descricao", "TEXT"),
        ("data_servico", "TEXT"), ("lembrete_dias", "INTEGER"),
        ("retorno_personalizado_id", "INTEGER")
    ]:
        col_name, col_type = col_def
        try:
            c.execute(f"ALTER TABLE servicos ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass
