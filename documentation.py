import requests
from bs4 import BeautifulSoup
import csv
from fact import Fact
from short import Short
import re
from settings import root_url, lang, url
from typing import List
from functions import extract_urls, save_urls_to_json, load_urls_from_json
from functions_scrap import extract_facts_from_url

##### Create a fact from a text #####
def create_fact_from_text(text,url_source,language,subject):
    fact = Fact(
        text = text,
        url_source = url_source,
        language=language,
        subject=subject
    )
    fact.to_save()
    fact.Get_Audio()
    fact.create_content()
    print("fait finalisé")
    return fact


def create_video(fact,title):
    short = Short(rush_list= [fact.path], subject= fact.subject, language=fact.language, title=title)
    short.create_short()

def create(text,url_source,language,subject,title):
    fact = create_fact_from_text(text,url_source,language,subject)
    create_video(fact,title)


if __name__ == '__main__':
    create(
        text="At the most conservative estimate there are at least 10 billion trillion stars in the universe. Red stars are relatively small and cool while the hottest burn blue-white. Stars are formed from dense knots contained in large clouds of dust and gas called nebulae.",
        url_source="https://www.factretriever.com/star-facts",
        language="EN",
        subject="star",
        title="3 Facts About Stars"
    )