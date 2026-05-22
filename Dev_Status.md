# 🚦 Dev Status — Battle Cats Web Editor

> **最後更新**：2026-05-23 03:37
> **目前 Sprint**：Sprint 0（技術債清償）準備中

---

## ✅ 已完成事項

### Web 核心功能
- [x] FastAPI 後端架構（main.py + service.py + models.py）
- [x] 前端 SPA 三層狀態機（login → dashboard → result）
- [x] 基礎資源修改（貓罐頭、XP、NP、領導力、各類券）
- [x] 列表型資源修改（戰鬥道具、喵力達、貓眼石、貓薄荷、基地素材）
- [x] 本能珠（Talent Orbs）按 S 屬性分群顯示與修改
- [x] 遊玩時間（play_time）修改

### 進階功能
- [x] 高安全性帳號移植（Safe Transplant Pro Max）
- [x] 批次貓咪解鎖（ID-形態語法，自動推算等級）
- [x] 科技（Special Skills）全升
- [x] 主線/未來/宇宙章節通關 + 全金寶
- [x] 自動跳過新手教學
- [x] 封號標記（Ban Flag）顯示

### 安全機制
- [x] 前端 Clamp：catfood ≤ 45,000 / rare_tickets ≤ 299
- [x] 後端 Clamp：所有資源值強制安全上限
- [x] 髒資料比對（只上傳有變動的欄位）
- [x] localStorage 備援轉移碼

### 資料庫與工具
- [x] ubers_list.txt：完整繁體中文超激稀有角色名稱（850+ 筆）
- [x] 預設地區：TW 台版
- [x] deep_scan.py：帳號法醫分析（時間戳、遊玩時數比、封號標記）
- [x] diagnose_account.py：詳細診斷腳本

### 專案管理文件
- [x] Project_Index.md（架構索引）
- [x] Task_Plan.md（任務計畫）
- [x] Dev_Status.md（本文件）

---

## 🚀 目前正在執行的區塊

> **Sprint 0 — 技術債清償** 剛啟動，尚未開始執行 Ticket

| Ticket | 狀態 | 說明 |
|--------|------|------|
| T-001 | 🔲 待執行 | 清理暫存檔 + 更新 .gitignore |
| T-002 | 🔲 待執行 | 更新 models.py 預設版本 13.0.0 → 15.3.0 |
| T-003 | 🔲 待執行 | 更新 CHANGELOG_ZH.md |

---

## 🐛 待修復的已知 Bug

| ID | 嚴重度 | 問題描述 | 影響範圍 |
|----|--------|---------|---------|
| BUG-001 | 🔴 高 | service 單例無 Session 隔離，多人同時操作互蓋存檔 | 多人使用場景 |
| BUG-002 | 🔴 高 | models.py 預設版本 `13.0.0`，與目前遊戲 `15.x` 不符 | 登入成功率 |
| BUG-003 | 🟡 中 | 貓咪 ID 超出 SaveFile 範圍時無明確前端錯誤訊息 | patch_advanced |
| BUG-004 | 🟢 低 | ubers_list_utf8.txt 殘留根目錄未清理 | 專案整潔度 |
| BUG-005 | 🟢 低 | unlock_batch.py / diagnose_account.py 未加入 .gitignore | 倉庫整潔度 |

---

## 📝 下一步待辦（Next Actions）

1. 執行 **T-002**：更新 `models.py` 預設版本為 `15.3.0`（低風險，10 分鐘）
2. 執行 **T-001**：整理 `.gitignore`，清理根目錄暫存檔
3. 執行 **T-003**：補充 CHANGELOG_ZH.md 近期變更
4. Sprint 0 完成後 → 討論 Sprint 1 優先項目

---

## 📊 功能完成度

```
基礎資源修改    ████████████  100%
進階貓咪管理    ████████░░░░   70%  (缺：搜尋補全、已擁有清單)
關卡/寶物管理   ████████████  100%
本能珠修改      ████████░░░░   75%  (缺：一鍵全滿)
帳號移植        ████████████  100%
安全診斷        ████████░░░░   70%  (缺：整合進 Web UI)
Session 管理   ████░░░░░░░░   20%  (無多人隔離)
文件完整度      ████████████  100%  ← 本次新增
```
