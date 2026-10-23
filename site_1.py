#*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
#*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse

app = FastAPI()

Accounts = []
Posts = []

class User(BaseModel):
    Name: str
    User_name: str
    PassWord: str

class Post(BaseModel):
    Title: str
    Text: str
    Like: int


@app.post("/logup")
def log_up(user: User):
    name = user.Name
    user_name = user.User_name
    password = user.PassWord
    for user in Accounts:
        if user_name == user["user_name"]:
            return "این حساب کاربری از قبل وجود دارد."

    Accounts.append({"user_name": user_name,"name": name, "password": password, "my-posts": []})
    return "حساب کاربری شما با موفقیت ساخته شد."

@app.post("/login")
def log_in(user_name: str, pass_word: str):
    for user in Accounts:
        if user_name == user["user_name"] and pass_word == user["password"]:
            return "با موفقیت به حساب خود وارد شدید"
        
    return "رمز اشتباه است یا این حساب وجود ندارد"

@app.post("/share-post")
def share_post(post: Post, user_name: str):
    title = post.Title
    text = post.Text
    like = post.Like
    for user in Accounts:
        if user_name == user["user_name"]:
            user["my-posts"].append({"title": title, "text": text})
            Posts.append({"user_name": user_name,"title": title, "text": text})
            return "پست شما با موفقیت منتشر شد."
    return "خطا در انتشار پست شما."
@app.get("/posts")
def get_posts():
    return Posts


@app.get("/my-posts")
def get_my_posts(user_name: str):
    for user in Accounts:
        if user_name == user["user_name"]:
            return user["my-posts"]

    return []


@app.get("/")
def home():
    return FileResponse("frontend/index.html")

