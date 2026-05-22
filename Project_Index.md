# 📋 Project Index — Battle Cats Web Editor

> **最後更新**：2026-05-23 | **維護者**：AI Tech Lead
> **目的**：此文件為專案的唯一架構藍圖，是 Codebase 盤點的 Single Source of Truth。

---

## 1. 專案總覽

| 項目 | 內容 |
|------|------|
| **專案名稱** | Battle Cats Web Editor（貓咪大戰爭網頁修改器）|
| **版本** | Web Edition 1.0.2 |
| **授權** | GNU GPLv3 |
| **核心來源** | Fork 自 fieryhenry/BCSFE-Python |
| **部署平台** | Render.com / Hugging Face Spaces（Docker）|
| **倉庫** | thomas950321/BattleCats-Web-Editor |

---

## 2. 技術堆疊

```
Frontend         │  Vanilla HTML5 + CSS3 + JavaScript (無框架)
Backend          │  Python 3.10 + FastAPI 0.115 + Uvicorn 0.30
資料驗證          │  Pydantic v2
核心業務邏輯      │  bcsfe Python 套件 (src/bcsfe/)
容器化            │  Docker (python:3.10-slim)
CI/CD            │  GitHub Actions (自動同步上游更新)
部署             │  Render.com (render.yaml) / HF Spaces (Dockerfile, PORT=7860)
```

---

## 3. 目錄結構

```
BCSFE-Python/
│
├── bcsfe_web/                       # Web 應用程式層（自研）★
│   ├── main.py                      # FastAPI 入口、路由定義、啟動事件
│   ├── models.py                    # Pydantic Request/Response 模型
│   ├── service.py                   # 業務邏輯服務層（核心橋接器）★ 最重要
│   ├── static/
│   │   ├── index.html               # 單頁應用主體（SPA）
│   │   ├── app.js                   # 前端邏輯（事件監聽、API 呼叫）
│   │   └── style.css                # 全域樣式
│   └── test_data/SAVE_DATA          # 測試用存檔（TEST 模式）
│
├── src/bcsfe/core/                  # 核心引擎（上游 BCSFE-Python）
│   ├── __init__.py                  # CoreData 初始化總出口 ★
│   ├── country_code.py
│   ├── game_version.py
│   ├── game/
│   │   ├── catbase/
│   │   │   ├── cat.py               # 貓咪物件核心 (42KB) ★
│   │   │   ├── playtime.py          # 遊玩時間計算
│   │   │   ├── officer_pass.py      # 軍官通行證（含時間戳）
│   │   │   ├── nyanko_club.py       # 帳號身世/俱樂部
│   │   │   ├── talent_orbs.py       # 本能珠系統 (22KB)
│   │   │   └── special_skill.py     # 科技系統
│   │   └── map/
│   │       ├── story.py             # 主線故事章節 (45KB) ★
│   │       ├── event.py             # 活動關卡 (34KB)
│   │       └── aku.py               # 魔王篇
│   ├── io/
│   │   ├── save.py                  # SaveFile 核心物件 (136KB) ★ 最關鍵
│   │   ├── data.py                  # 二進位資料處理
│   │   └── config.py                # 設定檔管理
│   └── server/
│       ├── server_handler.py        # 與 PONOS 伺服器通訊 (23KB) ★
│       └── request.py               # HTTP 請求封裝
│
├── deep_scan.py                     # 帳號安全診斷工具（法醫分析）
├── diagnose_account.py              # 帳號診斷腳本
├── ubers_list.txt                   # 超激稀有角色名稱資料庫 (繁體中文)
├── Project_Index.md                 # ← 本文件
├── Task_Plan.md                     # 開發任務規劃
├── Dev_Status.md                    # 開發進度追蹤
├── Dockerfile                       # 容器化設定
├── render.yaml                      # Render.com 部署設定
└── CHANGELOG_ZH.md                  # 繁體中文更新日誌
```

---

## 4. API 路由（bcsfe_web/main.py）

| 方法 | 路徑 | 功能 | 對應 Service 方法 |
|------|------|------|-----------------|
| GET | `/` | 回傳前端 index.html | — |
| POST | `/login` | 從 PONOS 伺服器下載存檔 | `service.login_and_fetch()` |
| GET | `/save/get` | 取得目前存檔的數據快照 | `service.get_save_data()` |
| POST | `/save/patch` | 修改記憶體內的存檔數據 | `service.patch_items/stages/advanced()` |
| POST | `/save/upload` | 上傳修改後的存檔至 PONOS | `service.upload()` |
| POST | `/save/transplant` | 高安全性帳號進度移植 | `service.transplant_account()` |

