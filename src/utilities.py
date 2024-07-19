import os
import re
import math
import torch
import yt_dlp
import whisper
import tiktoken
import streamlit as st

def sanitize_filename(filename):
    sanitized = re.sub(r'[\\/*?:"<>|\'"\t!]+', "_", filename)
    sanitized = re.sub(r'[\s_-]+', '_', sanitized)
    sanitized = sanitized.strip('_')
    return sanitized[:200]

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def download_audio(url):
    audio_dir = os.path.join('data', 'audio')
    ensure_dir(audio_dir)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(audio_dir, '%(title)s.%(ext)s'),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # First, just extract the info without downloading
        info = ydl.extract_info(url, download=False)
        video_title = info['title']
        safe_title = sanitize_filename(video_title)
        original_webm_file = os.path.join(audio_dir, f"{video_title}.webm")
        original_wav_file = os.path.join(audio_dir, f"{video_title}.wav")
        safe_webm_file = os.path.join(audio_dir, f"{safe_title}.webm")
        safe_wav_file = os.path.join(audio_dir, f"{safe_title}.wav")

        if os.path.exists(safe_wav_file):
            print(f"{safe_wav_file} already exists. Skipping download.")
            return safe_wav_file

        if os.path.exists(safe_webm_file):
            print(f"{safe_webm_file} exists, but {safe_wav_file} doesn't. Converting to WAV...")
            os.system(f"ffmpeg -i \"{safe_webm_file}\" -acodec pcm_s16le -ar 44100 \"{safe_wav_file}\"")
            return safe_wav_file

        print("Downloading audio...")
        ydl.download([url])

        # Rename files if they exist with original names
        if os.path.exists(original_webm_file):
            os.rename(original_webm_file, safe_webm_file)
        if os.path.exists(original_wav_file):
            os.rename(original_wav_file, safe_wav_file)

        if not os.path.exists(safe_wav_file):
            raise FileNotFoundError(f"Could not find downloaded file for {safe_title}")

    return safe_wav_file

def transcribe_audio(audio_file, model_name="base"):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    model = whisper.load_model(model_name).to(device)
    result = model.transcribe(audio_file, fp16=False)
    return result["text"]

@st.experimental_fragment
def display_transcript_with_pagination(transcript_file, tokens_per_page=1000):
    # Read the transcript
    with open(transcript_file, "r", encoding="utf-8") as f:
        transcript = f.read()
    
    # Initialize the tiktoken encoder
    encoder = tiktoken.get_encoding("cl100k_base")  # You can change this to the appropriate encoding
    
    # Split the transcript into sentences
    sentences = re.split(r'(?<=[.!?])\s+', transcript)
    
    # Encode each sentence and keep track of token counts
    encoded_sentences = []
    token_counts = []
    for sentence in sentences:
        encoded = encoder.encode(sentence)
        encoded_sentences.append(encoded)
        token_counts.append(len(encoded))
    
    # Calculate page boundaries
    page_boundaries = [0]
    current_count = 0
    for i, count in enumerate(token_counts):
        if current_count + count > tokens_per_page:
            page_boundaries.append(i)
            current_count = count
        else:
            current_count += count
    page_boundaries.append(len(sentences))
    
    # Calculate the number of pages
    pages = len(page_boundaries) - 1
    
    # Add a page selector
    page = st.selectbox("Select page", range(1, pages + 1))
    
    # Display the selected page
    start_index = page_boundaries[page - 1]
    end_index = page_boundaries[page]
    page_sentences = sentences[start_index:end_index]
    page_content = " ".join(page_sentences)
    
    col1, col2, col3 = st.columns([0.6, 5,  0.5])
    with col2:
        st.markdown(f"**Page {page} of {pages}**")
        st.markdown(f'<div style="text-align: justify; padding-bottom: 20px;">{page_content}</div>', unsafe_allow_html=True)

def process_audio(video_url):
    audio_file = download_audio(video_url)
    st.chat_message("Assistant", avatar="👩‍🏫").write(f"Audio file downloaded: {audio_file}")
    st.session_state.messages.append({"role": "Assistant", "content": f"Audio file downloaded: {audio_file}"})

    # Transcribe audio
    with st.spinner("Transcribing audio file..."):
        transcript_dir = os.path.join('data', 'transcribed_text')
        ensure_dir(transcript_dir)
        transcript_file = os.path.join(transcript_dir, f"{os.path.splitext(os.path.basename(audio_file))[0]}_transcript.txt")
        
        if os.path.exists(transcript_file):
            file_exist = f"Transcript file already exists:\n\n**{transcript_file}**\n\n Skipping transcription."
            st.chat_message("Assistant", avatar="👩‍🏫").write(file_exist)
            st.session_state.messages.append({"role": "Assistant", "content": file_exist})
        else:
            transcript = transcribe_audio(audio_file)
            
            # Write the transcript to the file
            with open(transcript_file, "w", encoding="utf-8") as f:
                f.write(transcript)

            transcript_done = f"Transcription complete! Saved to location:\n\n**{transcript_file}**\n\nDisplaying transcript:"
            st.chat_message("Assistant", avatar="👩‍🏫").write(transcript_done)
            st.session_state.messages.append({"role": "Assistant", "content": transcript_done})

        # Display the transcript with pagination
        display_transcript_with_pagination(transcript_file)
        