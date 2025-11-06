from fastapi import FastAPI
from omie_api import get_produtos
from ai_clustering import agrupar_produtos
from database import init_db, salvar_produtos, buscar_todos

app = FastAPI(title="Integração Omie + IA + Banco de Dados")

# Inicializa banco ao iniciar o servidor
init_db()

@app.get("/")
def raiz():
    return {"status": "ok", "mensagem": "API Omie com IA e Banco de Dados funcionando!"}

@app.get("/sincronizar")
def sincronizar():
    produtos = get_produtos()
    salvar_produtos(produtos)
    return {"mensagem": f"{len(produtos)} produtos importados e salvos no banco."}

@app.get("/produtos")
def listar():
    return {"dados": buscar_todos()}

@app.get("/agrupar")
def agrupar():
    produtos = buscar_todos()
    grupos = agrupar_produtos(produtos)
    return {"total_grupos": len(grupos), "grupos": grupos}