---

## 5. BCSFE_Service 方法索引（service.py）

| 方法 | 說明 | 關鍵行為 |
|------|------|---------|
| `login_and_fetch()` | 以轉移碼登入並下載存檔 | 支援 TEST 模式；自動跳過新手教學 |
| `get_save_data()` | 序列化 SaveFile 為前端字典 | 讀取貓罐頭、券、素材、本能珠等 |
| `patch_items()` | 修改基礎資源類數值 | Clamp：catfood ≤ 45,000 |
| `patch_stages()` | 修改關卡/寶物進度 | 支援主線/未來/宇宙/阿庫篇 |
| `patch_advanced()` | 進階功能（批次貓咪、科技）| 支援 `ID-形態` 語法；自動推算等級 |
| `upload()` | 上傳存檔並取得新轉移碼 | 模擬模式下回傳 TEST-SUCCESS |
| `transplant_account()` | 高安全帳號移植 | 保留目標帳 Inquiry Code、清洗時間戳 |

---

## 6. Pydantic 資料模型（models.py）

| 模型 | 用途 |
|------|------|
| `SaveLogin` | 登入請求（轉移碼、認證碼、版本、地區）|
| `ItemUpdate` | 資源修改項目（全部為 Optional）|
| `AdvancedOptions` | 進階功能（cats / tech / progress / special）|
| `StageOptions` | 關卡/寶物選項 |
| `SavePatchRequest` | 整合 Patch 的頂層請求 |
| `TransplantRequest` | 帳號移植請求 |
| `SaveDataResponse` | 存檔數據回應格式 |

---

## 7. 前端 SPA 狀態機（app.js / index.html）

```
[login-panel]
    ↓ 登入成功
[dashboard]
    ├── Tab 1：基礎資源（貓罐頭、XP、各類券、素材）
    ├── Tab 2：進階修改（批次貓咪、科技、關卡、寶物、勳章）
    └── Tab 3：帳號移植（Transplant）
    ↓ 上傳成功
[result-panel]（顯示新轉移碼 + 認證碼）
```

**關鍵前端機制**：
- **髒資料比對**：只上傳與原始值不同的欄位（降低封號風險）
- **localStorage 備援**：防止重整頁面遺失轉移碼
- **全局數值 Clamp**：前端 `change` 事件防止輸入超限
- **批次貓咪格子**：`initCatUnlockGrid()` + `addCatInput()` 動態管理

---

## 8. 資料流示意圖

```
瀏覽器
  ↓ POST /login
FastAPI main.py
  ↓ service.login_and_fetch()
  ↓ core.ServerHandler.from_codes()
PONOS 遊戲伺服器  →  SaveFile 物件（記憶體）
  ↑
  ↓ GET /save/get → JSON 回傳前端
  ↓ POST /save/patch → 修改記憶體 SaveFile
  ↓ POST /save/upload
  ↓ server_handler.get_codes()
PONOS 伺服器  →  新轉移碼 + 認證碼  →  瀏覽器
```

---

## 9. 已知技術債

| 優先級 | ID | 問題 | 說明 |
|--------|-----|------|------|
| 高 | BUG-001 | 無 Session 隔離 | `service` 是單例，多人同時使用互蓋存檔 |
| 高 | BUG-002 | 遊戲版本過舊 | `models.py` 預設 `13.0.0`，目前遊戲為 `15.x` |
| 中 | BUG-003 | 貓咪 ID 無範圍驗證 | 超出範圍時無明確錯誤訊息 |
| 低 | BUG-004 | 暫存檔未清理 | `unlock_batch.py`、`ubers_list_utf8.txt` 等 |

---

## 10. 部署設定速查

| 平台 | 設定檔 | Port | 啟動命令 |
|------|--------|------|---------|
| Render | `render.yaml` | `$PORT` | `uvicorn bcsfe_web.main:app --host 0.0.0.0 --port $PORT` |
| HF Spaces | `Dockerfile` | `7860` | `python bcsfe_web/main.py` |
| 本地開發 | — | `8000` | `python bcsfe_web/main.py` |
