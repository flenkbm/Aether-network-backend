from fastapi import FastAPI
from uuid import uuid4

app = FastAPI()

@app.get("/API/login")
def login(nickname: str, password: str):
    with open("closedfiles/testdb.txt") as f:
        entry = f.readline().split()
        while entry != []:
            if (entry[0] == nickname and entry[1] == password):
                return entry[2]
            entry = f.readline().split()
        return -1

@app.get("/API/registration")
def registration(nickname: str, password: str):
    with open("closedfiles/testdb.txt") as f:
        entry = f.readline().split()
        while entry != []:
            if (entry[0] == nickname):
                return -1
            entry = f.readline().split()
    uuid = uuid4()
    with open("closedfiles/testdb.txt", "a") as f:
        f.write(f"{nickname} {password} {uuid}\n")
    with open(f"openfiles/{uuid}.json", "x") as f:
        f.write(f"""{{
    "nickname" : "{nickname}",
    "EXP" : 0,
    "LVL" : 0,
    "inventory" : {{"air":2, "earth":2, "fire":2, "water":2}},
    "created" : ["air", "earth", "fire", "water"]
}}""")
    return f"{uuid}"