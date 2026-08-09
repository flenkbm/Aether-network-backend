from fastapi import FastAPI

app = FastAPI()

@app.get("/API/login")
def login(nickname: str, password: str):
    with open("closedfiles/testdb.txt") as f:
        entry = f.readline().split()
        while entry != []:
            if (entry[0] == nickname and entry[1] == password):
                return int(entry[2])
            entry = f.readline().split()
