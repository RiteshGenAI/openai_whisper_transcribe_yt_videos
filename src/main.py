import utilities as ut
import streamlit as st

if 'login_username' not in st.session_state:
    st.session_state.login_username=[]
if 'signup_username' not in st.session_state:
    st.session_state.signup_username=[]
if 'signup_email' not in st.session_state:
    st.session_state.signup_email=[]

def main():
    st.set_page_config(
        page_title="YouTube Video Transcription",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    with open("./css/theme.txt", "r") as css_file:
        css = css_file.read()

    css_styling=f"""{css}"""
    st.markdown(css_styling, unsafe_allow_html=True)
    
    st.markdown("""<h2 style='text-align: center; color: #111111; margin-top: 10px;'>Youtube Video Transcriber</h2>""", unsafe_allow_html=True)

    video_url = st.chat_input(placeholder="Please Enter The Youtube Link to be Transcribed...")

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "Assistant", "content": "👋Hello! I am Your Transcriptor! Enter the Link to Transcribe!"}]
    
    for msg in st.session_state.messages:
        if "Assistant" in msg["role"]:
            st.chat_message(msg["role"], avatar="👩‍🏫").write(msg["content"])
        else:
            st.chat_message(msg["role"], avatar="🧑‍🎓").write(msg["content"])
    if video_url:
        try:
            ut.process_audio(video_url)
            # Uncomment the following line if you want to remove the original audio file
            # os.remove(audio_file)

        except Exception as e:
            print(f"An error occurred: {str(e)}")

    else:
        st.warning("Please enter a YouTube video URL")

if __name__=="__main__":
    main()
