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


@app.post("/create-A")
def Creat_an_Account(user: User):
    name = user.Name
    user_name = user.User_name
    for user in Accounts:
        if user_name == user["user_name"]:
            return "این حساب کاربری از قبل وجود دارد."

    Accounts.append({"user_name": user_name,"name": name})
    return "حساب کاربری شما با موفقیت ساخته شد."

@app.get("/see-A")
def see_account():
    return Accounts

@app.get("/")
def home():
    return FileResponse("frontend/index.html")
