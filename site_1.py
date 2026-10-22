#*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
#*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse

app = FastAPI()

Accounts = []

class User(BaseModel):
    Name: str
    User_name: str
    PassWord: str


@app.post("/logup")
def log_up(user: User):
    name = user.Name
    user_name = user.User_name
    password = user.PassWord
    for user in Accounts:
        if user_name == user["user_name"]:
            return "این حساب کاربری از قبل وجود دارد."

    Accounts.append({"user_name": user_name,"name": name, "password": password})
    return "حساب کاربری شما با موفقیت ساخته شد."

@app.post("/login")
def log_in(user_name: str, pass_word: str):
    for user in Accounts:
        if user_name == user["user_name"] and pass_word == user["password"]:
            return "با موفقیت به حساب خود وارد شدید"
        
    return "رمز اشتباه است یا این حساب وجود ندارد"



@app.get("/")
def home():
    return FileResponse("frontend/index.html")
