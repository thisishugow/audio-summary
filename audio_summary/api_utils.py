import os

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

def get_gemini_url(model:str="gemini-pro", task:str="generateContent")->str:
    if GOOGLE_API_KEY is None:
        raise GeminiApiKeyNotFound("GOOGLE_API_KEY is not found in environmental variables.")
    return (f"https://generativelanguage.googleapis.com/v1beta/models/{model}:{task}?key={GOOGLE_API_KEY}")


def get_gemini_request_data(content:str)->list:
    data:list = []
    data.append({
        "role":"user",
        "parts":[
            {
                "text":(
                    f"Role Description: {prompts.MEETING_MINUTES_SECRETARY }"
                    f"Response Mode: {prompts.RESPONSE_IN_MARKDOWN}"
                    f"Response Language: Original language of the transcription."
                    "Please make the meeting minutes for me. Here is the meeting transcription:\n" + content)
            }
        ]
    })
    return data