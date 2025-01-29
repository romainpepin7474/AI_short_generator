from typing import Dict, List, Literal
from settings import main_storage_file, voice_params, audio_config_params 
import os, json, requests, time, random
from dotenv import load_dotenv
import deepl
import numpy as np
from google.cloud import texttospeech
from langdetect import detect
from transformers import pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from openai import OpenAI
from functions import create_directory_if_not_exists, generate_path, generated_texts, add_text, AskOpenAI,AskDALLE,GetAudio,Create_Video,FlouterPicture, GetAudio_OpenAI
import cv2, re
import wave
import json, time
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from moviepy.video.fx.resize import resize
from moviepy.editor import VideoFileClip, concatenate_videoclips
import keyboard
from PIL import Image

def split_paragraph_into_sentences(paragraph:str) -> str:
    """
    Divide  a paragraph in sentence based on : ".", "?", "!", et "...".
    
    :param paragraph: the paragraph to split into sentences
    :return: Une liste de phrases
    """
    # Utilisation d'une expression régulière pour diviser selon ".", "?", "!", et "..."
    sentence_endings = r'(?<=[.!?])\s+'    
    # Utiliser re.split pour diviser le texte
    sentences = re.split(sentence_endings, paragraph)
    # Filtrer les phrases vides résultant de fins de paragraphes
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]    
    return sentences

"""def processTimeStamp(data):

    json_data = json.loads(data)
    ans = list()
    for result in json_data['result']:
        ans.append((result['start'], result['end']))
    return ans"""

def DeepLTrad(text:str, target_lang:str) -> str:
    """
    translate the text into an other language set with  target_lang
    """
    load_dotenv()
    translator = deepl.Translator(os.getenv('API_KEY_DEEPL'))
    result = translator.translate_text(text, target_lang=target_lang)
    return result

