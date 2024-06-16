import argparse
import os
import sys
import time
from string import Template
import math
import textwrap
import shutil
from typing import Literal
import asyncio

import librosa
from openai import AsyncOpenAI
from openai.types.audio import Transcription
import google.generativeai as genai

from audio_summary.exceptions import GeminiSummarizedFailed, OpenaiApiKeyNotFound
from audio_summary.api_utils import *
import audio_summary.prompts.lang as lang

__WHISPER_CONTENT_LIMIT_IN_BYTES:int = 26214400

lang_map:dict[str, str] = {
    "original": lang.ORIGINAL,
    "zh-tw": lang.ZH_TW,
    "en": lang.EN,
}

def split_audio(
    fn: str, duration: float = 600, output_dir: str = "./.tmp_audio"
) -> list[str]:
    """
    Split an audio file into segments.

    Args:
        fn (str): Path to the input audio file.
        duration (float, optional): Duration of each segment in seconds. Defaults to 600.
        output_dir (str, optional): Output directory to save the segmented audio files. Defaults to "./.tmp_audio".

    Raises:
        RuntimeError: Raised if ffmpeg execution fails.

    Returns:
        list[str]: List of paths to the segmented audio files.
    """
    duration = float(duration)
    ffmpeg_exec = "ffmpeg"
    cmd = Template(
        (
            f"{ffmpeg_exec} "
            f"-i \"{fn}\" "
            f"-vn -acodec copy "
            f"-ss $start_time "
            f"-t {duration} "
            f"\"$output\" "
        )
    )

    total_len: float = librosa.get_duration(path=fn)
    results = []

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if os.path.isfile(output_dir):
        os.makedirs(output_dir)

    for i in range(math.ceil(total_len / duration)):
        b_fn, ext = os.path.splitext(os.path.basename(fn))
        o_fn = f"{b_fn}_{i+1}{ext}"
        full_o_fn = os.path.join(output_dir, o_fn)
        start_time = i * duration
        exec = cmd.substitute(
            {
                "start_time": start_time,
                "output": full_o_fn,
            }
        )
        res = os.popen(exec)
        print(res.read())
        res.close()
        results.append(full_o_fn)

    if results:
        return results
    else:
        raise RuntimeError("ffmpeg may not executed successfully.")


async def async_send_to_whisper(
        audio: str,
        tmp_dir:os.PathLike,
        order_:int, 
    ) -> Transcription:
    """
    Asynchronously send an audio file to OpenAI Whisper for transcription.

    Args:
        audio (str): Path to the input audio file.
        tmp_dir (os.PathLike): Temporary directory to store transcription files.
        order_ (int): Order of the audio file in the sequence.

    Returns:
        Transcription: Transcription object containing the text transcription.
    """
    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", ''))
    audio_file = open(audio, "rb")
    carry_on = "N"
    audio_size = os.path.getsize(audio)
    if audio_size>__WHISPER_CONTENT_LIMIT_IN_BYTES:
        print(f"🟡 Maximum content size limit of OpenAI Whisper ({__WHISPER_CONTENT_LIMIT_IN_BYTES} bytes) exceeded (\"{audio}\"={audio_size} bytes read)")
        carry_on = input("Do you want to continue?(y/N)")
    else:
        carry_on = 'y'

    if carry_on.lower().strip() not in ['y', 'yes']:
        raise InterruptedError(f"Process is interrupted manually due to file size exceeding. (\"{audio}\"={audio_size} bytes read)")
    transcription: Transcription = await client.audio.transcriptions.create(
        model="whisper-1", file=audio_file
    )
    audio_file.close()

    tmp_transcription_fn = os.path.join(tmp_dir, f".{order_}.txt")
    with open(tmp_transcription_fn, "w") as f:
        f.write(textwrap.fill(transcription.text))

    return tmp_transcription_fn

_now = time.strftime("%Y%m%d-%H%M%S", time.localtime(time.time()))
async def adump_transcription(
        audio_files:list[os.PathLike], 
        now:str=_now)->list[os.PathLike]:
    """
    Asynchronously dump transcriptions for multiple audio files.

    Args:
        audio_files (list[os.PathLike]): List of paths to the input audio files.
        now (str, optional): Current timestamp string. Defaults to current time in the specified format.

    Returns:
        list[os.PathLike]: List of paths to the dumped transcription files.
    """
    transcription_list = []
    tmp_dir = f".tmp_transcriptions_{now}"
    os.makedirs(tmp_dir)
    print("👉 Sending to OpenAI Whisper-1...")
    tasks = []
    for i, a in enumerate(audio_files):
        if librosa.get_duration(path=a) < 5:
            print((
                f"⚠️ WARNING: '{a}' "
                "less then 5 seconds. File skipped. "
            ))
            continue
        tasks.append(asyncio.create_task(
            async_send_to_whisper(a, tmp_dir, i)
        ))
    transcription_list = await asyncio.gather(*tasks,return_exceptions=True)
    if True in (issubclass(t.__class__, Exception) for t in transcription_list):
        print(*transcription_list, sep='\n')
        shutil.rmtree(tmp_dir)
        return []
    return transcription_list


