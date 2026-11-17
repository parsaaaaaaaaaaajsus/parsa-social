from fastapi import FastAPI, Response, Cookie, HTTPException, Depends
from pydantic import BaseModel
from fastapi.responses import FileResponse
from database import get_connection
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
import secrets
import hashlib


password_hash = PasswordHash.recommended()
app = FastAPI()

Reactions = ["😂", "👍", "😒", "😢", "🤩", "😐", "😭", "😡"]


# --------------------------------------------------
# Models
# --------------------------------------------------

class User(BaseModel):
    Name: str
    User_name: str
    PassWord: str
class Login(BaseModel):
    User_name: str
    PassWord: str
class Post(BaseModel):
    Title: str
    Text: str
class Comment(BaseModel):
    Text: str


# --------------------------------------------------
# Dependencies
# --------------------------------------------------

def get_current_user(
    session_id: str | None = Cookie(default=None, alias="session_id")
):
    if not session_id:
        raise HTTPException(status_code=401, detail="نشست وجود ندارد.")

    token_hash = hashlib.sha256(session_id.encode()).hexdigest()
    expired = False
    current_user = None

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.id, u.user_name, u.name, s.expires_at
                FROM sessions AS s
                JOIN users AS u ON u.id = s.user_id
                WHERE s.token_hash = %s
                """,
                (token_hash,)
            )
            session = cur.fetchone()

            if session is None:
                raise HTTPException(
                    status_code=401,
                    detail="نشست نامعتبر است."
                )

            if session["expires_at"] <= datetime.now(timezone.utc):
                cur.execute(
                    "DELETE FROM sessions WHERE token_hash = %s",
                    (token_hash,)
                )
                expired = True
            else:
                current_user = {
                    "id": session["id"],
                    "user_name": session["user_name"],
                    "name": session["name"]
                }

    if expired:
        raise HTTPException(
            status_code=401,
            detail="نشست منقضی شده است."
        )

    return current_user

def get_current_post(post_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM posts WHERE id = %s",
                (post_id,)
            )
            post = cur.fetchone()

    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    return post

def get_current_post_by_target(target_id: int):
    return get_current_post(target_id)

def get_current_comment(comment_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM comments WHERE id = %s",
                (comment_id,)
            )
            comment = cur.fetchone()

    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")

    return comment

def get_current_audience(user_name_audience: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_name, name
                FROM users
                WHERE user_name = %s
                """,
                (user_name_audience,)
            )
            audience = cur.fetchone()

    if audience is None:
        raise HTTPException(status_code=404, detail="Audience not found")

    return audience

def get_current_target(target_type: str, target_id: int):
    tables = {
        "post": "posts",
        "comment": "comments",
        "reply": "replys"
    }

    table = tables.get(target_type)

    if table is None:
        raise HTTPException(status_code=422, detail="Invalid target type")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT id FROM {table} WHERE id = %s",
                (target_id,)
            )
            target = cur.fetchone()

    if target is None:
        raise HTTPException(
            status_code=404,
            detail=f"{target_type.capitalize()} not found"
        )

    return target

def get_current_reply(reply_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id
                FROM replys
                WHERE id = %s
                """,
                (reply_id,)
            )
            reply = cur.fetchone()

    if reply is None:
        raise HTTPException(status_code=404, detail="Reply not found")

    return reply

def get_current_reply_in_comment(reply_id: int, comment_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM replys
                WHERE id = %s
                AND (
                    comment_or_reply_id = %s
                    OR comment_id = %s
                )
                """,
                (reply_id, comment_id, comment_id)
            )
            reply = cur.fetchone()

    if reply is None:
        raise HTTPException(
            status_code=404,
            detail="Reply not found in this comment"
        )

    return reply


# --------------------------------------------------
# Authentication
# --------------------------------------------------

@app.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return current_user


