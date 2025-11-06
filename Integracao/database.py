import sqlite3
from typing import List, Dict, Optional
import os

DB_PATH = os.getenv("DB_PATH", "omie_auth.db")

CREATE_PRODUCTS_SQL = """
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT,
    descricao TEXT,
    modelo TEXT,
    volumetria TEXT,
    tamanho_molde TEXT
);
"""

CREATE_USERS_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active INTEGER DEFAULT 1
);
"""


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(CREATE_PRODUCTS_SQL)
    cur.execute(CREATE_USERS_SQL)
    conn.commit()
    conn.close()


def salvar_produtos(produtos: List[Dict]):
    conn = get_conn()
    cur = conn.cursor()
    for p in produtos:
        cur.execute("""
            INSERT INTO produtos (codigo, descricao, modelo, volumetria, tamanho_molde)
            VALUES (?, ?, ?, ?, ?)
        """, (
            p.get("codigo_produto", ""),
            p.get("descricao", ""),
            p.get("modelo", ""),
            p.get("volumetria", ""),
            p.get("tamanho_molde", "")
        ))
    conn.commit()
    conn.close()


def buscar_todos_produtos():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM produtos")
    rows = cur.fetchall()
    conn.close()
    produtos = [dict(r) for r in rows]
    return produtos

def create_user(username: str, hashed_password: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (username, hashed_password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    conn.close()


def get_user_by_username(username: str) -> Optional[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None