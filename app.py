from fastapi import FastAPI
from uuid import uuid4
import re
import json
from time import time_ns
import sqlite3 as sqlite
from hashlib import sha256


def time_ms():
    return time_ns()//1000000

def hashstr(string: str):
    return sha256(bytes(string, encoding="utf-8")).hexdigest()


app = FastAPI()


cnnct = sqlite.connect("closedfiles/db.db")
cnnct.setconfig(sqlite.SQLITE_DBCONFIG_ENABLE_FKEY, True)
crsr = cnnct.cursor()
crsr.execute("""create table if not exists Credentials (
username text,
pswd_hash text,
uuid text,
primary key(username, uuid)
)""")
crsr.execute("""create table if not exists Userdata (
uuid text,
username text,
inventory text,
exp integer,
lvl integer,
scans text,
primary key(uuid, username),
constraint fk_uuid foreign key(uuid) references Credentials(uuid),
constraint fk_username foreign key(username) references Credentials(username)
)""")
crsr.execute("""create table if not exists Sessions (
sid text,
uuid text,
timestamp integer,
primary key(sid, uuid),
constraint fk_uuid foreign key(uuid) references Credentials(uuid)
)""")
crsr.close()


@app.get("/API/userdata/{sid}")
def getUserData(sid: str):
    crsr = cnnct.cursor()
    #
    crsr.execute()

@app.post("/API/login")
def login(username: str, password: str):
    crsr = cnnct.cursor()
    #
    crsr.execute(f"select uuid from Credentials where \
                 username='{username}' and \
                 pswd_hash='{hashstr(password)}'")
    uuid = crsr.fetchone()
    if uuid == None:
        crsr.close()
        return -1
    #
    sid = uuid4()
    crsr.execute(f"select * from Sessions where \
                 uuid={uuid}")
    if crsr.fetchone() == None:
        crsr.execute(f"insert into Sessions values ('{sid}', '{uuid}', {time_ms()})")
    else:
        crsr.execute(f"update Sessions set ('{sid}', {uuid}, {time_ms()}) where uuid='{uuid}'")
    crsr.close()
    return f"{sid}"


@app.post("/API/registration")
def registration(username: str, password: str):
    crsr = cnnct.cursor()
    #
    crsr.execute(f"select * from Credentials where \
                 username='{username}'")
    if crsr.fetchone() != None:
        return -1
    #
    uuid = uuid4()
    crsr.execute(f"insert into Credentials values ('{username}', '{hashstr(password)}', '{uuid}')")
    #
    crsr.execute(f"""insert into Userdata values (
    '{uuid}',
    '{username}',
    '{json.dumps({
        "air": 2,
        "fire": 2,
        "water": 2,
        "earth": 2
    })}',
    {0},
    {0},
    '{json.dumps()}',
    )""")
    #
    sid = uuid4()
    crsr.execute(f"insert into Sessions values ('{sid}', '{uuid}', {time_ms()})")
    crsr.close()
    return f"{sid}"


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
    "created" : ["air", "earth", "fire", "water"],
    "nextscans" : {{}}
}}""")
    return f"{uuid}"

@app.post("/API/scan")
def scan(code: str, uuid: str):
    crsr = cnnct.cursor()
    #
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
    if (userdata["nextscans"].get(code, 0) > time_ms()):
        return -3
    #
    try:
        with open("closedfiles/codes.txt") as f:
            entry = f.readline().split()
            while entry != []:
                if (entry[0] == code):
                    if(userdata["inventory"].get(entry[1], -1) == -1):
                        userdata["inventory"][entry[1]] = int(entry[2])
                    else:
                        userdata["inventory"][entry[1]] += int(entry[2])
                    userdata["created"] = list(set(userdata["created"]).union(set([entry[1]])))
                    #
                    userdata["EXP"] += int(entry[3])
                    if (userdata["EXP"] >= appdata["levelup-exp"][userdata["LVL"]+1]):
                        userdata["EXP"] -= appdata["levelup-exp"][userdata["LVL"]+1]
                        userdata["LVL"] += 1
                    #
                    userdata["nextscans"][code] = time_ms()+int(entry[4])
                    #
                    with open(f"openfiles/{uuid}.json", "w") as usrf:
                        json.dump(userdata, usrf)
                    return 0
                #
                entry = f.readline().split()
            return -1
    except FileNotFoundError:
        return -2

@app.get("/API/admin/makecode")
def makecode(code: str, element: str, count: int, exp: int, scanDelay: int, password: str):
    with open("closedfiles/admin.code", "r") as f:
        if (password != f.read().replace("\n", "")):
            return "Heeey! You're not the administrator! What are you doing here? Get away!"
    #
    if (re.match(r'^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$', code) == None):
        return "Bruh. R u dumb? That's NOT a valid uuid. idioooooot..."
    #
    with open("closedfiles/codes.txt", "a") as f:
        f.write(f"{code} {element} {count} {exp} {scanDelay}\n")
    return {"code": code, "msg":"Code added"}