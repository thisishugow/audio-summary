import os
import asyncio
import time
from uuid import uuid4
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from audio_summary.app import main
from audio_summary.server import html
import pypandoc

def _upload_file():
    """Widget for uploading a file"""
    st.file_uploader(
        "Upload file", 
        type=["txt", "md", "wav", "mp3", "m4a","mp4","mov","webm"],
        accept_multiple_files=False,
        key="src_file", 
    )

def _toggle_summarize():
    """Toggle widget for enabling or disabling summary output"""
    st.toggle(
        label="Output with summary",
        value=True,
        key="do_summarize"
    )

def _get_dump_dir():
    """Get and create file dump directory if not exists.
    
    Returns:
        str: Path to the dump directory
    """
    dump_dir = os.getenv("APP_FILE_DUMP", "file_dump")
    os.makedirs(dump_dir, exist_ok=True)
    return dump_dir

def _dump_audio(uploaded_file:UploadedFile)->str:
    """Dump the uploaded file and return the file path.

    Args:
        uploaded_file (UploadedFile): The file uploaded.

    Returns:
        str: File path of the dumped audio file.
    """
    if uploaded_file is None:
        raise FileNotFoundError('Please select a file')
    
    # 獲取並創建檔案存放目錄
    dump_dir = _get_dump_dir()
         
    rdm_name = str(uuid4())
    output_fn = os.path.join(dump_dir, f"{rdm_name}@{uploaded_file.name}")
    with open(output_fn, "wb") as f:
        f.write(uploaded_file.getvalue())

    _fn, ext = os.path.splitext(uploaded_file.name)
    if ext.lower() in [".mp4", ".webm"]:
        mp3_fn = os.path.join(dump_dir, f"{rdm_name}@{_fn}.mp3")
        os.system(f"ffmpeg -i {repr(output_fn)} -vn -ab 192k -ar 44100 -f mp3 {repr(mp3_fn)}")
        while not os.path.exists(mp3_fn):
            time.sleep(0.1)
        os.remove(output_fn)
        return mp3_fn
    return output_fn

def _output_lang():
    """Selectbox widget for choosing the output language"""
    options = [
        ("Original", "original"),
        ("ZH-TW", "zh-tw"),
        ("English", "en"),
    ]
    st.selectbox(
        "Output Language",
        options=options,
        format_func=lambda a: a[0],
        key="lang"
    )

def _duration():
    """Slider widget for setting the length (in seconds) for splitting the audio file"""

    st.slider(
        label="Length (sec) for splitting audio file ",
        value=360,
        min_value=60, 
        max_value=600,
        key="duration",
    )

def footer():
    """Footer section for the web app"""
    st.markdown(html.footer, unsafe_allow_html=True) 

def _dual_col():
    """Dual column layout for output language and duration settings"""
    col1, col2 = st.columns(2)
    with col1:
        _output_lang()
        _toggle_summarize()

    with col2:
        _duration()
        st.toggle("Use local Whisper", value=False, key="local_transcription")


def side_bar():
    """Sidebar for API configuration"""
    with st.sidebar:
        st.title("API Configure")
        st.text_input(
            label="OpenAI API Key",
            type="password", 
            key="openai_api_key",
            value=os.getenv("OPENAI_API_KEY")
        )

        st.text_input(
            label="Gemini API Key",
            type="password", 
            key="gemini_api_key",
            value=os.getenv("GOOGLE_API_KEY")
        )

def _output_container():
    """Container for displaying and downloading the transcript and summary"""
    ready_transcript = st.session_state.get('transcript', '')
    ready_summary = st.session_state.get('summary', '')
    dump_dir = _get_dump_dir()

    with st.container(border=True):
        tab_summary, tab_transcript  = st.tabs(["Summary", "Transcript", ])
        with tab_summary:
            col1, col2, _ = st.columns([1, 1, 2])
            with col1:
                md_filename = f"{st.session_state.get('src_file').name if st.session_state.get('src_file') else 'summary'}.md"
                md_path = os.path.join(dump_dir, md_filename)
                # 寫入 md 檔案
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(ready_summary)
                st.download_button("↓ Download markdown", ready_summary, md_filename, disabled=len(ready_summary)==0)
            with col2:
                output_file = f"{st.session_state.get('src_file').name if st.session_state.get('src_file') else 'summary'}.docx"
                output_path = os.path.join(dump_dir, output_file)
                pypandoc.convert_text(ready_summary, 'docx', format='md', outputfile=output_path)
                st.download_button("↓ Download docx", open(output_path, "rb").read() if len(ready_summary) > 0 else b"", output_file, disabled=len(ready_summary)==0)
            st.markdown(ready_summary)
            

        with tab_transcript:
            txt_filename = 'transcript.txt'
            txt_path = os.path.join(dump_dir, txt_filename)
            # 寫入 txt 檔案
            if len(ready_transcript) > 0:
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(ready_transcript)
            st.download_button("↓ Download", ready_transcript, txt_filename, disabled=len(ready_transcript)==0)
            st.markdown(ready_transcript)


async def run():
    """Start Web UI server

    """
    st.set_page_config(
        page_title='Audio Summary',
        layout='wide',
    )
    st.title("Audio Summary")
    side_bar()
    with st.form("main_form"):
        _upload_file()
        _dual_col()
        if_submit = st.form_submit_button("Start",)

    if if_submit:
        os.environ["GOOGLE_API_KEY"] = st.session_state.get("gemini_api_key")
        os.environ["OPENAI_API_KEY"] = st.session_state.get("openai_api_key")
        src_file:UploadedFile = st.session_state.get("src_file")
        fn = _dump_audio(src_file)
        dump_dir = _get_dump_dir()
        output_fn = os.path.join(dump_dir, f"transcript_{src_file.name}.txt")
        t0 = time.time()
        with st.spinner("work work ..."):
            transcript, summary = await main(
                fp=fn, 
                duration=st.session_state.get("duration", 600),
                lang_=st.session_state.get("lang", ("Original", "original"))[1], 
                output=output_fn,
                summarize=st.session_state.get("do_summarize", True),
                local_transcription=st.session_state.get("local_transcription", False)
            )
            st.session_state['transcript'] = transcript
            st.session_state['summary'] = summary
            await asyncio.to_thread(
                os.remove, fn
            )
        st.session_state['perf'] = time.time()-t0
    if perf:=st.session_state.get('perf', 0):    
        st.success(f"Done! ⏱️{round(perf, 2)}s.", icon="✅")

    _output_container()
    footer()
    

if __name__ == "__main__":
    asyncio.run(run())