from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
import re
import json
from time import time_ns
import sqlite3 as sqlite
from hashlib import sha256
from pydantic import BaseModel
import gspread
import pandas as pd


def time_ms():
    return time_ns()//1000000

def hashstr(string: str):
    return sha256(bytes(string, encoding="utf-8")).hexdigest()


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


connect = sqlite.connect("closedfiles/db.db", check_same_thread=False)
crsr = connect.cursor()
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
EXP integer,
LVL integer,
scans text,
primary key(uuid, username)
)""")
crsr.execute("""create table if not exists Sessions (
sid text,
uuid text,
timestamp integer,
primary key(sid, uuid)
)""")
crsr.execute("""create table if not exists Codes (
code text,
element text,
amount integer,
EXP integer,
cooldown integer,
primary key (code)
)""")
crsr.execute("""create temp table if not exists AdminLog (
timestamp integer
)""")
crsr.execute("""insert into AdminLog values (0)""")
connect.commit()
crsr.close()


gc = gspread.service_account()
RECIPES = pd.DataFrame(gc.\
    open_by_url("https://docs.google.com/spreadsheets/d/1y7vBDIC67i9duQCJv5KWvk5D1G5KdPVZg4C5pnqgs04").\
    worksheet("4code").get_all_records())
RECIPES.set_index("index", drop="index", inplace=True)
C_REWARDS = pd.DataFrame(gc.\
    open_by_url("https://docs.google.com/spreadsheets/d/1y7vBDIC67i9duQCJv5KWvk5D1G5KdPVZg4C5pnqgs04").\
    worksheet("EXP").get_all_records())
C_REWARDS.set_index("index", drop="index", inplace=True)
SESION_TIMEOUT = 1000 * 60 * 60 * 12
APPDATA = json.load(open("openfiles/appdata.json"))


def userDataByUUID(uuid: str):
    crsr = connect.cursor()
    crsr.execute(f"select username, inventory, EXP, LVL, scans from Userdata where uuid='{uuid}'")
    raw_userdata = crsr.fetchone()
    crsr.close()
    return {
        "username": raw_userdata[0],
        "inventory": json.loads(raw_userdata[1]),
        "EXP": raw_userdata[2],
        "LVL": raw_userdata[3],
        "scans": json.loads(raw_userdata[4])
    }

def UUIDfromSID(sid: str):
    crsr = connect.cursor()
    crsr.execute(f"select uuid, timestamp from Sessions where sid='{sid}'")
    sd = crsr.fetchone()# session data
    if sd == None:
        crsr.close()
        return -1
    #
    if(sd[1] + SESION_TIMEOUT < time_ms()):
        crsr.execute(f"delete from Sessions where sid='{sid}'")
        connect.commit()
        crsr.close()
        return -1
    #
    return sd[0]

def updateLVL(userdata: dict):
    while userdata["EXP"] >= APPDATA["levelup-EXP"][userdata["LVL"]+1]:
        userdata["EXP"] -= APPDATA["levelup-EXP"][userdata["LVL"]+1]
        userdata["LVL"] += 1

def updateUserData(userdata: dict, uuid: str):
    crsr = connect.cursor()
    #
    crsr.execute(f"""update Userdata set 
        username='{userdata["username"]}',
        inventory='{json.dumps(userdata["inventory"])}',
        EXP={userdata["EXP"]},
        LVL={userdata["LVL"]},
        scans='{json.dumps(userdata["scans"])}'
        where uuid='{uuid}'""")
    #
    connect.commit()
    crsr.close()


@app.get("/API/userdata/{sid}")
def getUserData(sid: str):
    uuid = UUIDfromSID(sid)
    if uuid == -1:
        return -1
    #
    return userDataByUUID(uuid)

class log_data(BaseModel):
    username: str
    password: str

@app.post("/API/login")
def login(dt: log_data):
    crsr = connect.cursor()
    #
    crsr.execute(f"select uuid from Credentials where \
                 username='{dt.username}' and \
                 pswd_hash='{hashstr(dt.password)}'")
    uuid = crsr.fetchone()
    if uuid == None:
        crsr.close()
        return -1
    uuid = uuid[0]
    if uuid[:16] == "banned#checkcode":
        return {"banned"}
    #
    sid = uuid4()
    crsr.execute(f"select * from Sessions where uuid='{uuid}'")
    if crsr.fetchone() == None:
        crsr.execute(f"insert into Sessions values ('{sid}', '{uuid}', {time_ms()})")
    else:
        crsr.execute(f"update Sessions set sid='{sid}', timestamp={time_ms()} where uuid='{uuid}'")
    connect.commit()
    crsr.close()
    return f"{sid}"


@app.post("/API/registration")
def registration(dt: log_data):
    crsr = connect.cursor()
    #
    crsr.execute(f"select * from Credentials where \
                 username='{dt.username}'")
    if crsr.fetchone() != None:
        return -1
    #
    uuid = uuid4()
    crsr.execute(f"insert into Credentials values ('{dt.username}', '{hashstr(dt.password)}', '{uuid}')")
    #
    crsr.execute(f"""insert into Userdata values (
    '{uuid}',
    '{dt.username}',
    '{json.dumps({
        "air": 2,
        "fire": 2,
        "water": 2,
        "earth": 2
    })}',
    0,
    0,
    '{json.dumps({"":""})}'
    )""")
    #
    sid = uuid4()
    crsr.execute(f"insert into Sessions values ('{sid}', '{uuid}', {time_ms()})")
    connect.commit()
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

class scan_data(BaseModel):
    code: str
    sid: str

@app.post("/API/scan")
def scan(dt: scan_data):
    crsr = connect.cursor()
    code = dt.code
    sid = dt.sid
    #
    uuid = UUIDfromSID(sid)
    if uuid == -1:
        crsr.close()
        return -1
    #
    crsr.execute(f"select element, amount, EXP, cooldown from Codes where code='{code}'")
    res = crsr.fetchone()
    if res == None:
        crsr.close()
        return -2
    #
    userdata = userDataByUUID(uuid)
    if userdata["scans"].get(code, 0) + res[3] > time_ms():
        crsr.close()
        return -3
    #
    userdata["EXP"] += res[2]
    updateLVL(userdata)
    if (userdata["inventory"].get(res[0], -1) == -1):
        userdata["inventory"][res[0]] = res[1]
    else:
        userdata["inventory"][res[0]] += res[1]
    userdata["scans"][code] = time_ms()
    #
    updateUserData(userdata, uuid)
    crsr.close()
    return 0
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
                    if (userdata["EXP"] >= appdata["levelup-EXP"][userdata["LVL"]+1]):
                        userdata["EXP"] -= appdata["levelup-EXP"][userdata["LVL"]+1]
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

@app.get("/API/toplist")
def toplist():
    crsr = connect.cursor()
    crsr.execute("select username, LVL from Userdata order by LVL desc, EXP desc")
    res = crsr.fetchall()[:10]
    for i in range(len(res)):
        if res[i][1] < 0:
            res = res[:i]
            break
    crsr.close()
    return res

class craft_data(BaseModel):
    sid: str
    el1: str
    el2: str

@app.post("/API/attemptCraft")
def attemptCraft(dt: craft_data):
    uuid = UUIDfromSID(dt.sid)
    if uuid == -1:
        return -1
    #
    userdata = userDataByUUID(uuid)
    if (userdata["inventory"].get(dt.el1, -1) < 1) or (userdata["inventory"].get(dt.el2, -1) < 1):
        return -2
    #
    try:
        if RECIPES[dt.el1][dt.el2] == "":
            return -3
    except Exception as e:
        print(e)
        return -3
    userdata["inventory"][dt.el1] -= 1
    userdata["inventory"][dt.el2] -= 1
    userdata["inventory"][RECIPES[dt.el1][dt.el2]] = userdata["inventory"].get(RECIPES[dt.el1][dt.el2], 0)+1
    userdata["EXP"] += C_REWARDS[dt.el1][dt.el2]
    updateLVL(userdata)
    updateUserData(userdata, uuid)
    return 0

class makecode_data(BaseModel):
    code: str
    element: str
    amount: int
    exp: int
    cooldown: int
    password: str

def checkadmin(password):
    with open("closedfiles/admin.code", "r") as f:
        crsr = connect.cursor()
        crsr.execute("select * from AdminLog order by timestamp desc")
        lastlogs = crsr.fetchall()[:20]
        if (lastlogs[-1][0] + 3600000 >= time_ms() and len(lastlogs) == 20):
            return False
        if (hashstr(password) != f.read().replace("\n", "")):
            crsr.execute("insert into AdminLog values ("+str(time_ms())+")")
            connect.commit()
            crsr.close()
            return False
        else:
            crsr.close()
            return True

@app.post("/API/admin/makecode")
def makecode(dt: makecode_data):
    if not checkadmin(dt.password):
        return "Heeey! You're not the administrator! What are you doing here? Get away!"
    #
    if (re.match(r'^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$', dt.code) == None):
        return "Bruh. That's NOT a valid uuid."
    #
    crsr = connect.cursor()
    crsr.execute(f"insert into Codes values ('{dt.code}', '{dt.element}', {dt.amount}, {dt.exp}, {dt.cooldown})")
    connect.commit()
    crsr.close()
    return {"code": dt.code, "msg":"Code added"}
print(makecode(makecode_data(code="1d44c80d-ef01-45ac-9eb1-81093f8849ce", element="fire", amount=1, exp=20, cooldown=7200000, password="-Q3kYMKB53dnqt3o7DNe9gNYRwY_QNtA86EZSLpc_hw")))

class modifyuser_data(BaseModel):
    username: str
    variable: str
    value: str
    password: str

@app.post("/API/admin/modifyuser")
def modifyuser(dt: modifyuser_data):
    if not checkadmin(dt.password):
        return "Heeey! You're not the administrator! What are you doing here? Get away!"
    #
    crsr = connect.cursor()
    crsr.execute(f"select uuid from Credentials where username='{dt.username}'")
    uuid = crsr.fetchone()
    if uuid == None:
        crsr.close()
        return "User not found :("
    uuid = uuid[0]
    userdata = userDataByUUID(uuid)
    if dt.variable in ["EXP", "LVL"]:
        userdata[dt.variable] = int(dt.value)
        updateLVL(userdata)
    elif dt.variable == "username":
        userdata[dt.variable] = dt.value
    elif dt.variable in ["inventory", "scans"]:
        userdata[dt.variable][json.loads(dt.value)[0]] = json.loads(dt.value)[1]
    updateUserData(userdata, uuid)
    crsr.close()
    return userDataByUUID(uuid)


class getuser_data(BaseModel):
    username: str
    password: str

@app.post("/API/admin/getuser")
def getuser(dt: getuser_data):
    if not checkadmin(dt.password):
        return "Heeey! You're not the administrator! What are you doing here? Get away!"
    #
    crsr = connect.cursor()
    crsr.execute(f"select uuid from Credentials where username='{dt.username}'")
    uuid = crsr.fetchone()
    if uuid == None:
        crsr.close()
        return "User not found :("
    uuid = uuid[0]
    crsr.close()
    return userDataByUUID(uuid)

class banuser_data(BaseModel):
    username: str
    password: str

@app.post("/API/admin/banuser")
def banuser(dt: banuser_data):
    if not checkadmin(dt.password):
        return "Heeey! You're not the administrator! What are you doing here? Get away!"
    #
    crsr = connect.cursor()
    crsr.execute(f"select uuid from Credentials where username='{dt.username}'")
    uuid = crsr.fetchone()[0]
    crsr.execute(f"update Credentials set uuid='{'banned#checkcode'+uuid}' where username='{dt.username}'")
    try:
        crsr.execute(f"delete from Sessions where uuid='{uuid}'")
    except:
        pass
    userdata = userDataByUUID(uuid)
    userdata["LVL"] -= 100
    updateUserData(userdata, uuid)
    connect.commit()
    crsr.close()
    return {"user":dt.username,"res":"banned","uuid":uuid}