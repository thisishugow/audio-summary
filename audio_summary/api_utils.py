import os
import typing_extensions

from audio_summary.exceptions import GeminiApiKeyNotFound
from audio_summary import prompts 
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', None)
"""
curl https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=$GOOGLE_API_KEY \
    -H 'Content-Type: application/json' \
    -X POST \
    -d '{
      "contents": [{
        "parts":[{
          "text": "Write a story about a magic backpack."}]}]}' 2> /dev/null
"""
@typing_extensions.deprecated('The get_gemini_request_data method is deprecated; use google.generativeai instead.', category=None)
def get_gemini_url(model:str="gemini-pro", task:str="generateContent")->str:
    if GOOGLE_API_KEY is None:
        raise GeminiApiKeyNotFound("GOOGLE_API_KEY is not found in environmental variables.")
    return (f"https://generativelanguage.googleapis.com/v1beta/models/{model}:{task}?key={GOOGLE_API_KEY}")

@typing_extensions.deprecated('The get_gemini_request_data method is deprecated; use get_prompt_parts instead.', category=None)
def get_gemini_request_data(content:str, resp_lang:str=prompts.ORIGINAL)->list:
    data:list = []
    data.append({
        "role":"user",
        "parts":[
            {
                "text":(
                    f"Role Description: {prompts.MEETING_MINUTES_SECRETARY }"
                    f"Response Mode: {resp_lang}"
                    "Please make the meeting minutes for me. Here is the meeting transcription:\n" + content)
            }
        ]
    })
    return data


def get_prompt_parts(content:str, resp_lang:str=prompts.ORIGINAL)->list[str]:
    return [
        (f"- Role Description: {prompts.MEETING_MINUTES_SECRETARY } \n"
        f"- Response Mode: {resp_lang} \n"
        "Please make the meeting minutes for me. Here is the meeting transcription:\n" + content),
    ]


def get_gemini_default_config()->dict[str, float]:
    return {
        "temperature": 0.9,
        "top_p": 0.95,
        "top_k": 32,
        "max_output_tokens": 1024,
    }

def get_gemini_default_safety_setting()->list[dict[str, str]]:
    return [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
    ]

def get_openai_prompt_parts(content: str, resp_lang: str) -> list[dict[str, str]]:
    """
    Generates the prompt parts for OpenAI API.

    Args:
        content (str): The text content to be summarized.
        resp_lang (str): The desired language for the response.

    Returns:
        list[dict[str, str]]: A list of message dictionaries for the OpenAI API.
    """
    return [
        {"role": "system", "content": f"You are a helpful assistant that summarizes text.\n Role Description:{prompts.MEETING_MINUTES_SECRETARY}"},
        {"role": "user", "content": f"Please summarize the following text in {resp_lang}:\n{content}"}
    ]

def get_openai_default_config() -> dict:
    """
    Returns the default configuration for the OpenAI API.

    Returns:
        dict: A dictionary containing default model, temperature, and max_tokens.
    """
    return {
        "model": "gpt-4.1-mini",
        "temperature": 0.7,
        "max_tokens": 1024,
    }
