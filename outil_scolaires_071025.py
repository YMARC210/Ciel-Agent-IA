# outils_scolaires.py
import sympy as sp
import chempy as ch
from pint import UnitRegistry
import wikipediaapi
import language_tool_python

# Initialisation des moteurs légers
ureg = UnitRegistry()
wiki_en = wikipediaapi.Wikipedia(
    user_agent="CIEL_Assistant_School/1.0 (contact@ciel.ai)",
    language="en"
)

# 1. MATHEMATICS (Maths, Add Maths, Further Maths)
def resoudre_maths(expression_texte):
    try:
        # Tente de résoudre ou simplifier une équation mathématique
        expr = sp.sympify(expression_texte)
        resolution = sp.simplify(expr)
        return f"[Calculateur SymPy] Résultat exact : {resolution}"
    except Exception as e:
        return f"Calcul mathématique non interprété : {e}"

# 2. CHEMISTRY & FOOD NUTRITION (Équilibrage de réactions)
def equilibrer_chimie(reactifs, produits):
    try:
        # Exemple: equilibrer_chimie(["H2", "O2"], ["H2O"])
        reac, prod = ch.balance_stoichiometry(set(reactifs), set(produits))
        return f"[Moteur ChemPy] Équation équilibrée : {dict(reac)} -> {dict(prod)}"
    except Exception as e:
        return f"Réaction non équilibrée : {e}"

# 3. PHYSICS & PE (Conversion d'unités)
def convertir_unite_physique(valeur_avec_unite, unite_cible):
    try:
        q = ureg(valeur_avec_unite)
        res = q.to(unite_cible)
        return f"[Physique Pint] Conversion : {valeur_avec_unite} = {res}"
    except Exception as e:
        return f"Erreur de conversion physique : {e}"

# 4. ENGLISH & FRENCH GRAMMAR CHECK
def corriger_grammaire_anglais(texte):
    try:
        tool = language_tool_python.LanguageToolPublicAPI('en-US')
        matches = tool.check(texte)
        correction = language_tool_python.utils.correct(texte, matches)
        return f"[LanguageTool English] Texte corrigé : {correction}"
    except Exception as e:
        return f"Erreur de vérification linguistique : {e}"

# 5. ENCYCLOPEDIA (Biology, ICT, History, Geography, Economics)
def chercher_cours_wikipedia(sujet):
    try:
        page = wiki_en.page(sujet)
        if page.exists():
            # Renvoie les 3 premiers paragraphes du cours certifié
            resume = page.summary[0:1000]
            return f"[Wiki Fiche Cours - {sujet}] : {resume}"
        else:
            return "Fiche de cours non trouvée."
    except Exception as e:
        return f"Erreur lors de la recherche du cours : {e}"

# ==========================================
# FONCTION PRINCIPALE APPELÉE PAR CIEL.PY
# ==========================================
def traiter_outils_scolaires(prompt_utilisateur: str) -> str:
    prompt_lower = prompt_utilisateur.lower().strip()
   
    # 1. Traitement des mathématiques formelles (dérivées, intégrales, équations)
    if any(m in prompt_lower for m in ["dérivée", "derivative", "intégrale", "integral", "solve", "résoudre"]):
        return resoudre_maths(prompt_utilisateur)
       
    # 2. Correction de grammaire en Anglais
    elif any(g in prompt_lower for g in ["grammar", "correct this", "orthographe anglais", "corriger anglais"]):
        return corriger_grammaire_anglais(prompt_utilisateur)
       
    # 3. Fiches de cours certifiées (Biology, Geography, Economics, ICT, Geology, Sport)
    else:
        # Nettoyage pour extraire le sujet principal de la recherche
        sujet = prompt_lower.replace("c'est quoi", "").replace("what is", "").replace("explique", "").replace("explain", "").strip()
        if not sujet:
            sujet = prompt_utilisateur
        return chercher_cours_wikipedia(sujet)