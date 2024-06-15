import os
import asyncio
import time
from uuid import uuid4
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from audio_summary.app import main
from audio_summary.server import html



def _upload_file():
    """widget of uploading file
    """
    st.file_uploader(
        "Upload file", 
        type=["txt", "md", "wav", "mp3", ],
        accept_multiple_files=False,
        key="src_file", 
    )

def _toggle_summarize():
    st.toggle(
        label="Output with summary",
        value=True,
        key="do_summarize"
    )

def _dump_audio(uploaded_file:UploadedFile)->str:
    """Dump the uploaded file and return path. 

    Args:
        uploaded_file (UploadedFile): The file uploaded. 

    Returns:
        str: file path
    """
    rdm_name = str(uuid4())
    output_fn = f"{rdm_name}@{uploaded_file.name}"
    with open(output_fn, "wb") as f:
        f.write(uploaded_file.getvalue())
    return output_fn

def _output_lang():
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
    st.slider(
        label="Length (sec) for splitting audio file ",
        value=360,
        min_value=60, 
        max_value=600,
        key="duration",
    )

def footer():
    st.markdown(html.footer, unsafe_allow_html=True) 

def _dual_col():
    col1, col2 = st.columns(2)
    with col1:
        _output_lang()
    with col2:
        _duration()


async def run():
    """Start Web UI server

    """
    st.set_page_config(
        page_title='Audio Summary'
    )
    st.title("Audio Summary")

    with st.form("main_form"):
        _upload_file()
        _dual_col()
        _toggle_summarize()
        if_submit = st.form_submit_button("Start")
    
    transcription:str = None
    perf:float = 0
    if if_submit:
        src_file:UploadedFile = st.session_state.get("src_file")
        fn = _dump_audio(src_file)
        output_fn = f"transcription_{src_file.name}.txt"
        t0 = time.time()
        with st.spinner("work work ..."):
            transcription, summary = await main(
                fp=fn, 
                duration=st.session_state.get("duration", 600),
                lang_=st.session_state.get("lang", ("Original", "original"))[1], 
                output=output_fn,
                summarize=st.session_state.get("do_summarize", True)
            )
            await asyncio.to_thread(
                os.remove, fn
            )
        t1 = time.time()
        perf = t1-t0
    if transcription:
        st.success(f"Done! ⏱️{round(perf, 2)}s.", icon="✅")
        tab_summary, tab_transcription  = st.tabs(["Summary", "Transcription", ])
        with tab_summary:
            st.markdown(summary)

        with tab_transcription:
            st.markdown(transcription)
    
    footer()
    


if __name__ == "__main__":
    asyncio.run(run())