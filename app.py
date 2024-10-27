import os
import streamlit as st
import yt_dlp
from deepgram import ( DeepgramClient, PrerecordedOptions, FileSource )
from openai import OpenAI
import re

def download_youtube(url,file):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': file,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def speech2text(mp3_file):
    deepgram = DeepgramClient(os.environ['DEEPGRAM_API_KEY'])
    with open(mp3_file, "rb") as file:
        buffer_data = file.read()
    payload: FileSource = {
        "buffer": buffer_data,
    }
    options = PrerecordedOptions(
        model="nova-2",
        smart_format=True,
        language="fr",
    )
    response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
    paragraphs = response['results']['channels'][0]['alternatives'][0]['paragraphs']['paragraphs']
    return "".join(sentence['text'] for sentences in paragraphs for sentence in sentences['sentences'])

def resume(text):
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    response = client.chat.completions.create(model="gpt-4o-mini",messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "résume moi ce transcript youtube sans faire une intro (il semble que le transcript, etc..), juste le résumé : "+ text}
    ])
    content = response.choices[0].message.content
    return content

st.image('logo.jpg')
st.title("download->deepgram->gtp4o")
url = st.text_input("Entres l'URL d'une vidéo youtube dont tu veux le résumé:", value="https://www.youtube.com/watch?v=gl2u16fidrk")

if st.button("Go"):
    if re.match(r"^https://www\.youtube\.com/watch\?v=[a-zA-Z0-9_-]+$", url) is not None:
        file = url.replace('https://www.youtube.com/watch?v=','') + ".mp3"
        with st.spinner('Chargement de la vidéo... Il faut juste attendre 😇'):
            download_youtube(url,file)
        with st.spinner('Okay, voyons voir..'):
            text = speech2text(file+".mp3")
            resume = resume(text)
        st.write(resume)
    else:
        st.error("L'URL doit avoir le format https://www.youtube.com/watch?v=xxxxx")
