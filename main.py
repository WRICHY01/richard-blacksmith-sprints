import os

import uuid
from supabase import Client, create_client
from postgrest.exceptions import APIError
from fastapi import FastAPI, HTTPException, Response, Cookie
from pydantic import BaseModel, EmailStr
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing database configuration inside .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


app = FastAPI()
ph = PasswordHasher()

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 256


class UserRegistration(BaseModel):
    email: EmailStr
    password: str


@app.get('/')
def get_root():
    """
    root directory of the application
    """
    return {"message": "Welcome to the homepage!"}

@app.get("/health")
def get_health_status():
    """
    The health of the application
    """
    return {"status": "ok"}

@app.post("/signup", status_code=201)
def register_user(user_cred: UserRegistration):
    """
    Validate the user's credentials on sign up before saving to the user-database.
    """
    normalized_email = user_cred.email.lower()
    
    if not user_cred.password:
        raise HTTPException(status_code=400, detail="Password cannot be empty!")
    
    if len(user_cred.password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=f"Password must have a min of {MIN_PASSWORD_LENGTH} characters long")

    if len(user_cred.password) > MAX_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=f"Password cannot be longer than {MAX_PASSWORD_LENGTH} characters")

    hashed_user_password = ph.hash(user_cred.password)

    try:
        supabase.table("users").insert({
            "email": normalized_email,
            "hashed_password": hashed_user_password
        }).execute()
        
    except APIError as e:
        if e.code == "23505":
            raise HTTPException(status_code=409, detail="That email is already in use")
        raise

    return {"message": "Your credentials have been saved! you can now log in"}

@app.post("/signin", status_code=202)
def user_signin(user_cred: UserRegistration, response: Response):
    """
    validate the user's signin credentials matches information in the user-database.
    """
    normalized_email = user_cred.email.lower()
    db_response = supabase.table("users").select("hashed_password").eq("email", user_cred.email).execute()

    if not db_response.data:
        raise HTTPException(status_code=400, detail="Email or Password doesnt match")

    user_hashed_password = db_response.data[0]["hashed_password"]

    try:
        ph.verify(user_hashed_password, user_cred.password)

    except VerifyMismatchError:
        raise HTTPException(status_code=400, detail="Email or Password doesnt match")
    
    session_token = str(uuid.uuid4())

    expiration_time = datetime.now(timezone.utc) + timedelta(days=1)
    
    supabase.table("user_sessions").insert({
        "session_token": session_token,
        "user_email": normalized_email,
        "expiration_time": expiration_time.isoformat()
    }).execute()

    response.set_cookie(
        key="session_id",
        value=session_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=86400
    )

    return {"message": "Welcome!"}

@app.get("/dashboard")
def view_dashboard_page(session_id: str | None = Cookie(default=None)):
    """
    Securely logs the user in after validation and survives context reset
    """
    if not session_id:
        raise HTTPException(status_code=401, detail="Unauthorized: No Active Session Found!")

    session_db_response = supabase.table("user_sessions").select("user_email", "session_token", "expiration_time").eq("session_token", session_id).execute()
    user_session_token = session_db_response.data
    
    if not user_session_token:
        raise HTTPException(status_code=401, detail="Unauthorized: No Active Session Found!")

    todays_date = datetime.now(timezone.utc)
    expiry_date = datetime.fromisoformat(user_session_token[0]["expiration_time"].replace("Z", "+00:00"))
    
    if todays_date > expiry_date:
        raise HTTPException(status_code=401, detail="Unauthorized: Session expired")
    
    return {"message": f"welcome to your secure identity vault, {user_session_token[0]["user_email"]}",
            "authenticated_as": user_session_token[0]["user_email"]}