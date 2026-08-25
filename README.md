---
title: Battlecats Web Editor
emoji: 🐱
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Battle Cats Web Editor | 貓咪大戰爭網頁修改器

這是基於 [BCSFE-Python](https://github.com/fieryhenry/BCSFE-Python) 核心所開發的網頁修改器。提供網頁介面，方便進行《貓咪大戰爭》的存檔管理與編輯。

---

## 功能特色

*   **存檔移植與複製**
    *   **無損拷貝**：將來源存檔的完整進度（貓咪、金寶、關卡進度等）複製到目標帳號。
    *   **保留身分**：保留目標帳號的「詢問碼 (Inquiry Code)」與相關憑證，避免帳號衝突。
    *   **安全清理**：重設存檔中的時間戳記，並清除封號標記 (banned, show_ban_message)。
    *   **一鍵自動註冊**（新功能）：複製時可選擇自動在伺服器註冊一個全新空殼帳號，不需要手動準備或輸入空殼帳的引繼代碼。
*   **修改數值比對 (Dirty Check)**：只會上傳有被修改的欄位，降低上傳損壞或異常的機率。
*   **完整資源編輯**：
    *   基礎資源：貓罐頭、經驗值 (XP)、NP、領導力、遊玩時間、黃金會員續訂次數等。
    *   轉蛋券：銀券、金券、白金券、傳說券、白金碎片。
    *   道具與素材：戰鬥道具、喵力達、貓眼石、貓薄荷與獸石、基地素材。
    *   其他：本能玉、迷宮獎牌等。

---

## 快速開始

### 修改步驟
1.  在遊戲中進入「設定」 -> 「轉移引繼資料」。
2.  點擊「上傳存檔到伺服器」，記下**引繼碼 (Transfer Code)** 與 **認證碼 (Confirmation Code)**。
3.  在修改器網頁輸入代碼，並選擇對應的地區（EN, TW, JP, KR）與遊戲版本。
4.  完成編輯後點擊「儲存並上傳至伺服器」，取得新的引繼碼。
5.  在遊戲中選擇「恢復引繼資料」並輸入新代碼即可。

---

## 本地開發與部署

如果您想在本地執行此專案：

1.  **複製專案**
    ```bash
    git clone https://github.com/thomas950321/BattleCats-Web-Editor.git
    cd BattleCats-Web-Editor
    ```
2.  **安裝依賴**
    ```bash
    pip install -r requirements.txt
    ```
3.  **啟動服務**
    ```bash
    python bcsfe_web/main.py
    ```
4.  **訪問網頁**
    開啟瀏覽器前往 `http://localhost:8000`

---

## 免責聲明

*   本工具僅供學術交流與技術研究使用。
*   過度修改帳號數值可能導致帳號被官方封鎖，請自行承擔風險。
*   請支持正版遊戲。

---

## 致謝

*   **Core Logic:** [fieryhenry/BCSFE-Python](https://github.com/fieryhenry/BCSFE-Python)
*   **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/)

---

## 授權

本專案遵循 **GNU GPLv3** 開源授權協議。
