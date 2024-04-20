import os

import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

# NotImplementedError: The operator 'aten::isin.Tensor_Tensor_out' is not currently 
# implemented for the MPS device. If you want this op to be added in priority during 
# the prototype phase of this feature, please comment on https://github.com/pytorch/pytorch/issues/77764. 
# As a temporary fix, you can set the environment variable `PYTORCH_ENABLE_MPS_FALLBACK=1` to 
# use the CPU as a fallback for this op. WARNING: this will be slower than running natively on MPS.
# os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'


def app():
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model_id = "openai/whisper-large-v3"
    model_id = "openai/whisper-medium"

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    )
    model.to(device)

    processor = AutoProcessor.from_pretrained(model_id)

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

    # dataset = load_dataset("distil-whisper/librispeech_long", "clean", split="validation")
    audio_fp = ""
    audio_fp = ""

    result = pipe(audio_fp)
    print(result)
    with open('test.txt', 'w') as f:
        f.write(result['text'])

# sample.close()

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    app()