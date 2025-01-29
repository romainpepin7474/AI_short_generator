import requests
from bs4 import BeautifulSoup
import csv
from fact import Fact
import re
from settings import root_url, lang, url
from typing import List
from functions import save_urls_to_json, load_urls_from_json

def extract_facts_from_url(url:str, subject)->List:
        facts = list()
        url_visited = load_urls_from_json()
        if url not in url_visited:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    url_visited.append(url)
                    save_urls_to_json(url_visited)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    facts_list = soup.find('ul', class_='factsList')
                    if facts_list:
                        # Extraire toutes les balises <li> dans la balise <ul>
                        list_items = facts_list.find_all('li')
                        facts = list()
                        for li in list_items:
                            print()
                            text = re.sub(r'\[\d+\]', '', li.get_text(strip=True))
                            text = re.sub(r"\([^)]*\)", "", text)
                            text = re.sub(r"\.\d+", "", text)

                            print(text)
                            print()
                            fact = Fact(text=text, url_source=url, subject=subject)
                            fact.to_save()
                            facts.append(fact)
                            # Extraire le texte de chaque balise <li>
                    else:
                        print("La balise <ul> avec class='factsList' n'a pas été trouvée.")      
                else:
                    print("Error ", response.status_code)       
            except Exception as e:
                print("Problem: ", str(e))
        return facts