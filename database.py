import psycopg

def get_connection():
    return psycopg.connect(
        dbname="signala",
        user="postgres",
        password="pcobnekhg2l'5wnclnfd$%eiyt95pjrglnb!@#$%^&*uh'j086uvnyfn5..cokdpojj*/*/*/*/*wfnnyukj*+bj6utgv+8+[hj",
        host="localhost",
        port=5432
    )