@app.post("/logup")
def log_up(user: User, response: Response):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (name, user_name, password_hash)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_name) DO NOTHING
                RETURNING id
                """,
                (
                    user.Name,
                    user.User_name,
                    password_hash.hash(user.PassWord)
                )
            )
            new_user = cur.fetchone()

            if new_user is None:
                return "این حساب کاربری از قبل وجود دارد."

            session_id = secrets.token_urlsafe(50)
            token_hash = hashlib.sha256(session_id.encode()).hexdigest()
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)

            cur.execute(
                """
                INSERT INTO sessions (user_id, token_hash, expires_at)
                VALUES (%s, %s, %s)
                """,
                (new_user["id"], token_hash, expires_at)
            )

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )

    return "حساب کاربری شما با موفقیت ساخته شد."


@app.post("/login")
def log_in(user: Login, response: Response):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, password_hash
                FROM users
                WHERE user_name = %s
                """,
                (user.User_name,)
            )
            db_user = cur.fetchone()

            if (
                db_user is None
                or not password_hash.verify(
                    user.PassWord,
                    db_user["password_hash"]
                )
            ):
                raise HTTPException(
                    status_code=401,
                    detail="نام کاربری یا رمز عبور اشتباه است."
                )

            session_id = secrets.token_urlsafe(50)
            token_hash = hashlib.sha256(session_id.encode()).hexdigest()
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)

            cur.execute(
                """
                INSERT INTO sessions (user_id, token_hash, expires_at)
                VALUES (%s, %s, %s)
                """,
                (db_user["id"], token_hash, expires_at)
            )

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )

    return "با موفقیت به حساب خود وارد شدید."


@app.delete("/logout")
def log_out(
    all: bool,
    response: Response,
    current_user: dict = Depends(get_current_user),
    session_id: str = Cookie(alias="session_id")
):
    token_hash = hashlib.sha256(session_id.encode()).hexdigest()

    with get_connection() as conn:
        with conn.cursor() as cur:
            if all:
                cur.execute(
                    "DELETE FROM sessions WHERE user_id = %s",
                    (current_user["id"],)
                )
                message = "تمام نشست‌ها حذف شدند."
            else:
                cur.execute(
                    """
                    DELETE FROM sessions
                    WHERE token_hash = %s AND user_id = %s
                    """,
                    (token_hash, current_user["id"])
                )
                message = "نشست حذف شد."

    response.delete_cookie(
        key="session_id",
        path="/",
        secure=True,
        httponly=True,
        samesite="lax"
    )

    return message


# --------------------------------------------------
# Likes
# --------------------------------------------------

@app.post("/like")
def like_post(
    target_type: str,
    target_id: int,
    user: dict = Depends(get_current_user),
    target: dict = Depends(get_current_target)
):
    tables = {
        "post": "posts",
        "comment": "comments",
        "reply": "replys"
    }

    table = tables[target_type]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT %s = ANY(likes) AS already_liked
                FROM {table}
                WHERE id = %s
                """,
                (user["id"], target_id)
            )
            result = cur.fetchone()

            if result["already_liked"]:
                cur.execute(
                    f"""
                    UPDATE {table}
                    SET likes = array_remove(likes, %s)
                    WHERE id = %s
                    """,
                    (user["id"], target_id)
                )
                return "لایک شما با موفقیت برداشته شد."

            cur.execute(
                f"""
                UPDATE {table}
                SET likes = array_append(likes, %s)
                WHERE id = %s
                """,
                (user["id"], target_id)
            )

    messages = {
        "post": "پست با موفقیت لایک شد.",
        "comment": "کامنت با موفقیت لایک شد.",
        "reply": "ریپلای با موفقیت لایک شد."
    }

    return messages[target_type]


# --------------------------------------------------
# Reactions
# --------------------------------------------------

@app.post("/Reaction")
def reaction(
    re_action: str,
    target_id: int,
    user: dict = Depends(get_current_user),
    post: dict = Depends(get_current_post_by_target)
):
    if re_action not in Reactions:
        raise HTTPException(
            status_code=422,
            detail="Invalid reaction. This reaction is not allowed."
        )

    user_name = user["user_name"]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT reactions ? %s AS already_reacted,
                       reactions ->> %s AS current_reaction
                FROM posts
                WHERE id = %s
                """,
                (user_name, user_name, target_id)
            )
            result = cur.fetchone()

            if (
                result["already_reacted"]
                and result["current_reaction"] == re_action
            ):
                cur.execute(
                    """
                    UPDATE posts
                    SET reactions = reactions - %s
                    WHERE id = %s
                    """,
                    (user_name, target_id)
                )
                return "ری اکشن شما برای پست برداشته شد."

            cur.execute(
                """
                UPDATE posts
                SET reactions = reactions || jsonb_build_object(%s, %s)
                WHERE id = %s
                """,
                (user_name, re_action, target_id)
            )

            if result["already_reacted"]:
                return "ری اکشن شما برای پست تغییر کرد."

    return "ری اکشن شما برای پست اضافه شد."


