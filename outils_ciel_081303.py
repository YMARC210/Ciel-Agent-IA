# outils_ciel.py
import os
import subprocess
from docx import Document
from jinja2 import Template
from AppOpener import open as ouvrir_app
import schedule
import time

# --- 1. OUTIL WORD + JINJA2 (Rédiger et enregistrer des lettres) ---
def generer_et_sauvegarder_lettre(nom_fichier, destinataire, poste, entreprise, corps_texte):
    """
    Utilise Jinja2 pour structurer une lettre formelle
    et python-docx pour l'enregistrer dans un fichier Word (.docx).
    """
    # Le modèle de structure de la lettre
    modele_lettre = Template("""
À l'attention de {{ destinataire }},

Objet : Candidature pour le poste de {{ poste }} chez {{ entreprise }}

{{ corps_texte }}

Veuillez agréer, Madame, Monsieur, l'expression de mes salutations distinguées.

Cordialement.
""")
   
    # On remplit le modèle avec les données fournies
    texte_final = modele_lettre.render(
        destinataire=destinataire,
        poste=poste,
        entreprise=entreprise,
        corps_texte=corps_texte
    )
   
    # On crée le document Word
    doc = Document()
    doc.add_paragraph(texte_final)
   
    # On l'enregistre avec le nom voulu
    chemin_complet = f"{nom_fichier}.docx"
    doc.save(chemin_complet)
    return f"Succès : Le fichier '{chemin_complet}' a été créé et enregistré !"

# --- 2. OUTIL APPOPENER (Ouvrir les applications) ---
def lancer_application(nom_application):
    """
    Ouvre une application sur ton PC (ex: 'word', 'notepad', 'chrome')
    """
    try:
        ouvrir_app(nom_application, match_closest=True)
        return f"Application '{nom_application}' ouverte avec succès."
    except Exception as e:
        return f"Erreur lors de l'ouverture de l'application : {e}"

# --- 3. OUTIL SCHEDULE (Mettre des alarmes ou rappels) ---
def programmer_rappel(message, heure_str):
    """
    Programme un rappel textuel ou une alerte à une heure précise (format 'HH:MM')
    """
    def action_alarme():
        print(f"\n[ALARME CIEL] Rappel : {message}\n")
        # Tu pourras ajouter ici une alerte visuelle ou sonore si tu veux
       
    schedule.every().day.at(heure_str).do(action_alarme)
    return f"Rappel programmé pour {heure_str} avec le message : '{message}'"