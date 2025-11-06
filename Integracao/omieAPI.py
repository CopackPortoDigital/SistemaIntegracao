import os
import requests

OMIE_URL = "https://app.omie.com.br/api/v1/geral/produtos/"
OMIE_APP_KEY = os.getenv("OMIE_APP_KEY")
OMIE_APP_SECRET = os.getenv("OMIE_APP_SECRET")


def get_produtos(pagina: int = 1, registros_por_pagina: int = 100):
    payload = {
        "call": "ListarProdutos",
        "app_key": OMIE_APP_KEY,
        "app_secret": OMIE_APP_SECRET,
        "param": [{"pagina": pagina, "registros_por_pagina": registros_por_pagina}]
    }
    r = requests.post(OMIE_URL, json=payload)
    r.raise_for_status()
    data = r.json()
    return data.get("produto_servico_cadastro", [])