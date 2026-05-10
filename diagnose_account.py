"""
=============================================================
  Battle Cats 移植帳號全面診斷工具
  Comprehensive Save File Audit Script
=============================================================
用法: python diagnose_account.py
"""
import sys
import os

# --- 路徑設定 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from bcsfe import core

# 初始化 core_data（必須在使用任何 core 功能前呼叫）
core.core_data.init_data()

# =============================================
# ★ 請在此填入移植後的帳號代碼 ★
# =============================================
TRANSFER_CODE    = "9fd158e68"
CONFIRMATION_CODE = "4553"
COUNTRY_CODE     = "tw"   # en / tw / jp / kr
GAME_VERSION     = "13.6.0"
# =============================================

PASS = "✅ PASS"
WARN = "⚠️  WARN"
FAIL = "❌ FAIL"
INFO = "ℹ️  INFO"

results = []

def check(label, status, detail=""):
    icon = {"PASS": PASS, "WARN": WARN, "FAIL": FAIL, "INFO": INFO}.get(status, INFO)
    line = f"  {icon}  {label}"
    if detail:
        line += f" → {detail}"
    results.append((status, line))
    print(line)

def section(title):
    print(f"\n{'─'*60}")
    print(f"  【{title}】")
    print(f"{'─'*60}")

# ─── 步驟 1：下載存檔 ───────────────────────────────────────
print("="*60)
print("  貓咪大戰爭 移植帳號診斷報告")
print("="*60)
print(f"\n[*] 正在登入: {TRANSFER_CODE} / {CONFIRMATION_CODE}")

cc = core.CountryCode.from_code(COUNTRY_CODE)
gv = core.GameVersion.from_string(GAME_VERSION)

server_handler, result = core.ServerHandler.from_codes(
    TRANSFER_CODE,
    CONFIRMATION_CODE,
    cc,
    gv,
    print=False,
    save_backup=False
)

if server_handler is None:
    print(f"\n[❌ 致命錯誤] 無法下載存檔！")
    if result and hasattr(result, 'response') and result.response:
        print(f"   HTTP Status: {result.response.status_code}")
        print(f"   Body: {result.response.text[:300]}")
    else:
        print("   原因：網路逾時或代碼錯誤。")
    sys.exit(1)

sf: core.SaveFile = server_handler.save_file
print(f"[✓] 存檔下載成功！\n")


# ─── 步驟 2：身份欄位 ─────────────────────────────────────
section("1. 帳號身份欄位")

inquiry_code = getattr(sf, 'inquiry_code', None)
check("Inquiry Code 存在", "PASS" if inquiry_code else "FAIL", str(inquiry_code))

# 確認 Token 存在 (Token 為 server_handler 取得的真實 token)
token = getattr(sf, 'token', None) or getattr(sf, 'password', None)
check("Token/Password 存在", "PASS" if token else "WARN", "(已取得)" if token else "無 token 屬性")


# ─── 步驟 3：封號標記 ─────────────────────────────────────
section("2. 封號 / 反作弊標記")

show_ban = getattr(sf, 'show_ban_message', None)
if show_ban is True:
    check("show_ban_message", "FAIL", f"= {show_ban}  ← 帳號目前帶有封號紅字標記！")
elif show_ban is False:
    check("show_ban_message", "PASS", "= False (乾淨)")
else:
    check("show_ban_message", "WARN", f"屬性不存在或為 None: {show_ban}")

banned = getattr(sf, 'banned', None)
if banned is True:
    check("banned", "FAIL", f"= {banned}  ← 帳號帶有硬封旗標！")
elif banned is False:
    check("banned", "PASS", "= False (乾淨)")
else:
    check("banned", "WARN", f"屬性不存在或為 None: {banned}")


# ─── 步驟 4：教學狀態 ─────────────────────────────────────
section("3. 教學 / 初始化狀態")

tutorial_state = getattr(sf, 'tutorial_state', 0)
if tutorial_state > 0:
    check("新手教學狀態", "PASS", f"已完成 (state={tutorial_state})")
else:
    check("新手教學狀態", "WARN", "尚未完成 (網頁版將在登入時自動跳過)")


# ─── 步驟 5：核心物資數值範圍 ─────────────────────────────
section("4. 核心物資數值安全性")

def check_val(label, val, safe_max, hard_max=None):
    hard_max = hard_max or safe_max * 10
    if val is None:
        check(label, "WARN", "無法讀取")
        return
    val = int(val) if hasattr(val, '__int__') else val
    if val > hard_max:
        check(label, "FAIL", f"{val:,} (超過硬上限 {hard_max:,}！高危！)")
    elif val > safe_max:
        check(label, "WARN", f"{val:,} (超過安全上限 {safe_max:,}，請注意)")
    else:
        check(label, "PASS", f"{val:,}")

catfood   = getattr(sf, 'catfood',    None)
xp        = getattr(sf, 'xp',        None)
np        = getattr(sf, 'np',        None)
leadership = getattr(sf, 'leadership', None)

check_val("貓罐頭 (Catfood)",  catfood,   45_000,  99_999)
check_val("XP 經驗值",         xp,        99_999_999, 2_000_000_000)
check_val("NP 本能點數",        np,         9_999,  99_999)
check_val("統率力 (Leadership)", leadership,  999, 9_999)

