import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
# pyrefly: ignore [missing-import]
from bcsfe_web.models import SaveLogin, SavePatchRequest, TransplantRequest, RestoreRequest
# pyrefly: ignore [missing-import]
from bcsfe_web.service import session_manager, BCSFE_Service
from bcsfe_web import scanner
import uvicorn
import traceback
import sys

# 確保能加載 src 中的 bcsfe 模組
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "..", "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from bcsfe import core

app = FastAPI(title="BCSFE Web Interface API")

def get_service_or_404(session_token: str) -> BCSFE_Service:
    svc = session_manager.get(session_token)
    if svc is None:
        raise HTTPException(status_code=401, detail="Session 已過期或無效，請重新登入")
    return svc

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

# 定期清理過期 session（每 5 分鐘）
@app.on_event("startup")
async def schedule_session_cleanup():
    import asyncio
    async def cleanup_loop():
        while True:
            await asyncio.sleep(300)
            expired = session_manager.cleanup_expired()
            if expired:
                print(f"[session] cleaned {expired} expired sessions", flush=True)
    asyncio.create_task(cleanup_loop())

# 掛載靜態檔案 (使用相對路徑)
static_path = os.path.join(current_dir, "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/")
async def root():
    return FileResponse(os.path.join(static_path, "index.html"))

@app.post("/login")
async def login(credentials: SaveLogin):
    session_id = session_manager.create()
    svc = session_manager.get(session_id)
    success, message = await svc.login_and_fetch(
        credentials.transfer_code,
        credentials.confirmation_code,
        credentials.country_code,
        credentials.game_version
    )
    if not success:
        session_manager.delete(session_id)
        raise HTTPException(status_code=400, detail=message)
    return {"status": "success", "message": message, "session_token": session_id}

@app.get("/save/get")
async def get_save(x_session_token: str = Header(...)):
    svc = get_service_or_404(x_session_token)
    data = svc.get_save_data()
    if not data:
        raise HTTPException(status_code=404, detail="存檔未載入")
    return data

@app.post("/save/patch")
async def patch_save(updates: SavePatchRequest, x_session_token: str = Header(...)):
    svc = get_service_or_404(x_session_token)
    if updates.items:
        svc.patch_items(updates.items.model_dump(exclude_unset=True))
    if updates.stages:
        svc.patch_stages(updates.stages.model_dump(exclude_unset=True))
    if updates.advanced:
        await svc.patch_advanced(updates.advanced.model_dump(exclude_unset=True))

    # T-010：回傳批次解鎖的逐一結果
    unlock_results = getattr(svc, "_last_unlock_results", None)
    response = {"status": "success", "message": "Save patched in memory"}
    if unlock_results is not None:
        failed = [r for r in unlock_results if not r["ok"]]
        response["unlock_results"] = unlock_results
        response["unlock_failed_count"] = len(failed)
        # 清除避免殘留
        svc._last_unlock_results = None
    return response

@app.get("/save/diagnose")
async def diagnose_save(x_session_token: str = Header(...)):
    """
    T-024：帳號安全性深度診斷
    對目前記憶體中的存檔執行完整安全審計（基於 account-security-analyzer Skill）。
    回傳結構化 JSON，包含身世、資源、活動強度比對與封號標記。
    """
    svc = get_service_or_404(x_session_token)
    if not svc.current_save:
        raise HTTPException(status_code=404, detail="存檔未載入，請先登入。")
    try:
        report = scanner.run_diagnosis(svc.current_save)
        return {"status": "success", "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"診斷失敗：{str(e)}")

@app.post("/save/upload")
async def upload_save(x_session_token: str = Header(...)):
    svc = get_service_or_404(x_session_token)
    result, message = await svc.upload()
    if not result:
        raise HTTPException(status_code=400, detail=message)
    # 上傳成功後清除 session（一次性使用）
    session_manager.delete(x_session_token)
    return {
        "status": "success",
        "new_transfer_code": result["transfer_code"],
        "new_confirmation_code": result["confirmation_code"]
    }


@app.post("/save/transplant")
async def transplant_save(req: TransplantRequest):
    """
    移植帳號：把來源帳的進度移植到目標帳（空殼），保留目標帳的 Inquiry Code。
    使用獨立 session 避免干擾已登入的使用者。回傳目標帳上傳後的新引繼碼。
    """
    # 建立臨時 session 執行移植，不影響使用者當前 session
    session_id = session_manager.create()
    svc = session_manager.get(session_id)
    try:
        result, message = await svc.transplant_account(
            req.source_transfer_code, req.source_confirmation_code,
            req.target_transfer_code, req.target_confirmation_code,
            req.country_code, req.game_version,
        )
        if not result:
            raise HTTPException(status_code=400, detail=message)
        return {
            "status": "success",
            "new_transfer_code":    result["new_transfer_code"],
            "new_confirmation_code": result["new_confirmation_code"],
        }
    finally:
        session_manager.delete(session_id)


@app.get("/admin/history")
async def get_history():
    try:
        # pyrefly: ignore [missing-import]
        from bcsfe_web.database import get_save_history
        history = get_save_history()
        return {"status": "success", "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取紀錄失敗: {str(e)}")

@app.post("/admin/restore")
async def restore_save(req: RestoreRequest):
    session_id = session_manager.create()
    svc = session_manager.get(session_id)
    try:
        result, message = await svc.restore_save_to_account(
            req.record_id,
            req.target_transfer_code,
            req.target_confirmation_code,
            req.country_code,
            req.game_version
        )
        if not result:
            raise HTTPException(status_code=400, detail=message)
        return {
            "status": "success",
            "new_transfer_code": result["new_transfer_code"],
            "new_confirmation_code": result["new_confirmation_code"]
        }
    finally:
        session_manager.delete(session_id)

@app.delete("/admin/history/{record_id}")
async def delete_record(record_id: int):
    try:
        # pyrefly: ignore [missing-import]
        from bcsfe_web.database import delete_save_record
        delete_save_record(record_id)
        return {"status": "success", "message": "紀錄已刪除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除紀錄失敗: {str(e)}")


if __name__ == "__main__":
    # Render 會自動提供 PORT 環境變數
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
