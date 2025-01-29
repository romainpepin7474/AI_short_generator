import requests
from bs4 import BeautifulSoup
import csv
from fact import Fact
import re
from settings import root_url, lang, url
from typing import List
from functions import extract_urls, save_urls_to_json, load_urls_from_json
from functions_scrap import extract_facts_from_url

# URL de la page à scraper
import os
from short import Short

def scrap_fact(url, subject):
    facts = extract_facts_from_url(url, subject)

def recuperer_fichiers_fact_json(repertoire_principal):
    fichiers_fact = []
    # Parcours récursif du répertoire principal
    for racine, dossiers, fichiers in os.walk(repertoire_principal):
        for fichier in fichiers:
            if fichier == "fact.json":
                # Création du chemin complet vers le fichier fact.json
                chemin_fichier = os.path.join(racine, fichier)
                fichiers_fact.append(chemin_fichier)

    return fichiers_fact

def create_contenu(storage_path):
    fichiers = recuperer_fichiers_fact_json(storage_path)
    for fichier in sorted(fichiers):
        fact = Fact.load(fichier)
        fact.process()
        fact.save()

def create_audio(storage_path):
    fichiers = recuperer_fichiers_fact_json(storage_path)
    for fichier in sorted(fichiers):
        fact = Fact.load(fichier)
        fact.Get_Audio()
        fact.save()

def create_videos(storage_path):
    fichiers = recuperer_fichiers_fact_json(storage_path)
    for fichier in sorted(fichiers):
        print("fichier", fichier)
        fact = Fact.load(fichier)
        print("create_video launch")
        fact.create_content()
        fact.save()


if __name__ == '__main__':
    # url = "https://www.factretriever.com/emu-facts"
    # Scrape des faits depuis le site
    # scrap_fact('https://www.factretriever.com/emu-facts', "emu")
    # scrap_fact('https://www.factretriever.com/dog-facts', "dog")
    # scrap_fact('https://www.factretriever.com/lions', "lion")
    # create_videos("storage_facts/dog/EN")
    # create_audio("storage_facts/dog/EN/Negative")
    
    """fact = Fact.load("storage_facts/dog/EN/Negative/fact_22/fact.json")
    fact.create_content()
    fact.save()"""

    create_videos("storage_facts/dog/EN/Positive")

    """short = Short(rush_list= ['storage_facts/dog/EN/Negative/fact_1'], subject= "dog", language='EN', title="Suprising Dog Fact")
    short.create_short()"""