# --------------------------------------------------
# Create post / comment / reply
# --------------------------------------------------

@app.post("/share-post")
def share_post(
    post: Post,
    name: str | None = None,
    user: dict = Depends(get_current_user)
):
    if user["id"] != 1:
        raise HTTPException(status_code=403, detail="You are not Admin")

    if name is not None and name != user["name"]:
        raise HTTPException(status_code=403, detail="Invalid display name")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO posts
                (user_id, name, user_name, title, text, likes, reactions)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    user["id"],
                    user["name"],
                    user["user_name"],
                    post.Title,
                    post.Text,
                    [],
                    {}
                )
            )
            new_post = cur.fetchone()

    return {
        "message": "Post created successfully",
        "post_id": new_post["id"]
    }


@app.post("/Comment")
def comment_for_post(
    comment: Comment,
    post: dict = Depends(get_current_post),
    user: dict = Depends(get_current_user)
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO comments
                (user_id, name, user_name, post_id, text, likes, reactions)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    user["id"],
                    user["name"],
                    user["user_name"],
                    post["id"],
                    comment.Text,
                    [],
                    {}
                )
            )
            new_comment = cur.fetchone()

    return {
        "message": "Comment created successfully",
        "comment_id": new_comment["id"]
    }


@app.post("/reply-to-comment")
def reply(
    r_comment: Comment,
    user_name_audience: str,
    comment: dict = Depends(get_current_comment),
    audience: dict = Depends(get_current_audience),
    user: dict = Depends(get_current_user),
    reply_id: int | None = None
):
    with get_connection() as conn:
        with conn.cursor() as cur:

            if reply_id is None:
                cur.execute(
                    """
                    INSERT INTO replys
                    (user_id, name, user_name, comment_or_reply_id,
                     text, likes, reply_to_user_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        user["id"],
                        user["name"],
                        user["user_name"],
                        comment["id"],
                        r_comment.Text,
                        [],
                        audience["user_name"]
                    )
                )

            else:
                get_current_reply_in_comment(reply_id, comment["id"])

                cur.execute(
                    """
                    INSERT INTO replys
                    (user_id, name, user_name, comment_id, reply_id,
                     text, likes, reply_to_user_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        user["id"],
                        user["name"],
                        user["user_name"],
                        comment["id"],
                        reply_id,
                        r_comment.Text,
                        [],
                        audience["user_name"]
                    )
                )

            new_reply = cur.fetchone()

    return {
        "message": "reply created successfully",
        "reply_id": new_reply["id"]
    }


# --------------------------------------------------
# Edit post / comment / reply
# --------------------------------------------------

@app.put("/edit-post")
def edit_post(
    edited_post: Post,
    post: dict = Depends(get_current_post),
    user: dict = Depends(get_current_user)
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if user["id"] != 1 and post["user_id"] != user["id"]:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to edit this post"
                )

            cur.execute(
                """
                UPDATE posts
                SET title = %s, text = %s
                WHERE id = %s
                """,
                (edited_post.Title, edited_post.Text, post["id"])
            )

    if user["id"] == 1:
        return "پست کاربر با موفقیت ویرایش شد"

    return "پست شما با موفقیت ویرایش شد."


