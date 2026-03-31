from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from bcsfe_web.models import SaveLogin, ItemUpdate, SaveDataResponse, SavePatchRequest
from bcsfe_web.service import service
import uvicorn
import os
import traceback
import sys

# 確保能加載 src 中的 bcsfe 模組
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "..", "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from bcsfe import core

app = FastAPI(title="BCSFE Web Interface API")

# 全域異常處理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": traceback.format_exc()},
    )

# 初始化核心數據
@app.on_event("startup")
async def startup_event():
    core.core_data.init_data()

# 掛載靜態檔案 (使用相對路徑)
static_path = os.path.join(current_dir, "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/")
async def root():
    return FileResponse(os.path.join(static_path, "index.html"))

@app.post("/login")
async def login(credentials: SaveLogin):
    success, message = await service.login_and_fetch(
        credentials.transfer_code,
        credentials.confirmation_code,
        credentials.country_code,
        credentials.game_version
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"status": "success", "message": message}

@app.get("/save/get")
async def get_save():
    data = service.get_save_data()
    if not data:
        raise HTTPException(status_code=404, detail="存檔未載入")
    return data

@app.post("/save/patch")
async def patch_save(updates: SavePatchRequest):
    if updates.items:
        service.patch_items(updates.items.model_dump(exclude_unset=True))
    if updates.stages:
        service.patch_stages(updates.stages.model_dump(exclude_unset=True))
    if updates.advanced:
        await service.patch_advanced(updates.advanced.model_dump(exclude_unset=True))
    return {"status": "success", "message": "Save patched in memory"}

@app.post("/save/upload")
async def upload_save():
    result, message = await service.upload()
    if not result:
        raise HTTPException(status_code=400, detail=message)
    return {
        "status": "success",
        "new_transfer_code": result["transfer_code"],
        "new_confirmation_code": result["confirmation_code"]
    }

if __name__ == "__main__":
    # Render 會自動提供 PORT 環境變數
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
