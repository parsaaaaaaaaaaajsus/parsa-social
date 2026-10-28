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
#------------------------
Reactions = ["😂", "👍", "😒", "😢", "🤩", "😐", "😭", "😡"]

class User(BaseModel):
    Name: str
    User_name: str
    PassWord: str

class Post(BaseModel):
    Title: str
    Text: str
    Like: int


class Comment(BaseModel):
    Text: str


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
def log_out(all: bool, response: Response, SEssion: str = Cookie(alias="session_id")):
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
                return "با موفقیت از حساب‌های خود خارج شدید"
            else:
                Sessions.pop(SEssion, None)
                response.delete_cookie(
                            key="session_id",
                            path="/",
                            secure=True,
                            httponly=True,
                            samesite="lax"
                        )
                return "با موفقیت از حساب خود خارج شدید"

len_posts = 0
@app.post("/share-post")
def share_post(post: Post, SEssion: str = Cookie(alias="session_id")):
    global len_posts
    title = post.Title
    text = post.Text
    like = post.Like
    user_name = Sessions.get(SEssion)

    if user_name is None:
        return "نشست نامعتبر است."
    for user in Accounts:
        if user_name == user["user_name"]:
            len_posts += 1
            user["my-posts"].append({"title": title, "text": text, "likes":[0], "num-p": len_posts, "comment": [], "num_comment": 0, "reactions": {}})
            Posts.append({"user_name": user_name,"title": title, "text": text, "likes":[0], "num-p": len_posts, "comment": [], "num_comment": 0, "reactions": {}})

            return "پست شما با موفقیت منتشر شد."
    return "خطا در انتشار پست شما."


@app.post("/Comment")
def comment_for_post(comment: Comment, len_post:int, SEssion: str = Cookie(alias="session_id")):
    text = comment.Text
    user_name = Sessions.get(SEssion)



    if user_name is None:
        return "نشست نامعتبر است."
    for user in Accounts:
        if user_name == user["user_name"]:
            for post in Posts:
                if len_post == post["num-p"]:
                    post["num_comment"] += 1
                    post["comment"].append({"user_name": user_name, "text": text, "likes":[0], "num-c": post["num_comment"], "reactions": {}, "reply": []})
                    

                    for owner in Accounts:
                        if owner["user_name"] == post["user_name"]:
                            for my_post in owner["my-posts"]:
                                if len_post == my_post["num-p"]:
                                    my_post["comment"].append({"user_name": user_name, "text": text, "likes":[0], "num-c": post["num_comment"], "reactions": {}, "reply": []})
                                    return "کامنت با موفقیت ثبت شد."
                    
                    return "مشکلی پیش آمده است."


    return "مشکلی پیش امده است."

@app.post("/Reaction-comment")
def reaction_comment(len_post: int, len_comment: int, re_action: str, SEssion: str = Cookie(alias="session_id")):
    user_name = Sessions.get(SEssion)

    if user_name is None:
        return "نشست نامعتبر است."
    for user in Accounts:
        if user_name == user["user_name"]:
            for post in Posts:
                if len_post == post["num-p"]:
                    for c in post["comment"]:
                        if c["num-c"] == len_comment:
                            for re in Reactions:
                                if re == re_action:
                                    c["reactions"][user_name] = re


                                    for owner in Accounts:
                                        if owner["user_name"] == post["user_name"]:
                                            for my_post in owner["my-posts"]:
                                                if len_post == my_post["num-p"]:
                                                    for C in my_post["comment"]:
                                                        if C["num-c"] == len_comment:
                                                            C["reactions"][user_name] = re
                                                            return "ری‌اکشن با موفقیت ثبت شد."
    return "مشکلی پیش امده است."



@app.post("/reply-to-comment")
def reply(len_post: int, len_comment: int, text: str, SEssion: str = Cookie(alias="session_id")):
    user_name = Sessions.get(SEssion)

    if user_name is None:
        return "نشست نامعتبر است."
    for user in Accounts:
        if user_name == user["user_name"]:
            for post in Posts:
                if len_post == post["num-p"]:
                    for c in post["comment"]:
                        if c["num-c"] == len_comment:

                            for owner in Accounts:
                                if owner["user_name"] == post["user_name"]:
                                    for my_post in owner["my-posts"]:
                                        if len_post == my_post["num-p"]:
                                            for C in my_post["comment"]:
                                                if C["num-c"] == len_comment:
                                                    C["reply"].append({"user_name": user_name, "text": text})
                                                    c["reply"].append({"user_name": user_name, "text": text})
                                                    return "پاسخ با موفقیت ثبت شد."
                                                
    return "مشکلی پیش آمده است."




