from google.cloud import texttospeech

url = 'https://www.factretriever.com/top10'
root_url = 'https://www.factretriever.com/'
lang = 'EN'
main_storage_file = 'storage_facts'

voice_params = {
    "language_code": "en-US",
    "name": "en-US-Neural2-D",
    "ssml_gender": "MALE"
}

audio_config_params = {
    "audio_encoding":texttospeech.AudioEncoding.MP3,
    "effects_profile_id" :['headphone-class-device'],
    "speaking_rate":1.10,
    "pitch":-5.0
}
voice_params_title = {
    "language_code": "en-US",
    "name": "en-US-Neural2-D",
    "ssml_gender": "MALE"
}

audio_config_params_title = {
    "audio_encoding":texttospeech.AudioEncoding.MP3,
    "effects_profile_id" :['headphone-class-device'],
    "speaking_rate":1.05,
    "pitch":-5.0
}


letter_width =  28
letter_heigth = 37
