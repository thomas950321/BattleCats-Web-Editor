from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

app = FastAPI(title="BCSFE Web Interface API")

# 資料模型定義
class SaveLogin(BaseModel):
    transfer_code: str
    confirmation_code: str
    country_code: str = "en"
    game_version: str = "13.0.0"

class ItemUpdate(BaseModel):
    catfood: Optional[int] = None
    xp: Optional[int] = None
    normal_tickets: Optional[int] = None
    rare_tickets: Optional[int] = None
    platinum_tickets: Optional[int] = None
    legend_tickets: Optional[int] = None

class SaveDataResponse(BaseModel):
    inquiry_code: str
    catfood: int
    xp: int
    normal_tickets: int
    rare_tickets: int
    platinum_tickets: int
    legend_tickets: int
    tutorial_cleared: bool
    # 進階進度可以在之後擴充

@app.get("/")
async def root():
    return {"message": "BCSFE Web API is running"}

@app.post("/login")
async def login(credentials: SaveLogin):
    # TODO: 串接 bcsfe.core.server.ServerHandler.from_codes
    return {"status": "success", "message": "Logged in and save fetched (Mock)"}

@app.get("/save/get")
async def get_save():
    # TODO: 回傳目前 Session 中的存檔數據
    return {
        "catfood": 20000,
        "xp": 99999999,
        "normal_tickets": 100,
        "rare_tickets": 100,
        "platinum_tickets": 9,
        "legend_tickets": 4
    }

@app.post("/save/patch")
async def patch_save(updates: ItemUpdate):
    # TODO: 套用修改至記憶體中的 SaveFile 物件
    return {"status": "success", "message": "Save patched in memory"}

@app.post("/save/upload")
async def upload_save():
    # TODO: 執行上傳並回傳新碼
    return {
        "status": "success",
        "new_transfer_code": "mock_code_123",
        "new_confirmation_code": "4567"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
