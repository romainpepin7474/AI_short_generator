import requests
from bs4 import BeautifulSoup
import csv
import re
from settings import root_url, lang
from typing import List
import os
import numpy as np
import json
from settings import letter_width, letter_heigth
from PIL import ImageFont, ImageDraw, Image
import cv2, os
from google.cloud import texttospeech
from dotenv import load_dotenv
from moviepy.editor import ImageClip, AudioFileClip
from openai import OpenAI
from settings import main_storage_file, voice_params_title, audio_config_params_title 


def extract_urls(data)->List[str]:
    """
    Extrait les urls des différents theme de fact
    """
    # Créer un objet BeautifulSoup
    soup = BeautifulSoup(data, 'html.parser')
    # Trouver tous les blocs qui ont une balise h3 enfant immédiate avec 'New' dans la classe
    url_list = list()
    for element in soup.find_all():
        # Trouver les enfants h3 immédiats
        h3_children = element.find_all('h3', recursive=False)
        for h3 in h3_children:
            classes = h3.get('class', [])
            if any('New' in class_name for class_name in classes):
                new_soup = BeautifulSoup(str(element), 'html.parser')
                a_tag = new_soup.find('a')
                href_value = a_tag.get('href')
                # Trouver la balise <h3> à l'intérieur de la balise <a>
                h3_tag = a_tag.find('h3')
                # Extraire le texte entre les balises <h3>
                h3_text = h3_tag.get_text(strip=True)
                if h3_tag and h3_text:
                    url_list.append(root_url+href_value)
                #break  # On arrête après avoir trouvé un h3 correspondant
    return url_list

def create_directory_if_not_exists(path):
    if not os.path.isdir(path):
        os.mkdir(path)
        print(f"Le dossier {path} a été créé.")
    else:
        print(f"Le dossier {path} existe déjà.")

def generate_path(class_feeling_path):
    # Lister les dossiers dans class_feeling_path
    directories = [int(d.split("_")[-1]) for d in os.listdir(class_feeling_path) if os.path.isdir(os.path.join(class_feeling_path, d)) and d !="image" and d!='audio']

    if not directories:  # Si aucun dossier n'existe
        path = os.path.join(class_feeling_path, 'fact_1')
        create_directory_if_not_exists(path)
    else:
        directories.sort(reverse=True)
        path = os.path.join(class_feeling_path, f"fact_{directories[0]+1}")
        create_directory_if_not_exists(path)
    return path

def save_urls_to_json(visited_urls, filename='visited_urls.json'):
    # Sauvegarder la liste des URLs visitées dans un fichier JSON
    with open(filename, 'w') as json_file:
        json.dump(visited_urls, json_file, indent=4)
    print(f"URLs sauvegardées dans {filename}")

def load_urls_from_json(filename='visited_urls.json'):
    """Charger les URLs visitées depuis un fichier JSON s'il existe."""
    if os.path.exists(filename):
        with open(filename, 'r') as json_file:
            return json.load(json_file)
    return []

