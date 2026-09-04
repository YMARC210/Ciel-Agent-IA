import os
from tavily import TavilyClient

# ---------------------------------------------------------
# CLÉ API TAVILY
# ---------------------------------------------------------
CLE_API_TAVILY = "🤔"

class MoteurGrounding:
    def __init__(self):
        try:
            self.client = TavilyClient(api_key=CLE_API_TAVILY)
        except Exception as e:
            print(f"Erreur lors de l'initialisation de TavilyClient : {e}")
            self.client = None

    def rechercher_web(self, prompt_utilisateur):
        """
        Recherche des informations sur le Web via Tavily.
        """
        if self.client is None:
            return "Erreur : Clé API Tavily manquante ou invalide."
           
        try:
            response = self.client.search(
                query=prompt_utilisateur,
                search_depth="advanced",
                max_results=3,
                include_answer=True
            )
           
            reponse_synthetisee = response.get('answer', '')
            if not reponse_synthetisee:
                snippets = [res.get('snippet', '') for res in response.get('results', [])]
                reponse_synthetisee = " ".join(snippets)
               
            return reponse_synthetisee[:1500]
        except Exception as e:
            return f"Erreur lors de la recherche Web via Tavily : {e}"

# ---------------------------------------------------------
# INSTANCIATION ET INTERFACE POUR CIEL.PY
# ---------------------------------------------------------
moteur = MoteurGrounding()

def executer_grounding_ciel(prompt):
    """
    Exécute la recherche Web de manière 100% autonome sans aucun filtre de mots-clés.
    Le choix d'appeler cette fonction est entièrement géré par le routeur IA de CIEL.
    """
    contexte_synthetise = moteur.rechercher_web(prompt)
    return contexte_synthetise, True
