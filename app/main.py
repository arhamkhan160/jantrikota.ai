from fastapi import FastAPI

app = FastAPI(title="AutoML Agent - Test Mode")

# Root endpoint
@app.get("/")
def home():
    return {
        "message": "AutoML API is running inside Docker 🚀"
    }

# Health check endpoint
@app.get("/health")
def health():
    return {
        "status": "ok"
    }

# Simple test endpoint
@app.get("/test")
def test():
    return {
        "docker": True,
        "fastapi": True,
        "message": "Everything is working fine inside container"
    }