@app.put("/edit-comment")
def edit_comment(
    edited_comment: Comment,
    comment: dict = Depends(get_current_comment),
    user: dict = Depends(get_current_user)
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if user["id"] != 1 and comment["user_id"] != user["id"]:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to edit this comment"
                )

            cur.execute(
                """
                UPDATE comments
                SET text = %s
                WHERE id = %s
                """,
                (edited_comment.Text, comment["id"])
            )

    if user["id"] == 1:
        return "کامنت کاربر با موفقیت ویرایش شد"

    return "کامنت شما با موفقیت ویرایش شد."


@app.put("/edit-reply")
def edit_reply(
    edited_reply: Comment,
    reply: dict = Depends(get_current_reply),
    user: dict = Depends(get_current_user)
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if user["id"] != 1 and reply["user_id"] != user["id"]:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to edit this reply"
                )

            cur.execute(
                """
                UPDATE replys
                SET text = %s
                WHERE id = %s
                """,
                (edited_reply.Text, reply["id"])
            )

    if user["id"] == 1:
        return "ریپلای کاربر با موفقیت ویرایش شد"

    return "ریپلای شما با موفقیت ویرایش شد."


# --------------------------------------------------
# Read post / comment / reply
# --------------------------------------------------

@app.get("/posts/{post_id}")
def get_posts(posts: dict = Depends(get_current_post)):
    return posts

@app.get("/comments/{comment_id}")
def get_comment(comments: dict = Depends(get_current_comment)):
    return comments

@app.get("/replys/{reply_id}")
def get_replys(replys: dict = Depends(get_current_reply)):
    return replys




@app.get("/posts/{post_id}/comments")
def get_post_comments(
    post: dict = Depends(get_current_post)
):
    with get_connection() as conn:
        with conn.cursor() as cur:

            # دریافت تمام کامنت‌های پست
            cur.execute(
                """
                SELECT *
                FROM comments
                WHERE post_id = %s
                ORDER BY id DESC
                """,
                (post["id"],)
            )
            comments = cur.fetchall()

            # دریافت تمام ریپلای‌ها و زیرمجموعه‌هایشان
            cur.execute(
                """
                WITH RECURSIVE reply_tree AS (

                    SELECT r.*
                    FROM replys AS r
                    JOIN comments AS c
                        ON c.id = r.comment_or_reply_id
                    WHERE c.post_id = %s

                    UNION ALL

                    SELECT r.*
                    FROM replys AS r
                    JOIN reply_tree AS rt
                        ON r.reply_id = rt.id
                )

                SELECT *
                FROM reply_tree
                ORDER BY id ASC
                """,
                (post["id"],)
            )
            replies = cur.fetchall()

    # تبدیل ریپلای‌ها به ساختار درختی
    reply_nodes = {
        reply["id"]: {**reply, "replies": []}
        for reply in replies
    }

    # اتصال ریپلای‌ها به والد خود
    for reply in replies:
        if reply["comment_or_reply_id"] is not None:
            continue

        if reply["reply_id"] is not None:
            parent = reply_nodes.get(reply["reply_id"])
            if parent is not None:
                parent["replies"].append(
                    reply_nodes[reply["id"]]
                )

    # اتصال ریپلای‌های مستقیم به کامنت‌ها
    for comment in comments:
        comment["replies"] = []

        for reply in replies:
            if reply["comment_or_reply_id"] == comment["id"]:
                comment["replies"].append(
                    reply_nodes[reply["id"]]
                )

    return comments



