from fastapi import FastAPI

app = FastAPI()

@app.get("/API/helloworld")
def hello():
    return "Hello, World! And blahblahblah"
