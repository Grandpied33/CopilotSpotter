# retrieve_docs.py
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# Récupération des variables d’environnement
endpoint = os.getenv("ENDPOINT")
deployment = os.getenv("EMBEDDINGS_MODEL")
api_key = os.getenv("SUBSCRIPTION_KEY")
api_version = os.getenv("API_VERSION")
search_endpoint = os.getenv("SEARCH_ENDPOINT")
search_index = os.getenv("AISEARCH_INDEX_NAME")
search_key = os.getenv("SEARCH_API_KEY")

# Initialisation des clients
search_client = SearchClient(
    endpoint=search_endpoint,
    index_name=search_index,
    credential=AzureKeyCredential(search_key)
)

embed_client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=api_key
)

def retrieve_docs(user_input: str, top_k: int = 5) -> list:
    # Génère l’embedding de la requête
    embedding = embed_client.embeddings.create(
        model=deployment,
        input=user_input
    )
    vec = embedding.data[0].embedding

    # Recherche vectorielle dans Azure Search
    vq = VectorizedQuery(vector=vec, k_nearest_neighbors=top_k, fields="contentVector")
    results = search_client.search(
        search_text="",
        vector_queries=[vq],
        select=["content", "title", "filepath", "url"],
    )

    # Formate les résultats
    docs = []
    for r in results:
        docs.append({
            "title": r.get("title", ""),
            "filepath": r.get("filepath", ""),
            "url": r.get("url", ""),
            "content": r.get("content", "")
        })
    return docs