# 票券
try:
    normal_t   = getattr(sf, 'normal_tickets',   None)
    rare_t     = getattr(sf, 'rare_tickets',     None)
    plat_t     = getattr(sf, 'platinum_tickets', None)
    legend_t   = getattr(sf, 'legend_tickets',   None)
    plat_shards = getattr(sf, 'platinum_shards', None)
    check_val("銀券 Normal Tickets",    normal_t,   999,  9_999)
    check_val("金券 Rare Tickets",      rare_t,     299,  2_999)
    check_val("白金券 Platinum Tickets", plat_t,       9,    999)
    check_val("傳說券 Legend Tickets",  legend_t,     4,     99)
    check_val("白金碎片 Plat Shards",   plat_shards, 99,    999)
except Exception as e:
    check("票券讀取", "WARN", str(e))


# ─── 步驟 6：時間欄位 ─────────────────────────────────────
section("5. 時間欄位合理性")

import datetime

time_fields = [
    'cat_fruit_seed_time',
    'gold_pass_start_time',
    'gold_pass_end_time',
    'last_checked_energy_recovery',
    'last_checked_cat_jobs',
]

now = datetime.datetime.now()
future_threshold = now + datetime.timedelta(days=30)

for tf in time_fields:
    val = getattr(sf, tf, None)
    if val is None:
        continue
    try:
        if isinstance(val, datetime.datetime):
            if val > future_threshold:
                check(f"時間欄位 {tf}", "WARN", f"值在遙遠未來: {val}")
            else:
                check(f"時間欄位 {tf}", "PASS", str(val)[:19])
    except Exception:
        pass


# ─── 步驟 7：貓咪資料 ─────────────────────────────────────
section("6. 貓咪資料完整性")

try:
    cats = getattr(sf, 'cats', None)
    if cats:
        total = len(cats.cats) if hasattr(cats, 'cats') else 0
        check("貓咪總數", "INFO", f"{total} 隻")
        
        # 檢查是否有等級異常的貓
        max_lvl_anomaly = 0
        for cat in (cats.cats if hasattr(cats, 'cats') else []):
            lvl = getattr(cat, 'level', 0)
            if isinstance(lvl, (int, float)) and int(lvl) > 900:
                max_lvl_anomaly += 1
        if max_lvl_anomaly > 0:
            check("異常等級貓咪 (>900)", "WARN", f"發現 {max_lvl_anomaly} 隻等級過高")
        else:
            check("貓咪等級範圍", "PASS", "無異常")
    else:
        check("貓咪資料", "WARN", "cats 屬性為空")
except Exception as e:
    check("貓咪資料讀取", "WARN", str(e))


# ─── 步驟 8：Ototo 基地材料 ──────────────────────────────
section("7. Ototo 基地材料")

try:
    ototo = getattr(sf, 'ototo', None)
    if ototo:
        base_mats = getattr(ototo, 'base_materials', None)
        if base_mats:
            mats = getattr(base_mats, 'materials', [])
            all_ok = all(getattr(m, 'amount', 0) <= 9999 for m in mats)
            check("基地素材數值", "PASS" if all_ok else "WARN",
                  f"共 {len(mats)} 種" + ("" if all_ok else " (部分超過 9999)"))
        else:
            check("基地素材", "INFO", "屬性不存在 (可能版本不同)")
    else:
        check("Ototo 基地", "INFO", "屬性不存在")
except Exception as e:
    check("Ototo 讀取", "WARN", str(e))


# ─── 步驟 9：本能玉 ──────────────────────────────────────
section("8. 本能玉 (Talent Orbs)")

try:
    orb_save = getattr(sf, 'talent_orb_data', None)
    if orb_save:
        orbs = getattr(orb_save, 'orbs', {})
        over_limit = {k: v for k, v in orbs.items() if v > 998}
        if over_limit:
            check("本能玉數量上限", "WARN", f"{len(over_limit)} 種超過 998")
        else:
            check("本能玉數量上限", "PASS", f"共 {len(orbs)} 種，全部合規")
    else:
        check("本能玉資料", "INFO", "屬性不存在")
except Exception as e:
    check("本能玉讀取", "WARN", str(e))


# ─── 步驟 10：Officer Pass (遊戲時數) ────────────────────
section("9. 遊戲時數")

try:
    officer_pass = getattr(sf, 'officer_pass', None)
    if officer_pass:
        play_time_raw = getattr(officer_pass, 'play_time', 0)
        play_hours = int(play_time_raw) // 30 // 3600
        check("遊戲時數", "INFO", f"{play_hours} 小時")
        if play_hours > 50_000:
            check("遊戲時數範圍", "WARN", "時數極高，請確認是否合理")
        else:
            check("遊戲時數範圍", "PASS", "正常")
    else:
        check("Officer Pass", "INFO", "屬性不存在")
except Exception as e:
    check("遊戲時數讀取", "WARN", str(e))


# ─── 最終摘要 ─────────────────────────────────────────────
section("📋 診斷摘要")

count = {"PASS": 0, "WARN": 0, "FAIL": 0, "INFO": 0}
for status, _ in results:
    count[status] = count.get(status, 0) + 1

print(f"  ✅ PASS: {count['PASS']}  ⚠️  WARN: {count['WARN']}  ❌ FAIL: {count['FAIL']}  ℹ️  INFO: {count['INFO']}")

if count['FAIL'] > 0:
    print("\n  [!] 發現嚴重問題，請在上傳前修復 FAIL 項目！")
elif count['WARN'] > 0:
    print("\n  [~] 有警告項目，建議確認後再上傳。")
else:
    print("\n  [★] 帳號狀態良好，無嚴重問題！")

print("\n" + "="*60 + "\n")
