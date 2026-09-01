from fastapi import FastAPI, HTTPException
import sys

app = FastAPI()

@app.get("/")
def read_root():
    """
    Home page endpoint.
    Serves a simple welcome message in JSON format.
    """
    return {"message": "Welcome to the Authentication Core."}

@app.get("/health")
def health_check():
    """
    Health check endpoint.
    Indicates that the app is running smoothly and ready for traffic.
    """
    return {"status": "ok"}