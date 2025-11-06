# Project: Omie Integration Backend with AI Clustering and JWT Auth
# Files included below. Save each section into the named filename.
#
# This document is a corrected and improved version addressing the reported
# runtime error `NameError: name 'fastapi' is not defined` and adding a
# simple test script to verify the running service.

### FILE: requirements.txt

fastapi
uvicorn
requests
scikit-learn
numpy
python-jose[cryptography]
passlib[bcrypt]
python-dotenv
pydantic

### FILE: .env (example)

OMIE_APP_KEY=your_omie_app_key
OMIE_APP_SECRET=your_omie_app_secret
JWT_SECRET_KEY=your_super_secret_key_change_this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DB_PATH=omie_auth.db

### FILE: omie_api.py

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


### FILE: database.py

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

# User helpers


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


### FILE: auth.py

from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from typing import Optional
import os

PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change_me")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def verify_password(plain_password, hashed_password):
    return PWD_CONTEXT.verify(plain_password, hashed_password)


def get_password_hash(password):
    return PWD_CONTEXT.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # python-jose accepts datetime for 'exp', but to be explicit we convert to int timestamp
    if isinstance(to_encode["exp"], datetime):
        to_encode["exp"] = int(to_encode["exp"].timestamp())
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise


### FILE: ai_clustering.py

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans


def agrupar_produtos(produtos):
    if not produtos:
        return {}

    textos = [
        f"{p.get('descricao','')} {p.get('modelo','')} {p.get('volumetria','')} {p.get('tamanho_molde','')}"
        for p in produtos
    ]

    vectorizer = TfidfVectorizer(stop_words='portuguese')
    X = vectorizer.fit_transform(textos)

    # Determine clusters conservatively
    n_clusters = max(2, min(8, max(2, len(produtos) // 10)))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)

    grupos = {}
    for label, produto in zip(labels, produtos):
        chave = f"grupo_{label+1}"
        grupos.setdefault(chave, []).append(produto)

    return grupos


### FILE: main.py

# NOTE: previous runtime error `NameError: name 'fastapi' is not defined` can
# happen if code references the module name `fastapi` directly while it wasn't
# imported. To be defensive and explicit we import the fastapi module as well
# as the specific helpers. We also avoid dynamic `__import__` usage.

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


### FILE: tests/test_health_and_auth.py

# Simple test script to validate the running service. This is not a full test
# suite but useful to confirm the app starts and the / endpoint responds.

import requests

BASE = "http://127.0.0.1:8000"


def test_health():
    r = requests.get(f"{BASE}/")
    print('health status code:', r.status_code)
    assert r.status_code == 200
    data = r.json()
    assert data.get('status') == 'ok'


if __name__ == '__main__':
    print('Running quick sanity test...')
    test_health()
    print('If this passed, start using /register and /token to test auth-protected endpoints.')


### RUN INSTRUCTIONS

1) Create a virtualenv and install requirements:

    python -m venv .venv
    source .venv/bin/activate   # on Linux/Mac
    .\.venv\Scripts\activate  # on Windows
    pip install -r requirements.txt

2) Create a `.env` file from the example or export the environment variables used.

3) Start the app:

    uvicorn main:app --reload

4) Run the quick test (optional) in another terminal to verify health:

    python tests/test_health_and_auth.py


### NOTES ABOUT THE ORIGINAL ERROR

- The error `NameError: name 'fastapi' is not defined` can appear if some code refers to the `fastapi` module object without importing it. In the original version the top-level explicit `import fastapi` was missing; the revised `main.py` adds `import fastapi` in addition to the specific imports to be defensive.
- We also replaced dynamic `__import__('auth')` usage with a direct import of `decode_access_token` for clarity and to avoid subtle runtime problems.
- `create_access_token` now converts the `exp` claim to an integer timestamp to avoid incompatibilities with some JWT libraries.

If you still see the error after this change, please tell me:
- the exact command you used to run the server, and
- the full stack trace (copy-paste).  

I can further debug environment issues (missing packages, wrong Python interpreter) if you paste the traceback.
