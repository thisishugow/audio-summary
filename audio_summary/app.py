import argparse
import http.client
import os
import time
from string import Template
import math
import textwrap
import shutil
from typing import Literal
import urllib
import urllib.parse
import urllib.request
import json

import tqdm
import librosa

from openai import OpenAI
from openai.types.audio import Transcription

from audio_summary.exceptions import GeminiSummarizedFailed, OpenaiApiKeyNotFound
from audio_summary.api_utils import *

OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", '')

def split_audio(
    fn: str, duration: float = 600, output_dir: str = "./.tmp_audio"
) -> list[str]:
    duration = float(duration)
    ffmpeg_exec = "ffmpeg"
    cmd = Template(
        (
            f"{ffmpeg_exec} "
            f"-i {fn} "
            f"-vn -acodec copy "
            f"-ss $start_time "
            f"-t {duration} "
            f"$output "
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


def send_to_whisper(audio: str) -> Transcription:
    client = OpenAI(api_key=OPENAI_API_KEY)
    audio_file = open(audio, "rb")
    transcription: Transcription = client.audio.transcriptions.create(
        model="whisper-1", file=audio_file
    )
    audio_file.close()
    return transcription


def _summarize(content:str, by_:Literal["gemini",]='gemini'):
    data = {"contents": get_gemini_request_data(content)}
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f)
    if by_ == "gemini":
        req = urllib.request.Request(
                url=get_gemini_url(),
                data=json.dumps(data).encode('utf-8'),
                method="POST",
                headers={
                    'Content-Type': 'application/json'
                }
            )
    try:
        with urllib.request.urlopen(req) as resp:
            res = resp.read().decode('utf-8')
            return res
    except urllib.error.HTTPError as e:
        error = json.loads(e.read().decode('utf-8'))
        raise ConnectionError((
            f'- HTTPError: {e.code}\n'
            '- detail: '+ error["error"]["message"]))
    except Exception as e:
        print(e)

def make_transcription():
    if "OPENAI_API_KEY" not in os.environ.keys():
        raise OpenaiApiKeyNotFound("OPENAI_API_KEY not found in environmental variables.")
    
    now = time.strftime("%Y%m%d-%H%M%S", time.localtime(time.time()))
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
        default=False,
        help="If to use Gemini to summarize.",
    )
    args = parser.parse_args()
    fp: str = args.file
    output: str = args.output
    summarize:bool = args.summarize 

    if summarize and ("GOOGLE_API_KEY" not in os.environ.keys()):
        raise GeminiApiKeyNotFound("GOOGLE_API_KEY not found in environmental variables.")

    if not output:
        output = f"{os.path.basename(fp)}_{now}.txt"

    print(
        f"You are using OPEN AI API: {OPENAI_API_KEY[:10]}*****************",
    )
    audio_files = []
    tmp_audio_dir = "./.tmp_audio"
    if librosa.get_duration(path=fp) > 600.0:
        audio_files = split_audio(fp, output_dir=tmp_audio_dir)
    else:
        audio_files.append(os.path.realpath(fp))

    transcription_list = []
    tmp_dir = f".tmp_transcriptions_{now}"
    os.makedirs(tmp_dir)
    print("Sending to OpenAI Whisper-1...")
    for i, a in enumerate(tqdm.tqdm(audio_files)):
        if librosa.get_duration(path=a) < 10:
            continue
        transcription = send_to_whisper(a)
        tmp_transcription_fn = os.path.join(tmp_dir, f".{i}.txt")
        with open(tmp_transcription_fn, "w") as f:
            f.write(textwrap.fill(transcription.text))
        transcription_list.append(tmp_transcription_fn)

    full_text = ""
    for t in transcription_list:
        with open(t, "r") as f:
            full_text += f.read() + "\n"

    with open(output, "w", encoding="utf8") as f:
        f.write(full_text)

    shutil.rmtree(tmp_dir)
    shutil.rmtree(tmp_audio_dir)
    print(f'✅ Transcription finished: {output}')

    if summarize:
        try:
            print("Start to summarize with Gemini...")
            res = _summarize(full_text)
            summary_md = (
                json.loads(res)
                .get("candidates", [])[0]
                .get('content', {})
                .get('parts', [])[0]
                .get('text', None)
            )
            fn, _ = os.path.splitext(os.path.basename(fp))
            if summary_md:
                _output_f = f"meeting-minutes_{fn}_{now}.md"
                with open(_output_f, 'w') as f:
                    f.write(summary_md)
                print(f'✅ Summary finished: {_output_f}')
            else: 
                raise GeminiSummarizedFailed("Sorry...summary seems failed....")
        except Exception as e:
            print(e)
