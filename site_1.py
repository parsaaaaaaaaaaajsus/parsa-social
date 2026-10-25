#*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
#*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse
import secrets
from fastapi import Response
from fastapi import Cookie

app = FastAPI()

Accounts = []
Posts = []
Sessions = {}

class User(BaseModel):
    Name: str
    User_name: str
    PassWord: str

class Post(BaseModel):
    Title: str
    Text: str
    Like: int


@app.post("/logup")
def log_up(user: User, response: Response):
    name = user.Name
    user_name = user.User_name
    password = user.PassWord
    for user in Accounts:
        if user_name == user["user_name"]:
            return "این حساب کاربری از قبل وجود دارد."

    Accounts.append({"user_name": user_name,"name": name, "password": password, "my-posts": []})
    session_id = secrets.token_urlsafe(50)
    Sessions[session_id] = user_name

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=86400
    )

    return "حساب کاربری شما با موفقیت ساخته شد."

@app.post("/login")
def log_in(user_name: str, pass_word: str, response: Response):
    for user in Accounts:
        if user_name == user["user_name"] and pass_word == user["password"]:
            session_id = secrets.token_urlsafe(50)
            Sessions[session_id] = user_name

            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=86400
            )

            return "با موفقیت به حساب خود وارد شدید"
        
    return "رمز اشتباه است یا این حساب وجود ندارد"

@app.delete("/logout")
def log_out(user_name: str, all: bool, response: Response, SEssion: str = Cookie(alias="session_id")):
    user_name = Sessions.get(SEssion)

    if user_name is None:
        return "نشست نامعتبر است."
    for user in Accounts:
        if user_name == user["user_name"]:
            if all:
                for S in list(Sessions):
                    if Sessions[S] == user_name:
                        Sessions.pop(S, None)
                response.delete_cookie(
                    key="session_id",
                    path="/",
                    secure=True,
                    httponly=True,
                    samesite="lax"
                )
            else:
                Sessions.pop(SEssion, None)
                response.delete_cookie(
                            key="session_id",
                            path="/",
                            secure=True,
                            httponly=True,
                            samesite="lax"
                        )


@app.post("/share-post")
def share_post(post: Post,user__name: str,SEssion: str = Cookie(alias="session_id")):
    title = post.Title
    text = post.Text
    like = post.Like
    num_post = len(Posts)
    user_name = Sessions.get(SEssion)

    if user_name is None:
        return "نشست نامعتبر است."
    for user in Accounts:
        if user_name == user["user_name"]:
            user["my-posts"].append({"title": title, "text": text, "likes":[0], "num-p": num_post})
            Posts.append({"user_name": user_name,"title": title, "text": text, "likes":[0], "num-p": num_post})

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

@app.post("/like-p")
def like(num_post: int, user__name: str, SEssion: str = Cookie(alias="session_id")):
    user_name = Sessions.get(SEssion)

    if user_name is None:
        return "نشست نامعتبر است."
    for user in Accounts:
        if user_name == user["user_name"]:
            for post in Posts:
                if num_post == post["num-p"]:
                    liked_before = user_name in post["likes"]
                    if liked_before:
                        post["likes"].remove(user_name)
                        post["likes"][0] -= 1
                    else:
                        post["likes"][0] += 1
                        post["likes"].append(user_name)

                    for owner in Accounts:
                        if owner["user_name"] == post["user_name"]:
                            for my_post in owner["my-posts"]:
                                if num_post == my_post["num-p"]:
                                    if liked_before:
                                        my_post["likes"].remove(user_name)
                                        my_post["likes"][0] -= 1
                                    else:
                                        my_post["likes"][0] += 1
                                        my_post["likes"].append(user_name)
                                    return "وضعیت لایک تغییر کرد"

@app.get("/")
def home():
    return FileResponse("frontend/index.html")

