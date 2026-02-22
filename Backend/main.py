from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from style_analyser import update_profile, get_profile, reset_profile

app = FastAPI()


class TextUploadRequest(BaseModel):
    texts: List[str]


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