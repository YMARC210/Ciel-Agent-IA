import os
import sys
import json
import requests
import streamlit as st
import chromadb
import pyautogui
import pyttsx3
import whisper

# Import du moteur grounding mis à jour
from moteur_grounding import executer_grounding_ciel

# Import du deuxième outil (Calculatrice)
from calcul import effectuer_calcul

# Import des nouveaux outils bureautiques et système
from outils_ciel import (
    generer_et_sauvegarder_lettre, 
    lancer_application, 
    programmer_rappel
)

# Import de l'outil général pour les matières scientifiques et scolaires
try:
    from outils_scolaires import traiter_outils_scolaires
except ImportError:
    traiter_outils_scolaires = None

# ==========================================
# CONFIGURATION STREAMLIT & MÉMOIRE CHROMADB
# ==========================================
st.set_page_config(page_title="CIEL V7.0", page_icon="🤖", layout="wide")

@st.cache_resource
def initialiser_chroma_multi():
    client = chromadb.PersistentClient(path="./memoire_ciel_db")
    dialogues = client.get_or_create_collection(name="dialogues_bruts")
    erreurs = client.get_or_create_collection(name="journal_d_erreurs")
    connaissances = client.get_or_create_collection(name="base_de_connaissances")
    return dialogues, erreurs, connaissances

collection_dialogues, collection_erreurs, collection_connaissances = initialiser_chroma_multi()

@st.cache_resource
def get_whisper_model():
    return whisper.load_model("tiny")

@st.cache_data
def charger_verbes_json():
    if os.path.exists("verbes.json"):
        with open("verbes.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return None

donnees_verbes_json = charger_verbes_json()

# ==========================================
# MOTEUR DE CONJUGAISON NATIVE
# ==========================================
def obtenir_radical(verbe: str) -> tuple:
    v = verbe.strip().lower()
    if v.endswith("er") and v != "aller":
        return v[:-2], 1
    elif v.endswith("ir") and not v.endswith(("oir", "oire")):
        return v[:-2], 2
    return v, 3

def conjuguer_verbe_francais(verbe: str, temps: str = "present") -> str:
    if not donnees_verbes_json:
        return "Erreur : Le fichier verbes.json n'est pas disponible."
    
    verbe_clean = verbe.strip().lower()
    temps_clean = temps.strip().lower()
    personnes = ["je", "tu", "il/elle", "nous", "vous", "ils/elles"]
    
    if "irreguliers_essentiels" in donnees_verbes_json and verbe_clean in donnees_verbes_json["irreguliers_essentiels"]:
        v_data = donnees_verbes_json["irreguliers_essentiels"][verbe_clean]
        if temps_clean in v_data:
            conjugs = v_data[temps_clean]
            res = f"### Conjugaison de **{verbe_clean.capitalize()}** ({temps_clean})\n"
            for p, c in zip(personnes, conjugs):
                res += f"- {p} {c}\n"
            return res

    radical, groupe = obtenir_radical(verbe_clean)
    
    if temps_clean in ["present", "présent"]:
        if groupe == 1:
            terminaisons = ["e", "es", "e", "ons", "ez", "ent"]
            res = f"### **{verbe_clean.capitalize()}** - Présent (1er groupe)\n"
            for p, t in zip(personnes, terminaisons):
                sujet = "j'" if p == "je" and radical[0] in "aeiouyéàâ" else p + " "
                res += f"- {sujet}{radical}{t}\n"
            return res
            
    return f"Conjugaison générée pour {verbe_clean} ({temps_clean})."

def extraire_details_conjugaison(texte: str) -> tuple:
    texte_lower = texte.lower()
    mots = [m.strip("?.!,'\"") for m in texte_lower.split()]
    
    temps_cible = "present"
    if "imparfait" in texte_lower:
        temps_cible = "imparfait"
    elif "futur" in texte_lower:
        temps_cible = "futur simple"
    elif "passé composé" in texte_lower or "passe compose" in texte_lower:
        temps_cible = "passé composé"
        
    mots_a_ignorer = ["le", "la", "les", "un", "une", "de", "du", "des", "verbe", "conjugue", "conjuguer", "conjugaison", "futur", "imparfait", "présent", "present", "passé", "composé"]
    verbe_trouve = "chanter"
    for mot in mots:
        if mot not in mots_a_ignorer and not mot.startswith("l'"):
            verbe_trouve = mot
            break
            
    return verbe_trouve, temps_cible

# ==========================================
# OUTILS SYSTÈME & LLM LOCAL
# ==========================================
def executer_commande_bureau(action: str) -> str:
    if "capture" in action or "screenshot" in action:
        pyautogui.screenshot("screenshot_ciel.png")
        return "Capture d'écran enregistrée dans le dossier du projet."
    return ""

def vocaliser_texte_local(texte: str):
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 170)
        engine.say(texte)
        engine.runAndWait()
    except Exception as e:
        st.warning(f"Erreur de synthèse vocale : {e}")

