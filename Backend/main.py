from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import List
from .style_analyser import update_profile, get_profile, reset_profile
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client
from fastapi.middleware.cors import CORSMiddleware
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

api_key = os.getenv("OPENAI_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Check your environment variables")

if not supabase_url or not supabase_service_role_key:
    raise ValueError("Supabase environment variables not found")

client = OpenAI(api_key=api_key)
supabase = create_client(supabase_url, supabase_service_role_key)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TextUploadRequest(BaseModel):
    texts: List[str]


class GenerateRequest(BaseModel):
    prompt: str


def get_current_user_id(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization.split(" ", 1)[1]

    try:
        response = supabase.auth.get_user(token)
        user = response.user
        if not user:
            raise HTTPException(status_code=401, detail="Invalid user")
        return user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@app.get("/")
def read_root():
    return {"message": "Backend is running"}


@app.post("/add_texts")
def add_texts(request: TextUploadRequest, authorization: str = Header(None)):
    user_id = get_current_user_id(authorization)
    return update_profile(user_id, request.texts)


@app.get("/profile")
def view_profile(authorization: str = Header(None)):
    user_id = get_current_user_id(authorization)
    return get_profile(user_id)


@app.post("/reset_profile")
def clear_profile(authorization: str = Header(None)):
    user_id = get_current_user_id(authorization)
    return reset_profile(user_id)


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
async def generate_text(request: GenerateRequest, authorization: str = Header(None)):
    user_id = get_current_user_id(authorization)
    profile = get_profile(user_id)

    if not profile or "message" in profile:
        return {"error": "No profile found. Upload texts first."}

    try:
        style_prompt = build_style_prompt(profile, request.prompt)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You imitate writing style."},
                {"role": "user", "content": style_prompt}
            ],
            temperature=0.8
        )

        return {
            "generated_text": response.choices[0].message.content
        }

    except Exception as e:
        return {"error": str(e)}
