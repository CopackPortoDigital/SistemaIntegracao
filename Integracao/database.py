import sqlite3
from typing import List, Dict

DB_NAME = "omie.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            descricao TEXT,
            modelo TEXT,
            volumetria TEXT,
            tamanho_molde TEXT
        )
    """)
    conn.commit()
    conn.close()

def salvar_produtos(produtos: List[Dict]):
    conn = sqlite3.connect(DB_NAME)
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

def buscar_todos():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM produtos")
    rows = cur.fetchall()
    conn.close()

    produtos = []
    for row in rows:
        produtos.append({
            "id": row[0],
            "codigo": row[1],
            "descricao": row[2],
            "modelo": row[3],
            "volumetria": row[4],
            "tamanho_molde": row[5]
        })
    return produtos
