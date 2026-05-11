import sys
import os

# 確保加載路徑
current_dir = os.getcwd()
src_path = os.path.join(current_dir, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from bcsfe import core
from bcsfe_web.service import service

async def run_scan():
    # 初始化
    core.core_data.init_data()
    
    transfer_code = "805001ef9"
    conf_code = "4270"
    cc = "tw"
    
    print(f"--- 開始掃描帳號: {transfer_code} (地區: {cc}) ---")
    
    success, msg = await service.login_and_fetch(transfer_code, conf_code, cc, "13.6.0")
    if not success:
        print(f"登入失敗: {msg}")
        return

    sf = service.current_save
    
    # 診斷報告開始
    print("\n=== [Account Identity & Timestamps] ===")
    print(f"* Inquiry Code: {sf.inquiry_code}")
    print(f"* Internal Save Date: {sf.date}")
    print(f"* Unix Timestamp: {sf.timestamp}")
    print(f"* Game Version: {sf.game_version.to_string()}")
    
    try:
        from bcsfe.core.game.catbase.playtime import PlayTime
        play_time_seconds = PlayTime(sf.officer_pass.play_time).seconds
    except (AttributeError, ImportError):
        play_time_seconds = 0
        
    print(f"* Total Play Time: {play_time_seconds // 3600} Hours ({play_time_seconds} seconds)")
    
    print("\n=== [Security Risk Assessment] ===")
    
    # 1. 貓罐頭
    cf = sf.catfood
    cf_status = "SAFE" if cf < 40000 else ("WARNING" if cf < 45000 else "CRITICAL (Auto-ban Limit)")
    print(f"* Catfood: {cf} ({cf_status})")
    
    # 2. 扭蛋券
    nt = sf.normal_tickets
    rt = sf.rare_tickets
    pt = sf.platinum_tickets
    lt = sf.legend_tickets
    print(f"* Normal Tickets: {nt} (Limit 999)")
    print(f"* Rare Tickets: {rt} (Limit 299)")
    print(f"* Platinum Tickets: {pt} / Legend Tickets: {lt}")
    
    # 3. 資源
    print(f"* NP: {sf.np}")
    print(f"* Platinum Shards: {sf.platinum_shards} (Limit 99)")
    
    # 4. 封號標記
    is_banned = getattr(sf, "banned", False)
    ban_msg = "!!! BANNED FLAG DETECTED !!!" if is_banned else "NO ABNORMAL FLAGS"
    print(f"* Ban Status: {ban_msg}")
    
    # 5. 進度邏輯
    chapters_cleared = 0
    for chapter in sf.story.chapters:
        if chapter.progress > 0:
            chapters_cleared += 1
    
    print(f"* Chapters with progress: {chapters_cleared}")
    
    # 6. 帳號身世掃描 (新增)
    print("\n=== [Account Heritage & Activity] ===")
    
    # 累計登入天數 (嘗試抓取 ID 1 或 總覽)
    total_logins = 0
    if hasattr(sf, "logins") and sf.logins.logins:
        # 在許多版本中，ID 1 代表累計登入
        login_1 = sf.logins.get_login(1)
        if login_1:
            total_logins = login_1.count
        else:
            # 如果找不到 ID 1，找最大的 count
            counts = [l.count for l in sf.logins.logins.values()]
            total_logins = max(counts) if counts else 0
            
    print(f"* Total Cumulative Logins: {total_logins} Days")
    
    # 估算帳號年齡
    if total_logins > 0:
        estimated_age_years = round(total_logins / 365, 2)
        print(f"* Estimated Account Age: ~{estimated_age_years} Years")
        
        # 檢查時數與天數比例 (每天遊玩超過 24 小時顯然異常)
        hours_per_day = (play_time_seconds / 3600) / total_logins if total_logins > 0 else 0
        if hours_per_day > 18:
            print(f"  !!! [CRITICAL]: Average {round(hours_per_day, 1)}h play/day. Humanly impossible!")
        elif hours_per_day > 8:
            print(f"  !!! [WARNING]: Average {round(hours_per_day, 1)}h play/day. Very high activity.")
    
    # 俱樂部紀錄
    club = sf.officer_pass.gold_pass
    if club and club.start_date_total > 0:
        from datetime import datetime
        join_date = datetime.fromtimestamp(club.start_date_total)
        print(f"* Nyanko Club First Joined: {join_date}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_scan())
