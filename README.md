# YouTube Video Transcriber

This project is a Streamlit-based application that allows users to download audio from YouTube videos, transcribe them using OpenAI's Whisper model, and display the transcriptions with pagination.

## Features

- Download audio from YouTube videos
- Transcribe audio using OpenAI's Whisper model
- Display transcriptions with pagination
- Sanitize filenames for compatibility
- Support for CUDA acceleration (if available)

## Demo

Check out the demo of the application: [OpenAI Whisper Transcribe YouTube Videos](https://transcribeytvideos.streamlit.app/)

## Requirements

- Python 3.9+
- PyTorch
- yt-dlp
- whisper
- tiktoken
- streamlit
- FFmpeg (for audio conversion)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/RiteshGenAI/openai_whisper_transcribe_yt_videos.git
   cd openai_whisper_transcribe_yt_videos
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Install FFmpeg if it's not already on your system. Installation methods vary by operating system.

## Usage

1. Run the Streamlit app:
   ```
   streamlit run .\src\app.py
   ```

2. Enter a YouTube video URL in the provided input field.

3. The app will download the audio, transcribe it, and display the transcription with pagination.

## How it Works

1. **Download Audio**: The `download_audio` function uses yt-dlp to download the audio from the provided YouTube URL. It saves the audio as a WAV file.

2. **Transcribe Audio**: The `transcribe_audio` function uses OpenAI's Whisper model to transcribe the downloaded audio file.

3. **Display Transcript**: The `display_transcript_with_pagination` function splits the transcript into pages and displays them using Streamlit's UI components.

4. **Process Audio**: The `process_audio` function orchestrates the entire process, from downloading to transcribing and displaying the result.

## Customization

- You can change the Whisper model size by modifying the `model_name` parameter in the `transcribe_audio` function.
- Adjust the `tokens_per_page` parameter in `display_transcript_with_pagination` to change the amount of text displayed per page.

## Note

This application requires a significant amount of computational resources, especially for longer videos. Using a CUDA-enabled GPU can significantly speed up the transcription process.

## License

[MIT License](LICENSE)
