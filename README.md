# SpotterCopilot 🚀
=== WIP ===

Agent IA sur Azure pour optimiser vos séances de sport.  
Répond **uniquement** aux questions sportives.  
S’appuie sur la RAG (Azure AI Search + embeddings) pour des réponses ancrées.

---

## 📋 Prérequis

- **Docker** installé et en cours d’exécution
- **Azure CLI** pour vous authentifier (`az login`)
- Un compte Azure avec un **projet AI Foundry** configuré
- Variables d’environnement dans un fichier `.env` à la racine :
  ```env
  ENDPOINT="https://<ton-endpoint>.openai.azure.com/"
  MODEL_NAME="<nom_du_modele>"
  DEPLOYMENT="<nom_du_deploiement>"
  SUBSCRIPTION_KEY="<ta_cle_api>"
  API_VERSION="2024-12-01-preview"
  ```
- Le CSV d’exercices prêt : `ressources/Large_Exercises_CSV.csv`

---

## 🚀 Installation & Lancement

1. **Cloner le dépôt** :
   ```bash
   git clone https://github.com/Grandpied33/CopilotSpotter.git
   cd CopilotSpotter
   ```
2. **Créer le fichier `.env`** à la racine (sans le versionner) :
   ```bash
   # Variables d’environnement
   ENDPOINT="https://<ton-endpoint>.openai.azure.com/"
   MODEL_NAME="<nom_du_modele>"
   DEPLOYMENT="<nom_du_deploiement>"
   SUBSCRIPTION_KEY="<ta_cle_api>"
   API_VERSION="2024-12-01-preview"
   ```
3. **Ouvrir le projet dans un Dev Container** (PyCharm ou VS Code) :
   - Accepter la proposition **Rebuild & Reopen in Container**.

   **OU** si tu préfères la ligne de commande :
   ```bash
   # Construire l’image Docker
   docker build -t spottercopilot .devcontainer
   
   # Exécuter le container en montant le code
   docker run --rm -it -v $PWD:/app spottercopilot bash
   ```
4. **Installer les dépendances** (dans le container) :  
   ```bash
   pip install --no-cache-dir -r requirements.txt
   ```
5. **Importer le CSV d’exercices** (`ressources/Large_Exercises_CSV.csv`) dans Azure AI Foundry :  
   - Dans **Data assets** > **+ Nouvelles données** > **Télécharger des fichiers** > sélectionner `ressources/Large_Exercises_CSV.csv`.  
   - Activer **Enable vector search**, choisir `description` pour les embeddings.
6. **Importer le template de prompt** :  
   - Dans **Assets**, uploader `grounded_chat.prompty`.
7. **Lancer l’agent localement** :  
   ```bash
   python main.py
   ```
8. **Interagir** :
   ```bash
   🧑> Je veux un plan force pour les pectoraux
   ```

---

> **Astuce** : Toute la partie RAG et configuration d’index se fait dans l’UI Azure AI Foundry, pas besoin de script supplémentaire.

