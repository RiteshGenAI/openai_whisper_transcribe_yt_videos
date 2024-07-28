import os
import re
import torch
import yt_dlp
import whisper
import tiktoken
import streamlit as st

def sanitize_filename(filename):
    # Replace invalid characters with an underscore
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', filename)
    # Replace spaces with underscores
    sanitized = re.sub(r'\s+', '_', sanitized)
    # Remove any non-ASCII characters
    sanitized = re.sub(r'[^\x00-\x7F]+', '', sanitized)
    # Remove leading and trailing underscores
    sanitized = sanitized.strip('_')
    # Ensure the filename is not empty
    if not sanitized:
        sanitized = "unnamed_file"
    # Trim the filename to 200 characters
    return sanitized[:200]

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

@st.cache_data(show_spinner=False)
def download_audio(url):
    audio_dir = os.path.join('data', 'audio')
    ensure_dir(audio_dir)

    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info['title']
            safe_title = sanitize_filename(video_title)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(audio_dir, f'{safe_title}.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
            # Find the downloaded file
            downloaded_files = [f for f in os.listdir(audio_dir) if f.lower().endswith('.wav')]
            print(f"Files in directory: {downloaded_files}")  # Debugging information
            
            if not downloaded_files:
                raise FileNotFoundError(f"Could not find any audio files in {audio_dir}")

            # Check for the correct file with sanitized name
            expected_file = f"{safe_title}.wav"
            if expected_file in downloaded_files:
                downloaded_file = os.path.join(audio_dir, expected_file)
            else:
                raise FileNotFoundError(f"Expected file {expected_file} not found in {audio_dir}")

            print(f"Selected file: {downloaded_file}")  # Debugging information

            return downloaded_file
    except Exception as e:
        print(f"An error occurred while downloading/processing the audio: {str(e)}")
        raise

def load_whisper_model(model_name="base"):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return whisper.load_model(model_name).to(device)

def transcribe_audio(_model, audio_file):
    result = _model.transcribe(audio_file, fp16=False)
    return result["text"]

def process_transcript(transcript_file, tokens_per_page=1000):
    with open(transcript_file, "r", encoding="utf-8") as f:
        transcript = f.read()
    
    encoder = tiktoken.get_encoding("cl100k_base")
    sentences = re.split(r'(?<=[.!?])\s+', transcript)
    
    encoded_sentences = []
    token_counts = []
    for sentence in sentences:
        encoded = encoder.encode(sentence)
        encoded_sentences.append(encoded)
        token_counts.append(len(encoded))
    
    page_boundaries = [0]
    current_count = 0
    for i, count in enumerate(token_counts):
        if current_count + count > tokens_per_page:
            page_boundaries.append(i)
            current_count = count
        else:
            current_count += count
    page_boundaries.append(len(sentences))
    
    pages = len(page_boundaries) - 1
    
    return sentences, page_boundaries, pages

@st.experimental_fragment
def display_transcript_with_pagination(transcript_file, tokens_per_page=1000):
    sentences, page_boundaries, pages = process_transcript(transcript_file, tokens_per_page)
    
    page = st.selectbox("Select page", range(1, pages + 1))
    
    start_index = page_boundaries[page - 1]
    end_index = page_boundaries[page]
    page_sentences = sentences[start_index:end_index]
    page_content = " ".join(page_sentences)
    
    col1, col2, col3 = st.columns([0.6, 5,  0.5])
    with col2:
        st.markdown(f"**Page {page} of {pages}**")
        st.markdown(f'<div style="text-align: justify; padding-bottom: 20px;">{page_content}</div>', unsafe_allow_html=True)

def process_audio(video_url):
    try:
        # Download and process the audio file
        with st.spinner("Downloading audio file..."):
            audio_file = download_audio(video_url)
            st.chat_message("Assistant", avatar="👩‍🏫").write(f"Audio file downloaded: {audio_file}")
            st.session_state.messages.append({"role": "Assistant", "content": f"Audio file downloaded: {audio_file}"})

        with st.spinner("Transcribing audio file..."):
            # Ensure the transcript directory exists
            transcript_dir = os.path.join('data', 'transcribed_text')
            ensure_dir(transcript_dir)
            
            # Define the transcript file path
            transcript_file = os.path.join(transcript_dir, f"{os.path.splitext(os.path.basename(audio_file))[0]}_transcript.txt")
            
            if os.path.exists(transcript_file):
                file_exist = f"Transcript file already exists:\n\n**{transcript_file}**\n\nSkipping transcription."
                st.chat_message("Assistant", avatar="👩‍🏫").write(file_exist)
                st.session_state.messages.append({"role": "Assistant", "content": file_exist})
            else:
                # Load the Whisper model
                model = load_whisper_model()

                # Transcribe the audio file
                transcript = transcribe_audio(model, audio_file)
                
                # Save the transcript to a file
                with open(transcript_file, "w", encoding="utf-8") as f:
                    f.write(transcript)

                transcript_done = f"Transcription complete! Saved to location:\n\n**{transcript_file}**\n\nDisplaying transcript:"
                st.chat_message("Assistant", avatar="👩‍🏫").write(transcript_done)
                st.session_state.messages.append({"role": "Assistant", "content": transcript_done})

            # Display the transcript with pagination
            display_transcript_with_pagination(transcript_file)
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        st.error(error_message)
        st.session_state.messages.append({"role": "Assistant", "content": error_message})