@app.get("/my-posts")
def get_my_posts(user: dict = Depends(get_current_user)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM posts
                WHERE user_id = %s
                ORDER BY id DESC
                """,
                (user["id"],)
            )
            posts = cur.fetchall()

    return posts

@app.get("/posts")
def get_posts():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM posts ORDER BY id DESC"
            )
            posts = cur.fetchall()

    return posts

@app.get("/comments")
def get_comments():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM comments ORDER BY id DESC"
            )
            comments = cur.fetchall()

    return comments

@app.get("/replys")
def get_replys():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM replys ORDER BY id DESC"
            )
            replys = cur.fetchall()

    return replys

# --------------------------------------------------
# Delete post / comment / reply
# --------------------------------------------------

@app.delete("/delet-post")
def delete_post(
    post: dict = Depends(get_current_post),
    user: dict = Depends(get_current_user)
):
    with get_connection() as conn:
        with conn.cursor() as cur:

            if user["id"] != 1 and post["user_id"] != user["id"]:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to delete this post"
                )

            # حذف تمام ریپلای‌های مربوط به کامنت‌های این پست
            cur.execute(
                """
                WITH RECURSIVE reply_tree AS (
                    SELECT r.id
                    FROM replys AS r
                    JOIN comments AS c
                        ON r.comment_or_reply_id = c.id
                    WHERE c.post_id = %s

                    UNION

                    SELECT r.id
                    FROM replys AS r
                    JOIN reply_tree AS rt
                        ON r.reply_id = rt.id
                )
                DELETE FROM replys
                WHERE id IN (SELECT id FROM reply_tree)
                """,
                (post["id"],)
            )

            # حذف تمام کامنت‌های پست
            cur.execute(
                "DELETE FROM comments WHERE post_id = %s",
                (post["id"],)
            )

            # حذف خود پست
            cur.execute(
                "DELETE FROM posts WHERE id = %s",
                (post["id"],)
            )

    if user["id"] == 1:
        return "پست کاربر و تمام محتویات آن حذف شدند"

    return "پست شما و تمام محتویات آن حذف شدند."

@app.delete("/delet-comment")
def delete_comment(
    comment: dict = Depends(get_current_comment),
    user: dict = Depends(get_current_user)
):
    with get_connection() as conn:
        with conn.cursor() as cur:

            if user["id"] != 1 and comment["user_id"] != user["id"]:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to delete this comment"
                )

            # حذف تمام ریپلای‌ها و زیرمجموعه‌هایشان
            cur.execute(
                """
                WITH RECURSIVE reply_tree AS (
                    SELECT id
                    FROM replys
                    WHERE comment_or_reply_id = %s

                    UNION

                    SELECT r.id
                    FROM replys AS r
                    JOIN reply_tree AS rt
                        ON r.reply_id = rt.id
                )
                DELETE FROM replys
                WHERE id IN (SELECT id FROM reply_tree)
                """,
                (comment["id"],)
            )

            # حذف کامنت اصلی
            cur.execute(
                "DELETE FROM comments WHERE id = %s",
                (comment["id"],)
            )

    if user["id"] == 1:
        return "کامنت کاربر و تمام ریپلای‌های آن حذف شدند"

    return "کامنت شما و تمام ریپلای‌های آن حذف شدند."

@app.delete("/delet-reply")
def delete_reply(
    reply: dict = Depends(get_current_reply),
    user: dict = Depends(get_current_user)
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if user["id"] != 1 and reply["user_id"] != user["id"]:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to delete this reply"
                )
            

            cur.execute(
                """
                WITH RECURSIVE reply_tree AS (
                    SELECT id
                    FROM replys
                    WHERE reply_id = %s

                    UNION ALL

                    SELECT r.id
                    FROM replys AS r
                    JOIN reply_tree AS rt
                        ON r.reply_id = rt.id
                )
                DELETE FROM replys
                WHERE id IN (SELECT id FROM reply_tree)
                """,
                (reply["id"],)
            )

            cur.execute(
                "DELETE FROM replys WHERE id = %s",
                (reply["id"],)
            )

    if user["id"] == 1:
        return "ریپلای کاربر با موفقیت حذف شد"

    return "ریپلای شما با موفقیت حذف شد."


# --------------------------------------------------
# General
# --------------------------------------------------

@app.get("/")
def home():
    return FileResponse("frontend/index.html")


@app.get("/test-db")
def test_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS value")
            result = cur.fetchone()

    return {"database": result["value"]}
