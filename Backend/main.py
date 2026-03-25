from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from .style_analyser import update_profile, get_profile, reset_profile, build_profile_from_texts
from dotenv import load_dotenv
from openai import OpenAI
import os
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

api_key = os.getenv("OPENAI_API_KEY")

#just here so i can test if it found
if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Check your enviorment variables")

client = OpenAI(api_key=api_key)

#just allowing everything for now might change latet
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#only accepting lists if strings so it expects [text 1, text 2, text 3 ....]
class TextUploadRequest(BaseModel):
    texts: List[str]

class GenerateRequest(BaseModel):
    prompt: str
    texts: List[str]

#test to see if backend is up 
@app.get("/")
def read_root():
    return {"message": "Backend is running"}

#getting all functions
@app.post("/add_texts")
def add_texts(request: TextUploadRequest):
    return update_profile(request.texts)

@app.get("/profile")
def view_profile():
    return get_profile()

@app.post("/profile_from_texts")
def profile_from_texts(request: TextUploadRequest):
    if not request.texts:
        return {"message": "No profile created yet"}
    return build_profile_from_texts(request.texts)

@app.post("/reset_profile")
def clear_profile():
    return reset_profile()

#where the prompt is built it basiclly appendes your prompt with your stylesheet
def build_style_prompt(profile: dict, user_prompt: str) -> str:
    return f"""
Write in the following style:
Average sentence length: {profile.get("avg_sentence_length")}
Average word length: {profile.get("avg_word_length")}
Average paragraph length: {profile.get("avg_paragraph_length")}
Vocabulary richness: {profile.get("vocabulary_richness")}
Readability score: {profile.get("avg_readability")}
Common words: {profile.get("top_10_words")}
Common bigrams: {profile.get("top_10_bigrams")}
Now write about:
{user_prompt}
"""

@app.post("/generate")
async def generate_text(request: GenerateRequest):
    if not request.texts:
        return {"error": "No profile found. Add texts first."}

    try:
        profile = build_profile_from_texts(request.texts)
        style_prompt = build_style_prompt(profile, request.prompt)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You imitate writing style."},
                {"role": "user", "content": style_prompt}
            ],
            #crontols how creative the model is
            temperature=0.8
        )

        return {
            "generated_text": response.choices[0].message.content
        }

    #here incase anything goes wrong
    except Exception as e:
        return {"error": str(e)}