def generated_texts(texte):
    max_nb_caracters = int(0.90*(1024//letter_width)) # letter = 27
    all_sentence = []
    sentence = []
    count = 0
    print( texte.split(" "))
    for word in texte.split(" "):
        print(word)
        if count + len(word) < max_nb_caracters:
            sentence.append(word)
            count += len(word)
        else:
            all_sentence.append(sentence)
            sentence = [word]
            count = len(word)
    all_sentence.append(sentence)
    all_sentence = [ " ".join(sentence) for sentence in all_sentence]
    print(all_sentence)
    return all_sentence

def add_text(image_path, output_path, word, police_size, position, isTitle = False):
# Charger l'image
    image = cv2.imread(image_path)
    # Convertir l'image en format compatible avec PIL
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    image_width, image_height = image_pil.size
    # Définir le texte à afficher et la police
    font_path = "police/Agdasima-Bold.ttf"  # Utilise un fichier de police TTF
    font = ImageFont.truetype(font_path, police_size)  # Taille de la police
    # Créer un objet de dessin
    draw = ImageDraw.Draw(image_pil)
    bbox_list = []
    p_x = (image_width*position[0]) 
    p_y = (image_height*position[1])    
    bbox = draw.textbbox((0, 0), word, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]    
    position_x = p_x - (text_width//2)   # Centre sur l'axe X
    position_y =  p_y + (text_height//2)  # 3ème quart de l'axe Y

    # Définir la position du texte
    position = (position_x, position_y)  # Position en pixels (x, y)
    # Couleurs
    couleur_texte = (255, 255, 255)  # Texte en blanc
    couleur_contour =  (0, 0, 0)  # Contour en noir
    # Taille du contour
    epaisseur_contour = 10
    # Ajouter le contour en dessinant plusieurs fois le texte décalé
    for x in range(-epaisseur_contour, epaisseur_contour+1):
        for y in range(-epaisseur_contour, epaisseur_contour+1):
            draw.text((position[0] + x, position[1] + y), word, font=font, fill=couleur_contour)

            # Ajouter le texte en blanc par-dessus
            draw.text(position, word, font=font, fill=couleur_texte)
    # Convertir l'image PIL de nouveau en format OpenCV
    image_finale = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
    # Enregistrer l'image avec le texte
    cv2.imwrite(output_path, image_finale)
    # Afficher l'image (optionnel)

def add_text(image_path, output_path, word, police_size, position, isTitle = False):
    # Charger l'image
    print("input path : ", image_path)
    image = cv2.imread(image_path)
    # Convertir l'image en format compatible avec PIL
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    image_width, image_height = image_pil.size
    # Définir le texte à afficher et la police
    font_path = "police/Agdasima-Bold.ttf"  # Utilise un fichier de police TTF
    font = ImageFont.truetype(font_path, police_size)  # Taille de la police
    # Créer un objet de dessin
    draw = ImageDraw.Draw(image_pil)
    bbox_list = []
    p_x = (image_width*position[0]) 
    p_y = (image_height*position[1])    
    bbox = draw.textbbox((0, 0), word, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]    
    position_x = p_x - (text_width//2)   # Centre sur l'axe X
    position_y =  p_y + (text_height//2)  # 3ème quart de l'axe Y

        # Définir la position du texte
    position = (position_x, position_y)  # Position en pixels (x, y)
    # Couleurs
    couleur_texte = (255, 0, 0)  # Texte en blanc
    couleur_contour =  (0, 0, 0)  # Contour en noir
    # Taille du contour
    epaisseur_contour = 10
    # Ajouter le contour en dessinant plusieurs fois le texte décalé
    for x in range(-epaisseur_contour, epaisseur_contour+1):
        for y in range(-epaisseur_contour, epaisseur_contour+1):
            draw.text((position[0] + x, position[1] + y), word, font=font, fill=couleur_contour)

            # Ajouter le texte en blanc par-dessus
            draw.text(position, word, font=font, fill=couleur_texte)

    # Convertir l'image PIL de nouveau en format OpenCV
    image_finale = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)

    # Enregistrer l'image avec le texte
    cv2.imwrite(output_path, image_finale)

def add_title(image_path, output_path, words, police_size, isTitle=False):
    # Charger l'image
    image = cv2.imread(image_path)
    # Convertir l'image en format compatible avec PIL
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    image_width, image_height = image_pil.size
    # Définir la police
    font_path = "police/Agdasima-Bold.ttf"  # Utilise un fichier de police TTF
    font = ImageFont.truetype(font_path, police_size)  # Taille de la police
    # Créer un objet de dessin
    draw = ImageDraw.Draw(image_pil)
    
    # Couleurs
    couleur_texte = (255, 0, 0)  # Texte en blanc
    couleur_contour = (0, 0, 0)      # Contour en noir
    epaisseur_contour = 10            # Taille du contour

    # Calculer la hauteur pour placer chaque mot
    num_words = len(words)
    margin = image_height // (num_words + 1)  # Marges pour espacer les mots

    for i, word in enumerate(words):
        # Position verticale : répartie selon le nombre de mots (i+1 pour éviter le bord supérieur)
        position_y = (i+1) * margin

        # Calcul de la position horizontale centrée
        bbox = draw.textbbox((0, 0), word, font=font)
        text_width = bbox[2] - bbox[0]
        position_x = (image_width - text_width) // 2

        # Dessiner le contour du texte pour chaque décalage de contour
        for x in range(-epaisseur_contour, epaisseur_contour + 1):
            for y in range(-epaisseur_contour, epaisseur_contour + 1):
                draw.text((position_x + x, position_y + 0.5*y), word, font=font, fill=couleur_contour)

        # Ajouter le texte en blanc par-dessus
        draw.text((position_x, position_y), word, font=font, fill=couleur_texte)

    # Convertir l'image PIL de nouveau en format OpenCV
    image_finale = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)

    # Enregistrer l'image avec le texte
    cv2.imwrite(output_path, image_finale)

def add_end(image_path, output_path, sentences, police_size, isTitle=False):

    # Charger l'image
    image = cv2.imread(image_path)
    # Convertir l'image en format compatible avec PIL
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    image_width, image_height = image_pil.size
    # Définir la police
    font_path = "police/Agdasima-Bold.ttf"  # Utilise un fichier de police TTF
    font = ImageFont.truetype(font_path, police_size)  # Taille de la police
    # Créer un objet de dessin
    draw = ImageDraw.Draw(image_pil)
    
    # Couleurs
    couleur_texte = (255, 0, 0)  # Texte en blanc
    couleur_contour = (0, 0, 0)      # Contour en noir
    epaisseur_contour = 10            # Taille du contour

    # Calculer la hauteur pour placer chaque mot
    num_words = max(len(sentences[0]), len(sentences[1]))
    margin = image_height // (num_words + 1)  # Marges pour espacer les mots
    for i, sentence in enumerate(sentences):
        # Position verticale : répartie selon le nombre de mots (i+1 pour éviter le bord supérieur)
        if i%2 == 0:

            # Calcul de la position horizontale centrée
            bbox = draw.textbbox((0, 0), sentence, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = abs(bbox[3] - bbox[1])

            position_y = (image_height//2)  - text_height

            position_x = (image_width - text_width) // 2

            # Dessiner le contour du texte pour chaque décalage de contour
            for x in range(-epaisseur_contour, epaisseur_contour + 1):
                for y in range(-epaisseur_contour, epaisseur_contour + 1):
                    draw.text((position_x + x, position_y + y), sentence, font=font, fill=couleur_contour)

            # Ajouter le texte en blanc par-dessus
            draw.text((position_x, position_y), sentence, font=font, fill=couleur_texte)
        else: 
            # Calcul de la position horizontale centrée
            bbox = draw.textbbox((0, 0), sentence, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = abs(bbox[3] - bbox[1])

            position_y = (image_height//2)  + text_height

            position_x = (image_width - text_width) // 2

            # Dessiner le contour du texte pour chaque décalage de contour
            for x in range(-epaisseur_contour, epaisseur_contour + 1):
                for y in range(-epaisseur_contour, epaisseur_contour + 1):
                    draw.text((position_x + x, position_y + y), sentence, font=font, fill=couleur_contour)

            # Ajouter le texte en blanc par-dessus
            draw.text((position_x, position_y), sentence, font=font, fill=couleur_texte)

    # Convertir l'image PIL de nouveau en format OpenCV
    image_finale = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)

    # Enregistrer l'image avec le texte
    cv2.imwrite(output_path, image_finale)

def AskOpenAI(prompt, consigne =  "You are a helpful assistant."):
    load_dotenv()
    client = OpenAI(api_key=os.getenv("API_KEY_OPENAI_USER"))
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
        {"role": "system", "content":consigne},
        {
        "role": "user",
        "content": prompt
                    }
                ]
            )
    return completion.choices[0].message.content

def AskDALLE(prompt, size="1024x1792", quality="standard"):
    load_dotenv()
    client = OpenAI(api_key=os.getenv("API_KEY_OPENAI_USER"))
    # Generate the image
    response = client.images.generate(
        model="dall-e-3",
        prompt= prompt,
        size=size,
        quality=quality,
        n=1,
    )
    # Get the image URL from the response
    image_url = response.data[0].url
    # Download the image from the URL
    image_data = requests.get(image_url).content
    return image_data

def GetAudio(texte,voice_params, audio_config_params ):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google_tts_auth.json'
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=texte)
        # Build the voice request, select the language code ("en-US") and the ssml
        # voice gender ("neutral")
        voice = texttospeech.VoiceSelectionParams(**voice_params)

            # Select the type of audio file you want returned
        audio_config = texttospeech.AudioConfig(**audio_config_params)
        response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
        )
        return response.audio_content
        # The response's audio_content is binary.

def GetAudio_OpenAI(texte, output_path):
    load_dotenv()
    api_key = os.getenv("API_KEY_OPENAI_USER")
    if not api_key:
        raise ValueError("API_KEY_OPENAI_USER n'est pas défini dans l'environnement.")
    try:
        client = OpenAI(api_key=api_key)
        response = client.audio.speech.create(
        model="tts-1-hd",
        voice="alloy",
        input=texte,
        response_format="mp3"
        )
        response.stream_to_file(output_path)
    except Exception as e:
        print(f"Erreur lors de la génération de l'audio : {e}")



def Create_Video(image_path, audio_path):
    audio_clip = AudioFileClip(audio_path)
    img_clip = ImageClip(image_path)
    # Ajuster la durée de l'image à la durée de l'audio
    video_clip = img_clip.set_duration(audio_clip.duration)
    # Ajouter l'audio à l'image
    video_clip = video_clip.set_audio(audio_clip)
    return video_clip

def FlouterPicture(image_path, output_path, kernel=(31,31)):
        print("image_path FlouterPicture", image_path)
        image = cv2.imread(image_path)
        # Appliquer un effet flou (GaussianBlur)
        blurred_image = cv2.GaussianBlur(image,kernel, 0)
        # Enregistrer l'image floue
        cv2.imwrite(output_path, blurred_image)

from pathlib import Path
if __name__ == "__main__":
    GetAudio_OpenAI("Hello, this is a test !")
    