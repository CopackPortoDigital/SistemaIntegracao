import os
import fastapi
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
from datetime import timedelta

from omie_api import get_produtos
from database import init_db, salvar_produtos, buscar_todos_produtos, create_user, get_user_by_username
from auth import get_password_hash, verify_password, create_access_token, decode_access_token
from ai_clustering import agrupar_produtos

# init database
init_db()

app = FastAPI(title="Omie + IA + JWT Backend")

# OAuth2 scheme - tokenUrl should be the path relative to the app (no leading slash required)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class UserCreate(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


@app.post('/register')
def register(user: UserCreate):
    existing = get_user_by_username(user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed = get_password_hash(user.password)
    create_user(user.username, hashed)
    return {"msg": "user created"}


@app.post('/token', response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_username(form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not verify_password(form_data.password, user['hashed_password']):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '60')))
    access_token = create_access_token(data={"sub": user['username']}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


# Dependency
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_access_token(token)
        username: str = payload.get('sub')
        if username is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@app.get('/')
def root():
    return {"status": "ok"}


@app.get('/sincronizar')
def sincronizar(current_user=Depends(get_current_user)):
    produtos = get_produtos()
    salvar_produtos(produtos)
    return {"mensagem": f"{len(produtos)} produtos importados e salvos no banco."}


@app.get('/produtos')
def listar(current_user=Depends(get_current_user)):
    return {"dados": buscar_todos_produtos()}


@app.get('/agrupar')
def agrupar(current_user=Depends(get_current_user)):
    produtos = buscar_todos_produtos()
    grupos = agrupar_produtos(produtos)
    return {"total_grupos": len(grupos), "grupos": grupos}