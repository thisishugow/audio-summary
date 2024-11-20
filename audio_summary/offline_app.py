import os
from typing import Literal

import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

# NotImplementedError: The operator 'aten::isin.Tensor_Tensor_out' is not currently 
# implemented for the MPS device. If you want this op to be added in priority during 
# the prototype phase of this feature, please comment on https://github.com/pytorch/pytorch/issues/77764. 
# As a temporary fix, you can set the environment variable `PYTORCH_ENABLE_MPS_FALLBACK=1` to 
# use the CPU as a fallback for this op. WARNING: this will be slower than running natively on MPS.
# os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'


def speech_to_text(audio_fn:os.PathLike, model_name:Literal["openai/whisper-large-v3", "openai/whisper-medium"]="openai/whisper-medium")->str:
    device = "cuda:0" if torch.cuda.is_available() else "mps"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_name, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    )
    model.to(device)

    processor = AutoProcessor.from_pretrained(model_name)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        max_new_tokens=128,
        chunk_length_s=30,
        batch_size=16,
        return_timestamps=True,
        torch_dtype=torch_dtype,
        device=device,
    )

    result:dict = pipe(audio_fn)
    return result.get('text', None)

