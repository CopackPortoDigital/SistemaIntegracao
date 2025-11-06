from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

def agrupar_produtos(produtos):
    """
    Usa IA (KMeans + TF-IDF) para agrupar produtos com base nas descrições e atributos.
    """
    if not produtos:
        return []

    textos = [
        f"{p['descricao']} {p['modelo']} {p['volumetria']} {p['tamanho_molde']}"
        for p in produtos
    ]

    # Cria vetores numéricos a partir do texto
    vectorizer = TfidfVectorizer(stop_words='portuguese')
    X = vectorizer.fit_transform(textos)

    # Define número de grupos com base na quantidade de produtos
    n_clusters = max(2, min(6, len(produtos)//5))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)

    # Agrupa por rótulos
    grupos = {}
    for label, produto in zip(labels, produtos):
        chave = f"grupo_{label+1}"
        if chave not in grupos:
            grupos[chave] = []
        grupos[chave].append(produto)

    return grupos