class Fact():
    manuel_mod = False # Fact will not generate the picture with the GPT API but give the prompt for the user to make it himself
    def __init__(self, text:str, url_source:str, subject:str, language = None) -> None:
        self.text = text
        self.text_eng = None
        self.url_source = url_source
        self.subject = subject 
        self.language = language 
        self.feeling = None 
        self.class_feeling = None # use Local model
        self.path = None
        self.PicturePrompt = None
        self.text_per_sentence= list() # set apres la reformulation et avant de générer les audios et vidéos.
        self.image_path = None
        self.audio_path = None
        self.image_text_path = None
        self.video_path = None
        self.isused = False

    def setTextPerSentence(self):
        self.text_per_sentence = split_paragraph_into_sentences(self.text)

    def setLanguage(self):
        """
        traduit le composant self.text en Anglais US avec l'API KEY DEEPL
        et extrait la langue du text originel 
        """
        result = DeepLTrad(self.text, "EN-US")
        self.language = result.detected_source_lang
        self.text_eng = result.text

    def reformuler(self): 
        
        """
        Utilise la ChatGPT doit reformuler le fait en anglais pour parlier au droit d'auteur.
        Il faut que chaque phrases contient le sujet explicite.
        Il faudra ensuite retraduire le texte dans la langue d'origine.
        """
        
        prompt = f"Reformulate the following fact :{self.text_eng} Your answer should only contain the reformulated fact and you have to replace every personal pronouns by the real subject in your answer and every numbers have to be write in full letter."
        answer = AskOpenAI(prompt)
        self.text_eng = answer
        print("reformulate fact is :", answer)
        if self.language == "EN": # Traduire directement la formulation dans la langue du fact
            self.text = self.text_eng
        else:
            pass # traduire le fait

    def traduction(self, target_lang):
        """
        Permet de traduire le fait dans une autre langue. A revoir pour generer la vidéo short plus efficacement.
        Et fait un copie coller des éléments déja générer pour faire la video
        """
        load_dotenv()
        translator = deepl.Translator(os.getenv('API_KEY_DEEPL'))
        result = translator.translate_text(self.text, target_lang=target_lang)
        return result

    def setFeeling(self):
        """
        permet de connaitre la connoation du fait. A noter que la méthode est déjà dépassée.
        """
        prompt = f"What is the main sensational emotion we can use to illustrate {self.subject} in this fact : {self.text}. Your answer is a single adjectif"
        result = AskOpenAI(prompt)
        self.feeling  = result

    def setClassFeeling(self):
        """
        Classifer le fait brut pour produire des vidéo avec des shorts du même ton // risque de dégager
        """
        analyzer = SentimentIntensityAnalyzer()
        scores = analyzer.polarity_scores(self.text_eng)
        if scores['compound'] >= 0.00:
            self.class_feeling = 'Positive'
        elif scores['compound'] < 0.00:
            self.class_feeling = 'Negative'

    def GetPromptforDALLE3(self):
        """
        Demande à ChatGPT de générer le prompt idéal pour génerer une image avec DALLE3
        """
        prompts = []
        prompt = f"I'd like you to write the ideal prompt for dalle 3 so that it can create an eye-catching, beautiful and impressive realist image that illustrates the following subject: A {self.feeling} fact about {self.subject} ! Your answer should only contain the ideal prompt "

        for sentence in self.text_per_sentence:
            prompt_V2 = f"I'd like you to write the ideal prompt for dalle 3 so that it can create an eye-catching, beautiful and impressive realist image that illustrates the following subject:  {sentence} Your answer should only contain the ideal prompt "
            answer = AskOpenAI(prompt_V2)
            if Fact.manuel_mod:
                prompts.append(".".join([answer, "The image must be in portrait format."]))
            else:
                prompts.append(answer)
        self.PicturePrompt = prompts

    def GetPicture(self):
        """
        Permet de générer des 
        """

        # Generate the image
        self.GetPromptforDALLE3()
        if not Fact.manuel_mod:
            for i, prompt in enumerate(self.PicturePrompt):
                # Download the image from the URL
                image_path = os.path.join(self.image_path,f"image_{i+1}.png")
                if not os.path.exists(image_path):
                    image_data = AskDALLE(prompt)
                    create_directory_if_not_exists(os.path.join(self.path, "image"))
                    # Save the image to a PNG file
                    with open(image_path, "wb") as file:
                        file.write(image_data)
                    print(f"Image saved successfully as {image_path}.")
                else:
                    p = os.path.join(self.image_path,f"image_{i+1}.png")
                    print(f"Image déjà présente {p}")
        else: 
            for i, prompt in enumerate(self.PicturePrompt):
                print("##"*12)
                print("voici le sujet: ", self.text_per_sentence[i])
                print(" ")
                print("Voici le prompt a rentré : ")
                print(prompt)
                print()
                print("voici la localisation et le nom de l'image qui doit être déposée")
                print(os.path.join(self.image_path,f"image_{i+1}.png"))
                print("Appuye sur A pour continuer")
                while True:
                    touche = input("Appuyez sur la touche 'A' pour continuer : ")
                    if touche.lower() == 'a':
                        print("Touche 'A' détectée. Le programme continue.")
                        break
                # Charger l'image en format .webp
        for file_path in [f for f in os.listdir(self.image_path) if os.path.isfile(os.path.join(self.image_path, f))]:
            input_image_path = os.path.join(self.image_path, file_path)
            output_image_path = input_image_path.split(".")[0] + ".png"
            if file_path.split(".")[-1] == "webp":
            # Ouvrir l'image et la sauvegarder au format .png
                with Image.open(input_image_path) as img:
                    img.save(output_image_path, "PNG")
        print("Conversion terminée !")

    def Get_Audio(self):
        create_directory_if_not_exists(os.path.join(self.path, "audio"))
        audio_path_init = os.path.join(self.path, 'audio')
        print("text_per_sentence", self.text_per_sentence)
        for i, text in enumerate(self.text_per_sentence):
            audio_path = os.path.join(audio_path_init, f"audio_{i+1}.mp3")
            GetAudio_OpenAI(text,audio_path)
            """            
            if not os.path.exists(audio_path):
                audio_data = GetAudio(text,voice_params, audio_config_params )
                # The response's audio_content is binary.
                with open(audio_path, "wb") as out:
                    # Write the response to the output file.
                    out.write(audio_data)
                    print(f'Audio content written to file {audio_path}')
            else:
                p = os.path.join(audio_path_init, f"audio_{i+1}.mp3")
                print(f"Audio déjà créer {p}")"""

    def setPath(self):
        main_path = os.path.join(main_storage_file)
        subject_path = os.path.join(main_storage_file, self.subject)
        language_path = os.path.join(subject_path, self.language)
        class_feeling_path = os.path.join(language_path, self.class_feeling)
        for path in [main_path, subject_path, language_path, class_feeling_path]:
            create_directory_if_not_exists(path)
        new_path = generate_path(class_feeling_path)
        audio_path = os.path.join(new_path, "audio")
        create_directory_if_not_exists(audio_path)

        image_path = os.path.join(new_path, "image")
        create_directory_if_not_exists(image_path)
        image_text_path = os.path.join(new_path, "image_with_text")
        create_directory_if_not_exists(image_text_path)
        video_path = os.path.join(new_path, "video")
        create_directory_if_not_exists(video_path)

        self.path = new_path
        self.image_path = image_path
        self.audio_path = audio_path
        self.image_text_path = image_text_path
        self.video_path = video_path

    def save(self):
        # Créer le dossier si nécessaire
        directory = self.path
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Définir le chemin du fichier de sauvegarde (nom basé sur le sujet ou un autre identifiant)
        file_name = "fact.json"
        file_path = os.path.join(directory, file_name)
        text_sentence = [string.replace("-", " ").strip() for string in self.text.replace(",", ".").split(".")[:-1]]        
        self.text_per_sentence = text_sentence
        # Créer un dictionnaire avec les données de l'instance
        data = {
            "text": self.text,
            "text_eng": self.text_eng,
            "url_source": self.url_source,
            "subject": self.subject,
            "language": self.language,
            "feeling": self.feeling,
            "class_feeling": self.class_feeling,
            "path": self.path,
            "text_per_sentence" : self.text_per_sentence,
            "PicturePrompt" : self.PicturePrompt,
            "image_path" : self.image_path,
            "audio_path" : self.audio_path,
            "image_text_path" : self.image_text_path,
            "video_path" : self.video_path,

        }

        # Sauvegarder en format JSON
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

        print(f"Les données de l'instance ont été sauvegardées dans {file_path}")

    @classmethod
    def load(cls, file_path):
        # Vérifier si le fichier existe
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Le fichier {file_path} n'existe pas.")

        # Charger les données depuis le fichier JSON
        with open(file_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)

        # Recréer une instance de Fact en utilisant les données chargées
        instance = cls(
            text=data["text"],
            url_source=data["url_source"],
            language=data.get("language"),
            subject = data.get("subject")
        )
        
        # Restaurer les autres attributs
        instance.text_eng = data.get("text_eng")
        instance.feeling = data.get("feeling")
        instance.class_feeling = data.get("class_feeling")
        instance.path = data.get("path")
        instance.text_per_sentence = data.get("text_per_sentence")
        instance.image_path = data.get("image_path")
        instance.audio_path = data.get("audio_path")
        instance.image_text_path = data.get("image_text_path")
        instance.video_path = data.get("video_path")
        instance.isused = data.get("isused")
        print(f"L'instance de Fact a été chargée depuis {file_path}")
        return instance

    def to_save(self):
        self.setLanguage()
        print(" self.setLanguage() done ")
        self.setFeeling()
        print(" self.setFeeling() done ")
        self.setClassFeeling()
        print(" self.setClassFeeling() done ")
        self.setPath()
        print(" self.setPath() done ")
        self.reformuler()
        print("self.reformuler() done")
        self.save()
        print(" self.save() done ")

    def process(self):
        self.GetPicture()
        self.save()

    def create_content(self):
        print("Avant self.GetPicture()")
        self.GetPicture()
        print("Après self.GetPicture()")
        print("Avant self.FlouterPictures()")
        self.FlouterPictures()
        print("Après self.FlouterPictures()")
        print("Avant self.Ajouter_text_image()")
        self.Ajouter_text_image()
        print("Après self.Ajouter_text_image()")
        print("Avant self.create_video()")
        self.create_video()
        print("Après self.create_video()")
        print("Avant self.merge_video()")
        self.merge_video()
        print("Après self.merge_video()")

    def FlouterPictures(self):
        fichiers_png = [f for f in os.listdir(self.image_path) if f.endswith('.png')]
        fichiers_png.sort()
        for  i,fichier in enumerate(fichiers_png):
            image_p = os.path.join(self.image_path,fichier)
            print(image_p)
            output = os.path.join(self.image_path,f'image_floue_{i+1}.png')
            FlouterPicture(image_p, output, kernel=(151,151))

    def Ajouter_text_image(self):
        
        position  = (0.5,0.75)
        image_text_path = os.path.join(self.path, "image_with_text")

        for i, sentence in enumerate(self.text_per_sentence):
            # create a directory
            image_path = os.path.join(self.image_path, f"image_{i+1}.png")
            for j, word in enumerate(sentence.split(" ")):
                police_size = 100
                if police_size <= 20:
                    police_size = 120
                path = os.path.join(image_text_path, f"image_with_text_{i+1}_{j+1}.png")
                add_text(image_path, path, word.upper(), police_size, position)

    def extract_time_code(self, audio_input):
        audio = AudioSegment.from_mp3(audio_input)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export("temp_audio.wav", format="wav")
        model = Model(lang="en-us")    
        # Ouvrir le fichier audio
        wf = wave.open("temp_audio.wav", "rb")
        if wf.getnchannels() != 1:
            raise ValueError("Le fichier audio doit être mono pour fonctionner avec Vosk")
        if wf.getsampwidth() != 2 or wf.getframerate() != 16000:
            raise ValueError("Le fichier audio doit être 16 kHz et 16 bits pour fonctionner avec Vosk")
        # Extraire les résultats avec les time codes
        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                rec.Result()
            else:
                rec.PartialResult()
        os.remove("temp_audio.wav")
        return processTimeStamp(rec.FinalResult())

    def create_video_from_images_and_audio(self,image_files, timecodes, audio_file, output_file, resolution=(1024, 1792)):
        """
        Crée une vidéo à partir d'une liste d'images, des timecodes pour chaque image et un fichier audio.
        
        :param image_files: Liste des chemins d'images
        :param timecodes: Liste des tuples (début, fin) en secondes pour chaque image
        :param audio_file: Chemin vers le fichier audio
        :param output_file: Chemin vers le fichier vidéo de sortie
        :param resolution: Résolution de la vidéo (largeur, hauteur)
        """
        clips = []
        
        # Charger l'audio
        audio = AudioFileClip(audio_file)

        # Créer des clips d'image avec les timecodes associés
        for idx, (image_file, (start_time, end_time)) in enumerate(zip(image_files, timecodes)):
            # Charger l'image
            img_clip = ImageClip(image_file).set_duration(end_time - start_time)
            img_clip = resize(img_clip, newsize=resolution)  # Redimensionner l'image à la résolution voulue
            img_clip = img_clip.set_start(start_time)  # Définir le début de l'image selon le timecode
            clips.append(img_clip)
        clips[-1] = clips[-1].set_duration(clips[-1].duration + 0.2)
        # Combiner les clips d'image dans une seule vidéo
        video = concatenate_videoclips(clips, method="compose")
        
        # Ajouter l'audio à la vidéo
        final_video = video.set_audio(audio)
        
        # Exporter la vidéo finale
        final_video.write_videofile(output_file, fps=30)

    def create_video(self):
        audio_paths = sorted([os.path.join(self.audio_path,d) for d in os.listdir(self.audio_path) ])
        for i, audio_path in enumerate(audio_paths):
            image_paths = sorted([os.path.join(self.image_text_path,d)  for d in os.listdir(self.image_text_path) if f"image_with_text_{i+1}" in d], key=lambda x: int(x.split('_')[-1].split('.')[0]))
            print("audio_path", audio_path)
            timescodes = self.extract_time_code(audio_path)
            create_directory_if_not_exists(self.video_path)
            self.create_video_from_images_and_audio(image_paths, timescodes, audio_path, os.path.join(self.video_path,f"video_temp_{i+1}.mp4") )

    def merge_video(self):
        # Liste pour stocker les clips vidéo
        video_clips = []
        # Parcourir tous les fichiers du répertoire
        for filename in sorted(os.listdir(self.video_path)):
            if filename.endswith(('.mp4', '.avi', '.mov', '.mkv')) and 'temp' in filename:  # Vérifie si c'est un fichier vidéo
                file_path = os.path.join(self.video_path, filename)
                print(f"Ajout de la vidéo : {file_path}")
                
                # Charger la vidéo et l'ajouter à la liste
                clip = VideoFileClip(file_path)
                video_clips.append(clip)
        
        if len(video_clips) == 0:
            print("Aucune vidéo trouvée dans le répertoire.")
                
        else:   
            # Fusionner tous les clips
            video_concat = concatenate_videoclips(video_clips, method="compose")
            
            # Exporter la vidéo fusionnée
            video_concat.write_videofile(os.path.join(self.video_path, "video_final.mp4"), fps=30)

if __name__ == '__main__':
    fact = Fact.load("storage_facts/emu/EN/Negative/fact_1/fact.json")
    fact.to_save()


