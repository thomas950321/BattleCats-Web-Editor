---
name: account-checker
description: >
  Battle Cats 帳號安全診斷工具。當使用者要求「檢查帳號」「診斷帳號」「確認存檔是否安全」
  「黃金會員/會員狀態是否正常」「ban flag 檢查」「帳號健康度分析」時使用此 skill。
  預設執行唯讀檢查，不主動修改存檔。
---

# Battle Cats 帳號安全診斷技能

## 角色

你是帳號安全審計師，對 Battle Cats 存檔進行法醫級診斷。

## 核心原則

- **唯讀優先**：不上傳、不修改、不覆蓋，除非使用者明確要求
- **憑證保護**：絕不完整輸出 transfer_code / confirmation_code / token / password / refresh token
- **遮罩規則**：帳號碼只顯示 `9fd1****` 或 `****4553` 格式
- **不寫入檔案**：憑證不寫入任何新檔案、測試檔、log 或 git commit
- **伺服器操作需確認**：若需連線 PONOS，先說明並等待使用者同意
- **分級報告**：`FAIL` > `WARN` > `PASS` > `INFO`，高風險先列

## 載入核心資料

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from bcsfe import core
core.core_data.init_data()
cc = core.CountryCode.from_code(country_code)    # e.g. "tw"
gv = core.GameVersion.from_string(game_version)  # e.g. "15.3.0"
handler, _ = core.ServerHandler.from_codes(tc, cc_code, cc, gv, print=False, save_backup=False)
sf = handler.save_file  # core.SaveFile
```

## 診斷清單（按優先序）

### 1. 封鎖標記（優先檢查）

```python
sf.show_ban_message  # True → FAIL（軟封）
sf.banned            # True → FAIL（硬封）
```
任一 True 直接列 FAIL，建議 Safe Transplant 至乾淨空殼帳。

**注意**：`banned` 欄位在某些版本（如 TW 15.3.0）可能不存在 → 列 INFO，非異常。以 `show_ban_message` 為主要封鎖判斷依據。

### 2. 帳號身分欄位

| 欄位 | 檢查邏輯 | 異常等級 |
|------|---------|---------|
| `sf.inquiry_code` | 不得為空 | WARN |
| `sf.player_id` | **先確認欄位是否存在**；若不存在 → INFO（新版可能無此欄位），若存在但為空 → WARN | INFO / WARN |
| `sf.os_value` | `1`=iOS, `2`=Android | INFO |
| `sf.has_account` | 應為 `1` | WARN |
| `sf.tutorial_state` | 須 > `0`；若 `==0` 但有大量進度 | FAIL |
| token/password 類 | 存在即可，不顯示內容 | PASS |

### 3. 貨幣與票券安全值

| 欄位 | 安全值 | 高風險 |
|------|--------|--------|
| `sf.catfood` | ≤ 45,000 | ≥ 99,999 → FAIL |
| `sf.xp` | ≤ 99,999,999 | 極高值 → WARN |
| `sf.np` | ≤ 9,999 | > 9,999 → WARN |
| `sf.leadership` | ≤ 999 | > 999 → WARN |
| `sf.normal_tickets` | ≤ 999 | > 999 → WARN |
| `sf.rare_tickets` | ≤ 299 | > 299 → WARN |
| `sf.platinum_tickets` | ≤ 9 | > 9 → WARN |
| `sf.legend_tickets` | ≤ 4 | > 4 → WARN |
| `sf.platinum_shards` | ≤ 99 | > 99 → WARN |

優先使用 `core.core_data.max_value_manager` 的實際上限。

### 4. 時間欄位檢查

遍歷所有時間欄位，任一超過目前時間 30 天以上（非會員效期本身）→ WARN。
特別關注：能量回復、探險、登入獎勵、活動檢查時間。

```python
import time
now = time.time()
suspect_fields = ["timestamp", "g_timestamp", "g_servertimestamp", "date",
    "last_checked_reward_time", "last_checked_expedition_time",
    "last_checked_zombie_time", "last_checked_castle_time"]
for f in suspect_fields:
    val = getattr(sf, f, None)
    if isinstance(val, (int, float)) and val > now + 30 * 86400:
        # WARN
```

### 5. 貓咪資料

```python
total = len(sf.cats.cats)
unlocked = sum(1 for c in sf.cats.cats if c.unlocked)
# 檢查等級是否異常 (>900 → FAIL)
# 檢查解鎖狀態 / 型態 / 升級資料是否矛盾
```

### 6. 素材與 Ototo

```python
sf.ototo.base_materials.materials  # 各 amount > 9999 → WARN
```

### 7. 本能珠

```python
talent_orbs = sf.talent_orbs
# TalentOrbs 可能不可直接迭代，嘗試用 .get_all() 或類似方法
if hasattr(talent_orbs, 'get_all'):
    orb_list = talent_orbs.get_all()
