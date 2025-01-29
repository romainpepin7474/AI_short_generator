from typing import Dict, List, Literal
import os, json, random
import json
from moviepy.editor import VideoFileClip, concatenate_videoclips
from datetime import datetime
from fact import Fact
from functions import AskOpenAI,AskDALLE,GetAudio,GetAudio_OpenAI,Create_Video,FlouterPicture, create_directory_if_not_exists, generate_path, generated_texts, add_title, add_end
from moviepy.editor import ImageClip
from settings import voice_params_title, audio_config_params_title
import keyboard

adjectif_list = ["terrifying", "wonderful", "breathtaking", "magnificient"] ### permet de génerer une image d'intro
class Short():
    manuel_mod = False
    def __init__(self, rush_list = None, title = None, subject= None, intro = None ,  EndMessage = None, language = None):
        self.rush_list = rush_list # On fournit la liste qu'on veut 
        self.intro = intro
        self.title = title
        self.EndMessage = EndMessage
        self.prompt_for_intro = None
        self.path = None
        self.subject = subject
        self.language = language
        self.output_short = "final_short"

    # Le but est de créer un short de toute pièce 
    # Le title peut être renseigner par une path, comme les facts et le end message
    def setPath(self):
        date_heure_actuelles = datetime.now()
        date_heure_actuelles = date_heure_actuelles.strftime("%Y-%m-%d-%H-%M-%S")
        main_path = os.path.join("storage_short")
        language_path = os.path.join(main_path, self.language)
        subject_path = os.path.join(language_path, self.subject)
        short_path = os.path.join(subject_path, date_heure_actuelles)
        for path in [main_path, language_path, subject_path,short_path]:
            create_directory_if_not_exists(path)
        self.path = short_path
        
    def GetPromptforDALLE3_Intro(self):
        """
        Demande à ChatGPT de générer le prompt idéal pour génerer une image avec DALLE3
        """
        adjectif_list = ["terrifying", "wonderful", "breathtaking" , "horrific", "magnificient"] ### permet de génerer une image d'intro
        adjectif = random.choice(adjectif_list)
        prompt = f"I'd like you to write the best prompt for dalle 3 so that it can create an eye-catching, \
        beautiful and impressive realist image that illustrates the following subject: A {adjectif}  {self.subject} ! Your answer should only contain the ideal prompt"
        answer = AskOpenAI(prompt)
        self.prompt_for_intro = answer
    
    def GetPicture(self):
        """                    
        Permet de générer des                
        """
        image_intro_path = os.path.join(self.path,"image_intro.png")
        image_end_path = os.path.join(self.path,"image_end.png")

        if not os.path.exists(image_intro_path):
            self.GetPromptforDALLE3_Intro()
            image_end_path = os.path.join(self.path,"image_end.png")
            if not Fact.manuel_mod:
                image_data = AskDALLE(self.prompt_for_intro, size="1024x1792", quality="standard")
                # Save the image to a PNG file
                image_intro_path = os.path.join(self.path,"image_intro.png")

                with open(image_intro_path, "wb") as file:
                    file.write(image_data)
            else :
                print("##"*12)
                print("Voici le prompt a rentré : ")
                print(self.prompt_for_intro)
                print()
                print("voici la localisation et le nom de l'image qui doit être déposée")
                print(os.path.join(self.path,"image_intro.png"))
                print("Appuye sur A pour continuer")
                while True:
                    touche = input("Appuyez sur la touche 'A' pour continuer : ")
                    if touche.lower() == 'a':
                        print("Touche 'A' détectée. Le programme continue.")
                        break

            # print(f"Image saved successfully as {image_path}.")
            FlouterPicture(image_intro_path, image_end_path, kernel=(31,31))
        if not os.path.exists(image_end_path):
            FlouterPicture(image_intro_path, image_end_path, kernel=(31,31))


    def GetAudio_Intro(self):
        path = os.path.join(self.path,"audio_intro.mp3")
        GetAudio_OpenAI(self.title, path)
 

    def Ajouter_text_image_intro(self,image_path, output_path, text=None):
        position  = (0.5,0.65)
        police_size = 120
        if text is None:
            add_title(image_path, output_path, self.title.split(" "), police_size, position)
        else:
            add_title(image_path, output_path, text.split(" "), police_size, position)


    """   
    Déprecier car le formatage du texte de fin et différente de celui de l'intro 
        def Ajouter_text_image_end(self,image_path, output_path, text):
            position  = (0.5,0.65)
            police_size = 120
            add_title(image_path, output_path, text, police_size, position)
    """
    def create_video_intro(self,resolution=(1024,1792)):
            image_path = os.path.join(self.path, "image_intro.png")
            output_path = os.path.join(self.path, "temp_image_with_text.png")
            self.Ajouter_text_image_intro(image_path, output_path)
            image_path = os.path.join(self.path,"temp_image_with_text.png")
            audio_path = os.path.join(self.path, "audio_intro.mp3")
            video_clip = Create_Video(image_path, audio_path)
            video_clip.write_videofile(os.path.join(self.path,"temp_intro.mp4"), fps=30)

    def CreateIntro(self):
        
        self.GetAudio_Intro()
        self.GetPicture()
        self.create_video_intro()

        # Fait le text de la subscription 

    def save(self):
        # Créer le dossier si nécessaire
        directory = self.path
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Définir le chemin du fichier de sauvegarde (nom basé sur le sujet ou un autre identifiant)
        file_name = "short.json"
        file_path = os.path.join(directory, file_name)

        # Créer un dictionnaire avec les données de l'instance
        data = {
        "rush_list":self.rush_list, # On fournit la liste qu'on veut 
        "intro":self.intro,
        "title"  :self.title ,
        "EndMessage"  :self.EndMessage, 
        "prompt" :self.prompt,
        "path" :self.path,
        "subject" :self.subject,
        "language"  :self.language
        }

        # Sauvegarder en format JSON
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

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
        )
        # Restaurer les autres attributs
        instance.rush_list = data.get("rush_list")
        instance.intro = data.get("intro")
        instance.title = data.get("title")
        instance.EndMessage = data.get("EndMessage")
        instance.prompt = data.get("prompt")
        instance.path = data.get("path")
        instance.subject = data.get("subject")
        instance.language = data.get("language")
        instance.output_short = "final_short"

        print(f"L'instance de Fact a été chargée depuis {file_path}")
        return instance


    def endAudio(self):
        message_1 = f"AND YOU ?..."
        message_2 = f"DO YOU KNOW OTHER {self.subject.upper()} FACT ?"
        message_3 = f"Don't forget to LIKE, SHARE AND SUBSCRIBE"
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google_tts_auth.json'
        # Build the voice request, select the language code ("en-US") and the ssml
        # voice gender ("neutral")
        for i, message in enumerate([message_1,message_2,message_3]):
            output_file= os.path.join(self.path, f"temp_audio_end_{i+1}.mp3")
            GetAudio_OpenAI(message, output_file)

    def endMessage(self):
        message_1 = f"AND YOU ?"
        message_2 = f"DO YOU KNOW OTHER {self.subject.upper()} FACT ?"
        message_3 = f"LIKE SHARE & SUBSCRIBE"
        image_path = os.path.join(self.path, "image_end.png")
        for i, message in zip([1, 3], [message_1, message_3]):
            output_path = os.path.join(self.path, f"end_image_temp_{i}.png")
            position  = (0.5,0.75)
            police_size = 120
            print(image_path)
            add_title(image_path, output_path, message.split(" "), police_size, position)
        message_2 =["DO YOU KNOW OTHER",f"{self.subject.upper()} FACT ?"]
        output_path = os.path.join(self.path, "end_image_temp_2.png")
        position  = (0.5,0.75)
        police_size = 100
        add_end(image_path, output_path, message_2, police_size, position)

    def create_end_video(self):

        image_file = sorted([os.path.join(self.path,f) for f in os.listdir(self.path) if 'end_image_temp_' in f], key= lambda x: x.split("_")[-1].split(".")[0])
        audio_file = sorted([os.path.join(self.path,f) for f in os.listdir(self.path) if 'temp_audio_end_' in f], key= lambda x: x.split("_")[-1].split(".")[0])
        video_clips = []
        
        for audio, image in zip(audio_file,image_file):
            video_clip = Create_Video(image, audio)
            video_clips.append(video_clip)
        final_video = concatenate_videoclips(video_clips)
        final_video.write_videofile(os.path.join(self.path,"temp_end.mp4"), fps=30)

    def getFactVideo(self, audio_text, video_text, image_flou_path ):
        # Créate the audio
        output_audio =  os.path.join(self.path, "fact.mp3")
        GetAudio_OpenAI(audio_text, output_audio)       
        # Créate the image 
        img_floue = ImageClip(image_flou_path)
        output_img = os.path.join(self.path, "fact.png")
        self.Ajouter_text_image_intro(image_flou_path, output_img ,video_text)
        # fusionner les images
        video_clip = Create_Video(output_img, output_audio) 
        return video_clip
    
    def create_final_short(self):
        # example d'un element de self.rush_list storage_facts/emu/EN/Negative/fact_1
        intro = os.path.join(self.path, "temp_intro.mp4")
        end = os.path.join(self.path, "temp_end.mp4")
        intro_video = VideoFileClip(intro)
        end_video = VideoFileClip(end)
        if len(self.rush_list) > 1:
            # créer les images d'intro
            video_clips = [intro_video]
            for i, fact_path in enumerate(self.rush_list):
                video_path = os.path.join(fact_path,"video","video_final.mp4")
                image_flou_path  = os.path.join(fact_path, "image", "image_floue_1.png")
                audio_text = f"Fact number {i+1}"
                text = f"Fact {i+1}"
                fact_clip = self.getFactVideo(audio_text, text, image_flou_path)
                video_clips.append(fact_clip)
                video_clips.append(VideoFileClip(video_path))
            video_clips.append(end_video)
            max_height = max([video.h for video in video_clips])
            video_clips = [ video.resize(height=max_height) for video in video_clips]
            final_video = concatenate_videoclips(video_clips)
            final_video.write_videofile(os.path.join(self.path,"final_video.mp4"), fps=30)
            return 
                
        if len(self.rush_list) == 1:
            print(self.rush_list[0])
            video_path = os.path.join(self.rush_list[0],"video","video_final.mp4")
            fact_video = VideoFileClip(video_path)
            max_height = max(intro_video.h, fact_video.h, end_video.h)
            # Redimensionner les clips pour qu'ils correspondent à la taille maximale 
            # tout en conservant leurs proportions
            intro_video = intro_video.resize(height=max_height)
            fact_video = fact_video.resize(height=max_height)
            end_video = end_video.resize(height=max_height)
            final_video = concatenate_videoclips([intro_video, fact_video, end_video], method="compose")
            # Merge l'intro, le fait et le end
            final_video.write_videofile(os.path.join(self.path,"final_video.mp4"), fps=30)
        return 

    def CreateEnd(self):
        self.endMessage()
        self.endAudio()
        self.create_end_video()

    def create_short(self):
        self.setPath()
        self.CreateIntro()
        self.CreateEnd()
        self.create_final_short()
        
        pass



