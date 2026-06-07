# AGENTS.md

本專案是 Battle Cats 存檔編輯與帳號檢查工具。當使用者要求「檢查帳號」、「診斷帳號」、「確認存檔是否安全」、「黃金會員/會員狀態是否正常」時，請依照本文件執行。

## 基本原則

- 預設只做唯讀檢查，不上傳、不修改、不覆蓋存檔，除非使用者明確要求。
- 不要在回覆中完整輸出 `transfer_code`、`confirmation_code`、token、password、refresh token 或其他帳號憑證。
- 若需要引用帳號碼，只顯示遮罩版本，例如 `9fd1****` 或 `****4553`。
- 不要把帳號憑證寫進新檔案、測試檔、log 或 git commit。
- 若需要執行會連線到 PONOS 伺服器的程式，先說明它會下載帳號存檔並等待使用者確認。
- 檢查結果要分成 `FAIL`、`WARN`、`PASS`、`INFO`，先列高風險問題。

## 主要參考腳本

- `diagnose_account.py` 是目前帳號檢查流程的參考來源。
- 該檔案可能含有亂碼與硬編碼帳號資訊；使用前先檢查語法是否可執行。
- 若腳本無法執行，請不要直接大改腳本；先用它的檢查邏輯作為清單，透過小型臨時讀取流程或既有 `bcsfe.core` API 進行唯讀檢查。
- 載入核心資料時通常需要：
  - 將專案 `src` 加入 `sys.path`
  - `from bcsfe import core`
  - `core.core_data.init_data()`
  - 使用 `core.CountryCode.from_code(...)`
  - 使用 `core.GameVersion.from_string(...)`
  - 使用 `core.ServerHandler.from_codes(..., save_backup=False)`

## 帳號檢查清單

### 1. 連線與下載

- 確認國家碼與版本號合理，例如 `tw`、`en`、`jp`、`kr` 與目前使用的遊戲版本。
- 檢查 `ServerHandler.from_codes` 是否成功。
- 若失敗，回報 HTTP status、錯誤摘要與可能原因，但不要輸出完整憑證。
- 確認 `server_handler.save_file` 有載入成 `core.SaveFile`。

### 2. 帳號身分欄位

- 檢查 `inquiry_code` 是否存在。
- 檢查 token/password/refresh token 類欄位是否存在，但不要顯示完整內容。
- 檢查帳號識別欄位是否異常為空，例如 `player_id`、`os_value`、`backup_counter`、`backup_frame`，若該版本存在這些欄位。
- 記錄 `os_value`（`1`=iOS、`2`=Android）與 `has_account` 是否正常（應為 `1`）。
- `tutorial_state` 應大於 `0`（已完成教學）；若為 `0` 且存在大量進度，列為 `FAIL`。

### 3. 封鎖與風險旗標

- 檢查 `show_ban_message`。
- 檢查 `banned`。
- 若任一為 `True`，列為 `FAIL`。
- 若欄位不存在或為 `None`，列為 `WARN`，並說明可能是版本差異。

### 4. 教學與基本進度

- 檢查 `tutorial_state` 是否大於 `0`。
- 檢查世界篇、未來篇、宇宙篇、魔界篇等章節物件是否存在。
- 若使用者要求詳細進度，檢查章節 clear 狀態、寶物等級、解鎖旗標是否互相一致。

### 5. 貨幣與票券

檢查下列欄位是否超出安全值或硬上限：

- `catfood`：安全值約 `45,000`，高於 `99,999` 視為高風險。
- `xp`：安全值約 `99,999,999`，極高值視為高風險。
- `np`：安全值約 `9,999`。
- `leadership`：安全值約 `999`。
- `normal_tickets`：安全值約 `999`。
- `rare_tickets`：安全值約 `299`。
- `platinum_tickets`：安全值約 `9`。
- `legend_tickets`：安全值約 `4`。
- `platinum_shards`：安全值約 `99`。

若專案內 `core.core_data.max_value_manager` 提供實際上限，優先使用該資料。

### 6. 時間欄位

- 檢查所有常見時間欄位是否異常落在未來。
- 任何超過目前時間 30 天以上、且不是會員有效期本身的時間欄位，列為 `WARN`。
- 對能量回復、探險、登入獎勵、活動檢查時間等欄位尤其要小心。
- 不要擅自把時間欄位改回現在，除非使用者要求修復。

### 7. 貓咪資料

- 檢查 `sf.cats.cats` 是否存在。
- 統計總貓數與已解鎖數。
- 檢查是否有等級、加值、型態超出該貓合理範圍。
- 檢查解鎖狀態、型態、升級資料是否互相矛盾。
- 若發現大量等級超高，例如大於 `900`，列為 `WARN` 或 `FAIL`。

### 8. Ototo 與素材

- 檢查 `sf.ototo`。
- 檢查 `ototo.base_materials.materials` 數量與各素材 `amount`。
- 一般素材高於 `9,999` 列為 `WARN`。
- 若素材列表長度與目前版本不符，列為 `WARN`。

### 9. 本能珠

- 檢查本能珠資料欄位，可能是 `talent_orbs` 或 `talent_orb_data`，依目前程式碼實際結構判斷。
- 檢查每種本能珠數量是否高於 `998`。
- 若資料結構不存在，先判斷是否為版本差異，不要直接視為錯誤。

### 10. Officer Pass 與黃金會員

