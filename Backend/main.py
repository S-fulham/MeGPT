from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from style_analyser import update_profile, get_profile, reset_profile
from dotenv import load_dotenv
from openai import OpenAI
import os
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

api_key = os.getenv("OPENAI_API_KEY")
print("ENV FILE LOADED, KEY =", api_key)

if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Check your .env file.")

client = OpenAI(api_key=api_key)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later you can restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextUploadRequest(BaseModel):
    texts: List[str]

class GenerateRequest(BaseModel):
    prompt: str

@app.get("/")
def read_root():
    return {"message": "Backend is running"}


@app.post("/add_texts")
def add_texts(request: TextUploadRequest):
    return update_profile(request.texts)


@app.get("/profile")
def view_profile():
    return get_profile()


@app.post("/reset_profile")
def clear_profile():
    return reset_profile()

def build_style_prompt(profile: dict, user_prompt: str) -> str:
    return f"""
Write in the following style:

Average sentence length: {profile.get("avg_sentence_length")}
Average word length: {profile.get("avg_word_length")}
Average paragraph length: {profile.get("avg_paragraph_length")}
Vocabulary richness: {profile.get("vocab_richness")}
Readability score: {profile.get("readability_score")}

Common words: {profile.get("top_words")}
Common bigrams: {profile.get("top_bigrams")}

Now write about:
{user_prompt}
"""
@app.post("/generate")
async def generate_text(request: GenerateRequest):
    profile = get_profile()  
    if "message" in profile:  
        return {"error": "No profile found. Upload texts first."}

    style_prompt = build_style_prompt(profile, request.prompt)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a writing style imitation engine."},
            {"role": "user", "content": style_prompt}
        ],
        temperature=0.8
    )

    return {
        "generated_text": response.choices[0].message.content
    }