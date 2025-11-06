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