def _summarize(*, content:str, by_:Literal["gemini",]='gemini', resp_lang:str):
    """
    Summarize content using Gemini or OpenAI.

    Args:
        content (str): Input content to be summarized.
        by_ (Literal["gemini"], optional): Summarization method. Defaults to 'gemini'.
        resp_lang (str): Language for response.

    Returns:
        str: Summary of the input content.
    """
    try: 
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel(model_name="gemini-1.5-pro",
                              generation_config=get_gemini_default_config(),
                              safety_settings=get_gemini_default_safety_setting())
        prompt_parts = get_prompt_parts(content, resp_lang)
        response = model.generate_content(prompt_parts)
        return response.text
    except Exception as e:
        raise e


async def main(*,
    fp:os.PathLike,
    duration:int | float,
    lang_:str,
    output:os.PathLike,
    summarize:bool, 
):
    now = time.strftime("%Y%m%d-%H%M%S", time.localtime(time.time()))
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", '')
    
    if "OPENAI_API_KEY" not in os.environ.keys():
        raise OpenaiApiKeyNotFound("OPENAI_API_KEY not found in environmental variables.")

    if summarize and ("GOOGLE_API_KEY" not in os.environ.keys()):
        raise GeminiApiKeyNotFound("GOOGLE_API_KEY not found in environmental variables.")

    if not output:
        output = f"{os.path.basename(fp)}_{now}.txt"

    audio_files = []
    tmp_audio_dir = "./.tmp_audio"
    _, origin_ext = os.path.splitext(os.path.basename(fp))
    is_text_file:bool = origin_ext.lower() in ('.txt', '.md')
    if not is_text_file:
        print(
            f"You are using OPEN AI API: {OPENAI_API_KEY[:10]}*****************",
        )
        if librosa.get_duration(path=fp) > duration:
            audio_files = split_audio(fp, duration=duration, output_dir=tmp_audio_dir)
        else:
            audio_files.append(os.path.realpath(fp))

        transcription_list = await adump_transcription(audio_files, now)
        shutil.rmtree(tmp_audio_dir)

        full_text = ""
        for t in transcription_list:
            print(transcription_list)
            with open(t, "r") as f:
                full_text += f.read() + "\n"
        if full_text:
            with open(output, "w", encoding="utf8") as f:
                f.write(full_text)
            print(f'✅ Transcription finished: {output}')
            shutil.rmtree(os.path.dirname(transcription_list[0]))

        else:
            _msg = "❗️Interrupted by errors."
            print('\x1b[33;20m' + _msg + '\x1b[0m')
            sys.exit(1)
        

    if summarize:
        if is_text_file:
            with open(fp, 'r') as f:
                full_text = f.read()
        try:
            print("👉 Start to summarize with Gemini...")
            res_text = _summarize(content=full_text, resp_lang=lang_)
            fn, _ = os.path.splitext(os.path.basename(fp))
            if res_text:
                _output_f = f"meeting-minutes_{fn}_{now}.md"
                with open(_output_f, 'w') as f:
                    f.write(res_text)
                print(f'✅ Summary finished: {_output_f}')
            else: 
                raise GeminiSummarizedFailed("Sorry...summary seems failed....")
        except Exception as e:
            print("🟥",e)
        finally:
            print("All tasks done, exit.")
            return full_text, res_text

        
    else:
        print((
            f"🟡 \"{os.path.basename(fp)}\" is a text file. "
            "Set `--summary true` if you need a summary"
        ))
        return full_text, ""




async def run():
    """
    Asynchronously perform audio transcription and optional summarization.

    Raises:
        OpenaiApiKeyNotFound: Raised if OPENAI_API_KEY is not found in environmental variables.
        GeminiApiKeyNotFound: Raised if GOOGLE_API_KEY is not found in environmental variables.
    """
    parser = argparse.ArgumentParser(
        description="Upload an audio file and make it transcription by OpenAI-Whisper"
    )
    parser.add_argument(
        "-f", "--file", required=True, type=str, help="The path of the audio file."
    )
    parser.add_argument(
        "-o",
        "--output",
        required=False,
        type=str,
        help="The path of the output transcription.",
    )
    parser.add_argument(
        "-s",
        "--summarize",
        required=False,
        type=bool,
        default=True,
        help="If to use Gemini to summarize. Default=true",
    )

    parser.add_argument(
        "--lang",
        required=False,
        type=str,
        default="original",
        help="""The lang to response""",
        choices=["original", "en", "zh-tw"],
    )

    parser.add_argument(
        "--duration",
        required=False,
        type=int,
        default=600,
        help="""Length of split audio in seconds.""",
    )
    args = parser.parse_args()
    fp: str = args.file
    output: str = args.output
    summarize:bool = args.summarize 
    duration:int = args.duration 
    lang_:str = lang_map[args.lang.replace('_', '-').lower()]

    await main(
        fp=fp,
        output=output,
        summarize=summarize,
        duration=duration,
        lang_=lang_
    )
