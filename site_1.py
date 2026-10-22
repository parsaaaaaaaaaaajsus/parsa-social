#*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
#*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

Accounts = []

class User(BaseModel):
    Name: str
    User_name: str


@app.get("/")
def hi():
    return "hello parsa batmani"
