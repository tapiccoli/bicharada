import streamlit as st
import locale
from datetime import datetime

def set_locale():
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except locale.Error:
        pass

def formatar_data(data_str: str) -> str:
    # entrada ISO: YYYY-MM-DD
    try:
        dt = datetime.fromisoformat(data_str)
        return dt.strftime('%d/%m/%Y')
    except:
        return data_str

def parsear_data(data_fmt: str) -> str:
    # entrada dd/mm/YYYY -> retorna ISO
    try:
        dt = datetime.strptime(data_fmt, '%d/%m/%Y')
        return dt.date().isoformat()
    except:
        return data_fmt