- 檢查 `sf.officer_pass` 是否存在。
- 將 `officer_pass.play_time` 從 frame 換算成小時：`play_time // 30 // 3600`。
- 若遊玩時間過高，例如大於 `50,000` 小時，列為 `WARN`。
- 檢查 `sf.officer_pass.gold_pass`，重點欄位：
  - `officer_id`
  - `total_renewal_times`
  - `start_date_now`
  - `end_date_now`
  - `start_date_next`
  - `end_date_next`
  - `start_date_total`
  - `end_date_total`
  - `time_error_end`
  - `total_state_updates`
  - `login_bonus_date`
  - `claimed_rewards`
  - `remaing_days_popup`
  - `first_popup_flag`
  - `badge_flag`
- 若 `total_renewal_times <= 0`，預期會員應被視為不存在：
  - `officer_id` 應為 `-1` 或空/無效狀態。
  - 所有會員日期應為 `0.0`。
  - `total_state_updates` 應為 `0`。
  - `claimed_rewards` 應為 `{}`。
- 若 `total_renewal_times > 0`，預期：
  - `officer_id` 應大於 `0`。
  - 會員日期應形成合理區間。
  - `end_date_now >= start_date_now`。
  - `start_date_next == end_date_now` 或至少不早於目前週期。
  - `end_date_total >= end_date_now`。
  - `total_state_updates` 應與 `total_renewal_times` 對齊，避免遊戲補發異常獎勵。
  - `login_bonus_date` 不應異常落在未來。
- 若 `total_renewal_times == 0` 但日期仍有效，列為 `FAIL`，這會造成遊戲可能不顯示購買按鈕。
- 若使用者問「免費首月是否恢復」，要說明免費資格通常不是只靠本地 `total_renewal_times` 判定，可能由伺服器或帳號歷史決定。

### 11. 登入獎勵

- 檢查 `sf.logins.get_login(5100)`，這通常與黃金會員每日獎勵相關。
- 若黃金會員狀態被重建或移除，`login.count` 應與目標狀態一致。
- 若 `login_bonus_date` 在未來且 `claimed_rewards` 非空，列為高風險，可能造成每日會員獎勵無法領取。

### 12. 帳號年齡與活躍歷史

> PONOS 官方存檔**不在本地儲存帳號創建日期**（那是伺服器端資料）。以下欄位可作為帳號年齡的間接指標，從最舊的一個推估「帳號至少在某時間點之前就已存在並活躍」。

#### 12-1. `next_week_timestamp`

- 玩家**首次看到週銷售/週排名**時由遊戲寫入，是本地存檔中最能反映帳號早期活躍時間的欄位。
- 讀取方式：`sf.next_week_timestamp`（為 float Unix timestamp）。
- 若欄位不為 `0` 且距今超過 30 天，視為有效的帳號年齡下界。
- 若 `next_week_timestamp` 晚於最早 `ud` 時間戳，應以更舊的值為準。

#### 12-2. `ud` 系列時間戳（`ud1`～`ud14` 等）

- 遊戲用途未完全公開，但每個欄位代表特定功能（新聞/探險/商店等）的最後活動時間。
- 讀取方式：遍歷 `vars(sf)` 中 `k.startswith('ud') and k[2:].isdigit()` 的欄位，取得所有值後找最舊的一個。
- 有效範圍：Unix timestamp 介於 `946684800`（2000-01-01）至 `4102444800`（2100-01-01）。
- 最舊的 `ud` 時間戳可作為「帳號至少在這個時間點之前就存在」的另一個指標。
- 若所有 `ud` 值都在 30 天以內，但其他進度顯示長期遊玩，列為 `INFO`（可能是帳號遷移或重置）。

#### 12-3. `sf.logins.logins` 登入記錄

- `sf.logins.logins` 是一個 `{login_id: Login}` 字典，記錄各活動/週回/每日獎勵的領取次數。
- 檢查項目：
  - `login_id` 總數：越多代表參與過越多不同活動期，長期玩家通常超過 50 個。
  - 各 `login_id` 的 `count` 加總：作為「累計登入互動次數」的參考。
  - `login_id` 號碼範圍：號碼跨度越大（例如從 `1876` 到 `52476`），代表帳號存在的時間跨度越長。
- 若登入記錄極少（例如總 `login_id` < 5 且 count 合計 < 20），但進度顯示大量關卡完成，列為 `WARN`（不符合長期正常遊玩的登入分布）。

#### 12-4. 帳號年齡交叉判斷邏輯

以下條件若同時成立，視為帳號年齡與進度**互相一致**（`PASS`）：

1. `next_week_timestamp` 或最舊 `ud` 時間戳距今 ≥ 90 天。
2. `officer_pass.play_time // 30 // 3600`（遊玩小時）> 200h，且與主線/活動進度比例合理。
3. `sf.logins.logins` 的 `login_id` 總數 ≥ 30。

若帳號遊玩時間 < 24h 但主線 cleared > 200 關或活動 cleared > 300 關，列為 `FAIL`（開帳即通關訊號）。

若 `next_week_timestamp` 為 `0` 或不存在，說明帳號從未觸發過週銷售，僅列為 `INFO`，不單獨視為異常。

## 報告格式

回覆使用者時使用繁體中文，建議格式：

1. 先列 `FAIL`。
2. 再列 `WARN`。
3. 簡短列出 `PASS` 摘要。
4. 最後給「建議修復順序」。

每個問題都要包含：

- 欄位名稱。
- 目前值，敏感資訊需遮罩。
- 為什麼可疑。
- 建議修復方式。
- 是否已修改；若未經使用者同意，預設只報告不修改。

## 驗證建議

- 修改檢查工具後，優先跑針對性測試。
- 若執行全量 `pytest`，注意 `scratch/test_supabase.py` 可能需要 `SUPABASE_URL` 與 `SUPABASE_KEY`，這類環境問題不要誤判為帳號檢查失敗。
- 對黃金會員邏輯至少跑：
  - `pytest -q .\tests\test_gold_pass_renewal_web.py .\tests\test_nyanko_club.py`