@app.post("/like-c")
def like_comment(num_post: int, len_c: int, SEssion: str = Cookie(alias="session_id")):
    user_name = Sessions.get(SEssion)

    if user_name is None:
        return "نشست نامعتبر است."
    for user in Accounts:
        if user_name == user["user_name"]:
            for post in Posts:
                if num_post == post["num-p"]:
                    for c in post["comment"]:
                        if c["num-c"] == len_c:
                            liked_before = user_name in c["likes"]
                            if liked_before:
                                c["likes"].remove(user_name)
                                c["likes"][0] -= 1
                            else:
                                c["likes"][0] += 1
                                c["likes"].append(user_name)

                            for owner in Accounts:
                                if owner["user_name"] == post["user_name"]:
                                    for my_post in owner["my-posts"]:
                                        if num_post == my_post["num-p"]:
                                             for C in my_post["comment"]:
                                                if C["num-c"] == len_c:
                                                    if liked_before:
                                                        C["likes"].remove(user_name)
                                                        C["likes"][0] -= 1
                                                    else:
                                                        C["likes"][0] += 1
                                                        C["likes"].append(user_name)
                                                    return "وضعیت لایک تغییر کرد"

@app.get("/posts")
def get_posts():
    return Posts


@app.get("/my-posts")
def get_my_posts(user_name: str, SEssion: str = Cookie(alias="session_id")):

    user_name = Sessions.get(SEssion)

    if user_name is None:
        return "نشست نامعتبر است."
    for user in Accounts:
        if user_name == user["user_name"]:
            return user["my-posts"]

    return []


@app.post("/like-p")
def like_post(num_post: int, SEssion: str = Cookie(alias="session_id")):
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



@app.post("/Reaction")
def reaction(len_post: int, re_action: str, SEssion: str = Cookie(alias="session_id")):
    user_name = Sessions.get(SEssion)

    if user_name is None:
        return "نشست نامعتبر است."
    for user in Accounts:
        if user_name == user["user_name"]:
            for post in Posts:
                if len_post == post["num-p"]:
                    for re in Reactions:
                        if re == re_action:
                            post["reactions"][user_name] = re


                            for owner in Accounts:
                                if owner["user_name"] == post["user_name"]:
                                    for my_post in owner["my-posts"]:
                                        if len_post == my_post["num-p"]:
                                            my_post["reactions"][user_name] = re
                                            return "ری‌اکشن با موفقیت ثبت شد."
    return "مشکلی پیش امده است."



@app.delete("/delet-post")
def delet_post(len_post: int, SEssion: str = Cookie(alias="session_id")):
    user_name = Sessions.get(SEssion)

    if user_name is None:
        return "نشست نامعتبر است."
    for user in Accounts:
        if user_name == user["user_name"]:
            if user_name == "Admin":
                for post in Posts:
                    if len_post == post["num-p"]:
                        Posts.remove(post)


                        for owner in Accounts:
                                if owner["user_name"] == post["user_name"]:
                                    for my_post in owner["my-posts"]:
                                        if len_post == my_post["num-p"]:
                                            owner["my-posts"].remove(my_post)
                                            return "پست با موفقیت حذف شد."



            else:
                 for post in Posts:
                    if len_post == post["num-p"]:
                        if post["user_name"] == user_name:
                            Posts.remove(post)

                            for owner in Accounts:
                                if owner["user_name"] == post["user_name"]:
                                    for my_post in owner["my-posts"]:
                                        if len_post == my_post["num-p"]:
                                            owner["my-posts"].remove(my_post)
                                            return "پست شما با موفقیت حذف شد."
    return "مشکلی در حذف پست وجود دارد."

@app.get("/")
def home():
    return FileResponse("frontend/index.html")

