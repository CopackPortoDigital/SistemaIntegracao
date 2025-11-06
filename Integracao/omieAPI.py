import requests
import os

OMIE_URL = "https://app.omie.com.br/api/v1/geral/produtos/"
OMIE_APP_KEY = os.getenv("chave OMIE")
OMIE_APP_SECRET = os.getenv("OMIE_APP_SECRET")

def get_produtos():
    payload = {
        "call": "ListarProdutos",
        "app_key": OMIE_APP_KEY,
        "app_secret": OMIE_APP_SECRET,
        "param": [{"pagina": 1, "registros_por_pagina": 100}]
    }
    r = requests.post(OMIE_URL, json=payload)
    r.raise_for_status()
    data = r.json()
    produtos = data.get("produto_servico_cadastro", [])
    return produtos
