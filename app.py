from fastapi import FastAPI
from uuid import uuid4
import re
import json

app = FastAPI()

@app.get("/API/login")
def login(nickname: str, password: str):
    with open("closedfiles/db.txt") as f:
        entry = f.readline().split()
        while entry != []:
            if (entry[0] == nickname and entry[1] == password):
                return entry[2]
            entry = f.readline().split()
        return -1

@app.get("/API/registration")
def registration(nickname: str, password: str):
    with open("closedfiles/db.txt") as f:
        entry = f.readline().split()
        while entry != []:
            if (entry[0] == nickname):
                return -1
            entry = f.readline().split()
    uuid = uuid4()
    with open("closedfiles/db.txt", "a") as f:
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

@app.get("/API/scan")
def scan(code: str, uuid: str):
    appdata = dict()
    with open("openfiles/appdata.json") as f:
        appdata = json.load(f)
    #
    userdata = dict()
    try:
        with open(f"openfiles/{uuid}.json", "r") as f:
            userdata = json.load(f)
    except FileNotFoundError:
        return -1
    #
    try:
        with open("closedfiles/codes.txt", "r") as f:
            entry = f.readline().split()
            while entry != []:
                if (entry[0] == code):
                    if(userdata["inventory"].get(entry[1], -1) == -1):
                        userdata["inventory"] = int(entry[2])
                    else:
                        userdata["inventory"] += int(entry[2])
                userdata["created"] = list(set(userdata["created"]).add(entry[1]))
                #
                userdata["EXP"] += int(entry[3])
                if (userdata["EXP"] >= appdata["levelup-exp"][userdata["LVL"]+1]):
                    userdata["EXP"] -= appdata["levelup-exp"][userdata["LVL"]+1]
                    userdata["LVL"] += 1
                entry = f.readline().split()
                #
                with open(f"openfiles/{uuid}.json", "w") as usrf:
                    json.dump(userdata, usrf)
                return 0
            return -1
    except FileNotFoundError:
        return -2

@app.get("/API/admin/makecode")
def makecode(code: str, element: str, count: int, exp: int, password: str):
    with open("closedfiles/admin.code", "r") as f:
        if (password != f.read().replace("\n", "")):
            return "Heeey! You're not the administrator! What are you doing here? Get away!"
    #
    if (re.match(r'^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$', code) == None):
        return "Bruh. R u dumb? That's NOT a valid uuid. idioooooot..."
    #
    with open("closedfiles/codes.txt", "a") as f:
        f.write(f"{code} {element} {count} {exp}\n")
    return {"code": code, "msg":"Code added"}