if __name__ == '__main__':

    short = Short.load("storage_short/EN/Emu/2024-10-21-21-28-11/short.json")
    short.create_short()

    """intro = VideoFileClip(os.path.join(short.path, "temp_intro.mp4"))
    end = VideoFileClip(os.path.join(short.path, "temp_end.mp4"))
    fact = Fact.load("storage_facts/emu/EN/Negative/fact_1/fact.json")
    fact_clip = VideoFileClip(os.path.join(fact.video_path, "video_final.mp4"))
    # Trouver la taille maximale (largeur, hauteur) parmi les vidéos
    max_width = max(intro.w, fact_clip.w, end.w)
    max_height = max(intro.h, fact_clip.h, end.h)

    # Redimensionner les clips pour qu'ils correspondent à la taille maximale tout en conservant leurs proportions
    intro = intro.resize(height=max_height)
    fact_clip = fact_clip.resize(height=max_height)
    end = end.resize(height=max_height)

    final_clip = concatenate_videoclips([intro, fact_clip, end], method="compose")
    # Sauvegarde du résultat
    final_clip.write_videofile("merged_horizontal_video.mp4")"""

"""
Le message de fin comportortera l'image du début avec un peu de flou un premier text qui dit 
Connais tu d'autre emu fact ? 
et le seconde Like, Share & Subscribe
"""