def transcrire_audio_whisper(fichier_audio_bytes) -> str:
    try:
        nom_temp = "input_temp.wav"
        with open(nom_temp, "wb") as f:
            f.write(fichier_audio_bytes.read())
        modele = get_whisper_model()
        resultat = modele.transcribe(nom_temp, language="fr", fp16=False)
        return resultat.get("text", "").strip()
    except Exception as e:
        st.error(f"Erreur Whisper : {e}")
        return ""

def interroger_llm_local(system_prompt: str, user_prompt: str, tools=None) -> dict:
    """Interroge le serveur LLM local (ex: llama-server/Qwen)"""
    url = "http://127.0.0.1:8080/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 512,
        "temperature": 0.1
    }
    
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
        
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=300)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]
        else:
            return {"role": "assistant", "content": f"Erreur Serveur HTTP {response.status_code} : {response.text}"}
    except Exception as e:
        return {"role": "assistant", "content": f"Erreur de connexion au LLM : {e}"}

# ==========================================
# DECLARATION DES OUTILS POUR CIEL
# ==========================================
outils_ciel = [
    {
        "type": "function",
        "function": {
            "name": "moteur_grounding",
            "description": "Appelle cet outil dès que la demande porte sur une valeur numérique en temps réel, un cours, un prix dynamique, un événement actuel ou tout fait nécessitant une vérification externe.",
            "parameters": {
                "type": "object",
                "properties": {
                    "requete": {
                        "type": "string",
                        "description": "La recherche exacte à effectuer sur le Web pour trouver la donnée fraîche"
                    }
                },
                "required": ["requete"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "effectuer_calcul",
            "description": "Appelle cet outil pour exécuter des calculs mathématiques ou résoudre des équations arithmétiques précises.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "L'expression mathématique exacte à évaluer"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]

# ==========================================
# MOTEUR PRINCIPAL (SÉGREGATION ET OUTILS)
# ==========================================
def traiter_demande_utilisateur(prompt_utilisateur: str) -> str:
    prompt_lower = prompt_utilisateur.lower().strip()
    
    # 0. Réponse personnalisée d'identité CIEL (YEDE MARC)
    if any(p in prompt_lower for p in ["qui es tu", "qui es-tu", "presente toi", "présente toi", "qu'es tu", "qu'es-tu"]):
        return "Je suis CIEL, un assistant IA autonome développé par YEDE MARC, un jeune autodidacte et HPI de 15 ans passionné de science. Je suis la concrétisation de son projet CIEL et j'ai été développé pour repousser les limites de l'IA locale."

    # 1. Conjugaison native
    if any(m in prompt_lower for m in ["conjugue", "conjuguer", "conjugaison"]):
        verbe, temps = extraire_details_conjugaison(prompt_utilisateur)
        return conjuguer_verbe_francais(verbe, temps)

    # 2. Prise de décision par classification LLM autonome
    with st.spinner("🤖 CIEL analyse et choisit le meilleur outil..."):
        system_router = (
            "Tu es le routeur d'outils autonome de CIEL V7.0.\n"
            "Analyse le message de l'utilisateur et réponds STRICTEMENT par un seul mot parmi :\n"
            "- 'GROUNDING' : Si la demande porte sur un prix, un cours variable (ex: Bitcoin, devises), une valeur actuelle, la météo ou une information récente.\n"
            "- 'CALCUL' : UNIQUEMENT si la demande contient une opération arithmétique simple et directe.\n"
            "- 'SCOLAIRE' : Si la demande porte sur une réaction chimique, un équilibrage de chimie, un calcul formel/dérivée/intégrale, de la physique avec unités, de la biologie, une correction de grammaire, ou une définition/fiche de cours académique.\n"
            "- 'BUREAUTIQUE' : Si la demande concerne l'ouverture d'une application (Word, etc.), la rédaction/création d'un document Word, ou la programmation d'une alarme/rappel.\n"
            "- 'DIRECT' : Pour TOUT LE RESTE (salutations, questions générales, conseils, conversation simple).\n"
            "Ta réponse doit être UNIQUEMENT l'un de ces mots : GROUNDING, CALCUL, SCOLAIRE, BUREAUTIQUE ou DIRECT."
        )
        
        classification = interroger_llm_local(system_router, prompt_utilisateur)
        decision = classification.get("content", "").strip().upper()

        if "SCOLAIRE" in decision and traiter_outils_scolaires is not None:
            res_scolaire = traiter_outils_scolaires(prompt_utilisateur)
            if res_scolaire:
                return res_scolaire

        if "GROUNDING" in decision:
            res_grounding = executer_grounding_ciel(prompt_utilisateur)
            
            if isinstance(res_grounding, tuple):
                reponse_grounding = res_grounding[0]
            else:
                reponse_grounding = res_grounding
                
            if reponse_grounding:
                return reponse_grounding
            return "Impossible de récupérer les données en direct."

        elif "CALCUL" in decision:
            prompt_calc = f"Extraire uniquement l'expression mathématique à évaluer dans ce texte (ex: '2500*4*12') : {prompt_utilisateur}"
            res_calc = interroger_llm_local("Tu es une calculatrice. Donne uniquement l'expression mathématique sans aucun texte.", prompt_calc)
            expression = res_calc.get("content", "").strip()
            return effectuer_calcul(expression)

        elif "BUREAUTIQUE" in decision:
            if "ouvre" in prompt_lower or "lancer" in prompt_lower:
                if "word" in prompt_lower:
                    return lancer_application("word")
                elif "bloc-notes" in prompt_lower or "notepad" in prompt_lower:
                    return lancer_application("notepad")
                else:
                    mots = prompt_lower.split()
                    for i, m in enumerate(mots):
                        if m in ["ouvre", "lance"] and i + 1 < len(mots):
                            return lancer_application(mots[i+1])
                    return lancer_application("word")

            elif "rappel" in prompt_lower or "alarme" in prompt_lower:
                return programmer_rappel(
                    message=prompt_utilisateur,
                    heure_str="08:00"
                )

            system_bureau = (
                "Tu es l'agent bureautique de CIEL V7.0. "
                "Ton rôle est d'analyser la demande de l'utilisateur et d'utiliser l'outil de génération de documents pour rédiger et enregistrer les fichiers."
            )
            
            outils_bureautiques_specifiques = [
                {
                    "type": "function",
                    "function": {
                        "name": "generer_et_sauvegarder_lettre",
                        "description": "Rédige et enregistre un document Word sur le disque de l'ordinateur.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "nom_fichier": {
                                    "type": "string",
                                    "description": "Le nom exact du fichier à enregistrer"
                                },
                                "corps_texte": {
                                    "type": "string",
                                    "description": "Le contenu textuel complet à placer dans le document"
                                }
                            },
                            "required": ["nom_fichier", "corps_texte"]
                        }
                    }
                }
            ]

            reponse_agent_bureau = interroger_llm_local(system_bureau, prompt_utilisateur, tools=outils_bureautiques_specifiques)
            
            if isinstance(reponse_agent_bureau, dict) and "tool_calls" in reponse_agent_bureau:
                tool_call = reponse_agent_bureau["tool_calls"][0]
                nom_fonction = tool_call["function"]["name"]
                arguments_str = tool_call["function"]["arguments"]
                
                try:
                    arguments = json.loads(arguments_str)
                    if nom_fonction == "generer_et_sauvegarder_lettre":
                        return generer_et_sauvegarder_lettre(
                            nom_fichier=arguments.get("nom_fichier", "document_ciel"),
                            destinataire="À qui de droit",
                            poste="Demande utilisateur",
                            entreprise="Souveraineté Locale",
                            corps_texte=arguments.get("corps_texte", prompt_utilisateur)
                        )
                except Exception as e:
                    pass

            nom_secours = "document_ciel"
            for m in prompt_utilisateur.split():
                m_clean = m.strip(".,;:?!'\"")
                if m_clean.endswith(".docx") or m_clean.lower() in ["document", "lettre"]:
                    nom_secours = m_clean.replace(".docx", "")
                    break
                    
            return generer_et_sauvegarder_lettre(
                nom_fichier=nom_secours,
                destinataire="À qui de droit",
                poste="Demande utilisateur",
                entreprise="Souveraineté Locale",
                corps_texte=prompt_utilisateur
            )

        else:
            system_direct = "Tu es CIEL V7.0, un assistant IA utile, universel et autonome."
            message_reponse = interroger_llm_local(system_direct, prompt_utilisateur)
            return message_reponse.get("content", "").strip()

# ==========================================
# INTERFACE UTILISATEUR
# ==========================================
st.title("🤖 CIEL V7.0")

if "historique" not in st.session_state:
    st.session_state.historique = []

audio_value = st.audio_input("Enregistrer un message vocal")
prompt_saisi = st.chat_input("Posez votre question à CIEL...")

prompt_final = None
if audio_value:
    with st.spinner("Transcription audio avec Whisper..."):
        prompt_final = transcrire_audio_whisper(audio_value)
elif prompt_saisi:
    prompt_final = prompt_saisi

for message in st.session_state.historique:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt_final:
    st.session_state.historique.append({"role": "user", "content": prompt_final})
    with st.chat_message("user"):
        st.markdown(prompt_final)
        
    with st.chat_message("assistant"):
        reponse = traiter_demande_utilisateur(prompt_final)
        st.markdown(reponse)
        
    st.session_state.historique.append({"role": "assistant", "content": reponse})
    
    try:
        collection_dialogues.add(
            documents=[f"User: {prompt_final}\nCIEL: {reponse}"],
            ids=[f"msg_{len(st.session_state.historique)}"]
        )
    except Exception as e:
        pass