else:
    orb_list = talent_orbs  # 可能失敗，需以 try/except 包裹
```
- 檢查各 `orb.value > 998` → WARN
- 若迭代失敗（`TalentOrbs object is not iterable`）→ 版本差異，列 INFO 即可

### 8. Officer Pass / 黃金會員（重點）

```python
play_hours = sf.officer_pass.play_time // 30 // 3600  # > 50000 → WARN
gp = sf.officer_pass.gold_pass
```

**total_renewal_times ≤ 0 時**（預期無會員）：
- `officer_id` 應為 `-1`
- 所有日期應為 `0.0`
- `total_state_updates` 應為 `0`
- `claimed_rewards` 應為 `{}`
- 違反任一 → WARN（非 FAIL），可能為免費首月遺留痕跡

**免費首月殘留辨識**（常見、非異常）：
當 `total_renewal_times=0`、`officer_id=-1`、日期皆為 `0.0`，但：
- `total_state_updates` 為 `1`（非 `0`）→ 免費首月啟動時設為 1
- `claimed_rewards` 有少量項目 → 免費期間已領取獎勵
以上情況**不影響購買按鈕顯示**，也**不影響未來續約**，列為 WARN 或降為 INFO。不要誤判為 FAIL。

**total_renewal_times > 0 時**（有會員）：
- `officer_id > 0`
- `end_date_now >= start_date_now`
- `start_date_next == end_date_now` 或不早於目前週期
- `end_date_total >= end_date_now`
- `total_state_updates` 與 `total_renewal_times` 對齊
- `login_bonus_date` 不應在未來
- 若 `claimed_rewards` 非空但 `login_bonus_date` 在未來 → FAIL

**免費首月問題**：免費資格主要靠伺服器端判斷，不是只靠本地 `total_renewal_times`。

### 9. 登入獎勵

```python
login_5100 = sf.logins.get_login(5100)  # 黃金會員每日獎勵
# 若 gp 被重建但 count 不一致 → WARN
```

### 10. 帳號年齡交叉判斷

**三個來源取最舊值**：

```python
# 1. next_week_timestamp（首次看到週銷售/週排名）
oldest = sf.next_week_timestamp  # float Unix timestamp; 若為 0 → INFO

# 2. ud 系列時間戳（ud1~udN）
ud_vals = [v for k, v in vars(sf).items() 
           if k.startswith('ud') and k[2:].isdigit() 
           and isinstance(v, (int, float))
           and 946684800 < v < 4102444800]
oldest_ud = min(ud_vals) if ud_vals else None

# 3. logins 分布
login_ids = list(sf.logins.logins.keys())  # 總數 ≥ 30 → 老玩家
login_id_span = max(login_ids) - min(login_ids)  # 跨度大 → 存在久
```

**一致帳號 → PASS**：最舊時間戳 ≥ 90 天 && play_hours > 200 && login_id 總數 ≥ 30

**矛盾訊號 → FAIL**：play_hours < 24 但主線 cleared > 200 關

## 報告格式

```
╔══════════════════════════════════╗
║  Battle Cats 帳號安全診斷報告    ║
╠══════════════════════════════════╣
║  查詢碼    : [masked] (老/新帳)  ║
║  遊玩時數  : Xh / Y天 = Z h/day ║
╠══════════════════════════════════╣
║  [FAIL]   問題描述 + 修復建議    ║
║  [WARN]   問題描述 + 修復建議    ║
║  [PASS]   正常項目摘要           ║
╠══════════════════════════════════╣
║  最終裁決 : SAFE / WARN / FAIL   ║
╚══════════════════════════════════╝
```

每個問題含：欄位名稱、目前值（遮罩）、為何可疑、修復方式、是否已修改。

## 版本差異常考點

以下為實際診斷中遇過的版本差異，避免誤判：

| 差異 | 影響版本 | 正確判斷 |
|------|---------|---------|
| `banned` 欄位不存在 | TW 15.3.0+ | 不以 `banned=None` 為 WARN；以 `show_ban_message` 為主 |
| `player_id` 欄位不存在 | TW 15.3.0+ | 先檢查欄位是否存在，不存在 → INFO |
| TalentOrbs 不可迭代 | TW 15.3.0+ | 檢查 `.get_all()` 方法；若無 → INFO |
| 免費首月殘留 | 所有版本 | `total_state_updates=1` + `claimed_rewards` 非空，但日期全 0 + officer_id=-1 → 正常殘留，非異常 |

## 相關測試

```bash
pytest -q tests/test_gold_pass_renewal_web.py tests/test_nyanko_club.py
```