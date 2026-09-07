from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


app = FastAPI()
ph = PasswordHasher()

MIN_PASSWORD_LENGTH = 8
users_db = {}

class UserRegisteration(BaseModel):
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
    The health of the site
    """
    return {"status": "ok"}

@app.post("/signup", status_code=201)
def register_user(user_cred: UserRegisteration):
    """
    Validate the user's credentials on sign up before saving to the user-database.
    """
    if user_cred.email in users_db:
        raise HTTPException(status_code=400, detail="That email is already in use!")

    if not user_cred.password:
        raise HTTPException(status_code=400, detail="Password cannot be empty!")
    
    if len(user_cred.password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=f"Password must have a min of {MIN_PASSWORD_LENGTH} characters long")

    hashed_user_password = ph.hash(user_cred.password)
    users_db[user_cred.email] = hashed_user_password

    return {"message": "Your credentials have been saved! you can now log in"}


@app.post("/signin", status_code=202)
def user_signin(user_cred: UserRegisteration):
    """
    validate the user's signin credentials matches information in the user-database.
    """
    if user_cred.email not in users_db:
        raise HTTPException(status_code=400, detail="Email or Password doesnt match")
    
    if not user_cred.password:
        raise HTTPException(status_code=400, detail="Email or Password doesnt match")
    
    try:
        ph.verify(users_db[user_cred.email], user_cred.password)
        return {"message": "Welcome back!"}
    except VerifyMismatchError:
        raise HTTPException(status_code=400, detail="Email or Password doesnt match")
    


