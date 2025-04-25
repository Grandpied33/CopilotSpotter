import os
from dotenv import load_dotenv
from backend.chat.retrieve_docs import retrieve_docs

# Charge ton .env
load_dotenv()

if __name__ == "__main__":
    # Ta requête de test
    requete = "Je veux un programme volume pour les biceps"
    try:
        docs = retrieve_docs(user_input=requete)
        print("Résultats :\n")
        if not docs:
            print("⚠️ Aucun document trouvé.")
        for d in docs:
            print(f"- Title   : {d['title']}")
            print(f"  Filepath: {d['filepath']}")
            print(f"  Content : {d['content'][:200]}...\n")
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
