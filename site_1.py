from fastapi import FastAPI, Response, Cookie, HTTPException, Depends
from pydantic import BaseModel
from fastapi.responses import FileResponse
from database import get_connection, init_database
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
import secrets
import hashlib


password_hash = PasswordHash.recommended()
app = FastAPI()


@app.on_event("startup")
def startup_database():
    init_database()


Reactions = ["😂", "👍", "😒", "😢", "🤩", "😐", "😭", "😡"]
