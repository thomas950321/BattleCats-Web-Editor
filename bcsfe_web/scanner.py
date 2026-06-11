"""
bcsfe_web/scanner.py
帳號安全性深度診斷模組
基於 account-security-analyzer Skill 的診斷協議實作
"""
from __future__ import annotations
from bcsfe import core
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# ── PONOS statusCode 對照表（與 service.py 共用邏輯）
PONOS_ERROR_MAP = {
    101: "認證失敗：轉移碼或認證碼錯誤",
    111: "帳號驗證失敗：地區或版本不符",
    104: "帳號不存在：轉移碼已失效",
    107: "伺服器維護中",
    400: "請求格式錯誤",
    429: "請求過於頻繁",
}

# ── 安全閾值常數
CATFOOD_CRITICAL = 45_000
CATFOOD_WARNING  = 40_000
RARE_TICKET_LIMIT = 299
NORMAL_TICKET_LIMIT = 999
PLATINUM_SHARD_LIMIT = 99
NP_WARNING = 9_999
HOURS_PER_DAY_CRITICAL = 18
HOURS_PER_DAY_WARNING  = 8


def run_diagnosis(sf: core.SaveFile) -> dict:
    """
    對一個已載入的 SaveFile 執行完整的安全性診斷。
    回傳結構化字典，方便 API 序列化或 CLI 輸出。
    """
    report = {
        "identity": {},
        "resources": [],
        "activity": {},
        "flags": [],
        "verdict": "SAFE",   # SAFE | WARNING | CRITICAL
    }
    issues = []  # List[dict]：{level, category, message}

    # ── 1. Identity & Timestamps ──────────────────────────────────────────
    identity = {
        "inquiry_code": getattr(sf, "inquiry_code", "N/A"),
        "internal_save_date": str(getattr(sf, "date", "N/A")),
        "unix_timestamp": getattr(sf, "timestamp", 0),
        "game_version": sf.game_version.to_string() if hasattr(sf, "game_version") else "N/A",
    }

    # Nyanko Club 加入時間（帳號真實出生日期）
    try:
        club = sf.officer_pass.gold_pass
        if club and club.start_date_total > 0:
            identity["nyanko_club_join_date"] = datetime.fromtimestamp(
                club.start_date_total
            ).strftime("%Y-%m-%d %H:%M:%S")
        else:
            identity["nyanko_club_join_date"] = "N/A（未加入或資料缺失）"
    except (AttributeError, OSError, OverflowError):
        identity["nyanko_club_join_date"] = "N/A"

    # Inquiry Code 類型推斷
    iq = identity["inquiry_code"]
    if iq.startswith(("0", "1", "2", "3")):
        identity["account_type_hint"] = "老帳（查詢碼開頭為舊格式）"
    else:
        identity["account_type_hint"] = "新帳"

    report["identity"] = identity

    # ── 2. 遊玩時間計算 ───────────────────────────────────────────────────
    play_time_seconds = 0
    try:
        from bcsfe.core.game.catbase.playtime import PlayTime
        play_time_seconds = PlayTime(sf.officer_pass.play_time).seconds
    except (AttributeError, ImportError):
        pass
    play_hours = play_time_seconds / 3600

    # ── 3. 累計登入天數 ───────────────────────────────────────────────────
    total_logins = 0
    if hasattr(sf, "logins") and sf.logins.logins:
        try:
            login_1 = sf.logins.get_login(1)
            if login_1:
                total_logins = login_1.count
            else:
                counts = [l.count for l in sf.logins.logins.values()]
                total_logins = max(counts) if counts else 0
        except Exception:
            pass

    # 強度比對（Intensity Ratio）
    hours_per_day = play_hours / total_logins if total_logins > 0 else 0
    estimated_age_years = round(total_logins / 365, 2) if total_logins > 0 else 0

    report["activity"] = {
        "play_time_hours": round(play_hours, 1),
        "total_logins_days": total_logins,
        "estimated_age_years": estimated_age_years,
        "avg_hours_per_day": round(hours_per_day, 1),
    }

    if hours_per_day > HOURS_PER_DAY_CRITICAL:
        issues.append({
            "level": "CRITICAL",
            "category": "遊玩強度比對",
            "message": f"平均每日 {round(hours_per_day, 1)}h — 超越人類極限，疑為加速器或存檔移植。"
        })
    elif hours_per_day > HOURS_PER_DAY_WARNING:
        issues.append({
            "level": "WARNING",
            "category": "遊玩強度比對",
            "message": f"平均每日 {round(hours_per_day, 1)}h — 極高強度，易引起人工審查。"
        })

    # ── 4. 資源安全性檢查 ─────────────────────────────────────────────────
    cf = getattr(sf, "catfood", 0)
    cf_level = "CRITICAL" if cf >= CATFOOD_CRITICAL else ("WARNING" if cf >= CATFOOD_WARNING else "SAFE")
    report["resources"].append({"name": "貓罐頭", "value": cf, "limit": CATFOOD_CRITICAL, "level": cf_level})
    if cf_level != "SAFE":
        issues.append({"level": cf_level, "category": "貓罐頭", "message": f"貓罐頭 {cf}（上限 {CATFOOD_CRITICAL}）"})

    rt = getattr(sf, "rare_tickets", 0)
    rt_level = "WARNING" if rt > RARE_TICKET_LIMIT else "SAFE"
    report["resources"].append({"name": "金券", "value": rt, "limit": RARE_TICKET_LIMIT, "level": rt_level})
    if rt_level != "SAFE":
        issues.append({"level": "WARNING", "category": "金券", "message": f"金券 {rt} 超過建議上限 {RARE_TICKET_LIMIT}"})

    nt = getattr(sf, "normal_tickets", 0)
    nt_level = "WARNING" if nt > NORMAL_TICKET_LIMIT else "SAFE"
    report["resources"].append({"name": "銀券", "value": nt, "limit": NORMAL_TICKET_LIMIT, "level": nt_level})

    ps = getattr(sf, "platinum_shards", 0)
    ps_level = "CRITICAL" if ps > PLATINUM_SHARD_LIMIT else "SAFE"
    report["resources"].append({"name": "白金碎片", "value": ps, "limit": PLATINUM_SHARD_LIMIT, "level": ps_level})
    if ps_level != "SAFE":
        issues.append({"level": "CRITICAL", "category": "白金碎片", "message": f"白金碎片 {ps} 超過上限 {PLATINUM_SHARD_LIMIT}"})

    np_val = getattr(sf, "np", 0)
    np_level = "WARNING" if np_val > NP_WARNING else "SAFE"
    report["resources"].append({"name": "NP", "value": np_val, "limit": NP_WARNING, "level": np_level})

    # ── 5. 封號標記 ───────────────────────────────────────────────────────
    is_banned = getattr(sf, "banned", False)
    show_ban  = getattr(sf, "show_ban_message", False)
    if is_banned:
        issues.append({"level": "CRITICAL", "category": "封號標記", "message": "硬封標記 (banned=True) 已存在！帳號已被封鎖。"})
    if show_ban:
        issues.append({"level": "WARNING", "category": "封號標記", "message": "軟封標記 (show_ban_message=True)，已收到官方警告。"})

    report["flags"] = {
        "banned": is_banned,
        "show_ban_message": show_ban,
    }

    # ── 6. 進度矛盾檢查 ───────────────────────────────────────────────────
    chapters_cleared = sum(
        1 for ch in sf.story.chapters if getattr(ch, "progress", 0) > 0
    ) if hasattr(sf, "story") else 0

    if play_hours < 10 and chapters_cleared >= 9:
        issues.append({
            "level": "CRITICAL",
            "category": "進度矛盾",
            "message": f"遊玩時數僅 {round(play_hours, 1)}h，卻已通關 {chapters_cleared} 個章節，邏輯崩潰。"
        })

    # ── 7. 最終裁決 ───────────────────────────────────────────────────────
    if any(i["level"] == "CRITICAL" for i in issues):
        report["verdict"] = "CRITICAL"
    elif any(i["level"] == "WARNING" for i in issues):
        report["verdict"] = "WARNING"
    else:
        report["verdict"] = "SAFE"

    report["issues"] = issues
    return report
