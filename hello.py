# simple_test.py
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World", "status": "success"}

if __name__ == "__main__":
    print("开始启动服务...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")