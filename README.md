# 🐈 Battle Cats Web Editor | 貓咪大戰爭網頁存檔修改器

![GitHub Repo stars](https://img.shields.io/github/stars/thomas950321/BattleCats-Web-Editor?style=for-the-badge)
![GitHub license](https://img.shields.io/github/license/thomas950321/BattleCats-Web-Editor?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)

這是基於 [BCSFE-Python](https://github.com/fieryhenry/BCSFE-Python) 核心所開發的**視覺化網頁修改器**。它結合了強大的 Python 後端邏輯與現代化的 Web 前端介面，讓你在瀏覽器中就能輕鬆管理與修改《貓咪大戰爭》的存檔。

---

## ✨ 專案特色 (Features)

*   **🌐 視覺化介面：** 告別繁瑣的指令列，使用直觀的網頁表單進行修改。
*   **⚡ 雲端同步技術：** 整合 GitHub Actions，每天自動抓取原作者的最新代碼，確保支援最新的遊戲版本！
*   **🛡️ 安全機制 (Dirty Check)：** 僅上傳有修改過的數值，降低存檔毀損風險，維護帳號安全性。
*   **📦 全功能支援：**
    *   **基礎資源：** 貓罐頭、經驗值 (XP)、NP、領導力、遊玩時間。
    *   **轉蛋券：** 普通、稀有、白金、傳說轉蛋券及碎片的修改。
    *   **素材與消耗品：** 戰鬥用品、喵力達、貓眼石、貓薄荷、基地素材。
    *   **進階功能：** 本能玉 (Talent Orbs)、迷宮獎牌等。

---

## 🚀 快速開始 (Quick Start)

### 使用方法
1.  在遊戲內進入「設定」 -> 「轉移引繼資料」。
2.  點擊「上傳存檔到伺服器」，取得 **引繼碼 (Transfer Code)** 與 **認證碼 (Confirmation Code)**。
3.  開啟此網頁修改器，輸入代碼並選擇對應的國家版本（EN, TW, JP, KR）。
4.  修改完成後點擊「儲存並上傳至伺服器」，會取得一組**新的代碼**。
5.  回到遊戲中使用「恢復引繼資料」輸入新代碼即可！

---

## 🛠️ 開發與部署 (Deployment)

如果你想在本地執行此專案：

1.  **複製專案：**
    ```bash
    git clone https://github.com/thomas950321/BattleCats-Web-Editor.git
    cd BattleCats-Web-Editor
    ```
2.  **安裝依賴：**
    ```bash
    pip install -r requirements.txt
    ```
3.  **啟動服務：**
    ```bash
    python bcsfe_web/main.py
    ```
4.  **訪問網頁：**
    開啟瀏覽器前往 `http://localhost:8000`

---

## ⚠️ 免責聲明 (Disclaimer)

*   本工具僅供學術交流與技術研究使用。
*   過度修改帳號數值可能導致帳號被官方封鎖 (Ban)，請自行承擔風險。
*   請尊重遊戲開發商 (PONOS)，建議適度娛樂。

---

## ❤️ 致謝 (Credits)

*   **Core Logic:** [fieryhenry/BCSFE-Python](https://github.com/fieryhenry/BCSFE-Python) - 感謝原作者提供強大的存檔處理核心。
*   **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) & Vanilla JavaScript.

---

## 📜 授權 (License)

本專案遵循與原核心相同的 **GNU GPLv3** 開放原始碼授權。
