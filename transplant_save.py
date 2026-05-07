"""
transplant_save.py
==================
將「來源存檔（強帳）」的進度數據移植到「目標存檔（新帳）」中，
同時保留目標存檔的身份識別資訊（Inquiry Code、Token、Device ID）。

使用方式
--------
python transplant_save.py <來源存檔路徑> <目標存檔路徑> [--output <輸出路徑>]

範例
----
python transplant_save.py SAVE_DATA_SOURCE SAVE_DATA_TARGET
python transplant_save.py SAVE_DATA_SOURCE SAVE_DATA_TARGET --output SAVE_DATA_EDITED
"""

from __future__ import annotations

import argparse
import sys
import copy
from pathlib import Path as PyPath

# ── 初始化 bcsfe core（必須在 import SaveFile 之前） ──────────────────────
import bcsfe.core as core

core.core_data.init_data()  # 初始化設定、Logger、LocalManager 等

from bcsfe.core.io.save import SaveFile  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# 常數：所有「身份識別」欄位，這些欄位必須從「目標存檔」保留
# ─────────────────────────────────────────────────────────────────────────────
IDENTITY_FIELDS: list[str] = [
    # 帳號轉移相關（目標帳號的 Inquiry Code / Transfer Code / Confirmation Code）
    "inquiry_code",        # 詢問碼（最重要，伺服器識別帳號）
    "transfer_code",       # 轉移碼
    "confirmation_code",   # 確認碼
    "transfer_flag",       # 轉移旗標
    "password_refresh_token",  # 密碼刷新 Token（Google / Apple 帳號登入）

    # 平台帳號 ID（Android: Google Play / iOS: Game Center）
    "player_id",           # 平台玩家 ID

    # 帳號狀態
    "has_account",         # 是否已綁定帳號
    "backup_state",        # 備份狀態

    # 訂單 ID（購買紀錄，不可混淆）
    "order_ids",

    # 平台時間戳（各平台同步時間，保留目標的）
    "g_timestamp",
    "g_servertimestamp",
    "m_gettimesave",
    "g_timestamp_2",
    "g_servertimestamp_2",
    "m_gettimesave_2",
    "m_dGetTimeSave2",
    "m_dGetTimeSave3",
    "unknown_timestamp",
    "usl1",  # Google Play 相關字串列表

    # 遊戲內購（In-App Purchase）相關
    "full_gameversion",
    "energy_notification",
]


# ─────────────────────────────────────────────────────────────────────────────
# 「進度」欄位（從來源存檔移植的資料）
# ─────────────────────────────────────────────────────────────────────────────
PROGRESS_FIELDS: list[str] = [
    # ── 貓咪 ──────────────────────────────────────────────────────────────
    "cats",             # 所有貓咪的解鎖、升級、形態、天賦、收藏等

    # ── 關卡進度 ──────────────────────────────────────────────────────────
    "story",            # 世界篇、未來篇、宇宙篇 + 寶物
    "event_stages",     # 活動關卡（包含傳說關卡限制組合）
    "item_reward_stages",   # 道具獎勵關卡
    "timed_score_stages",   # 限時評分關卡
    "ex_stages",            # EX 關卡
    "uncanny",              # 超難關卡（レジェンドステージ）
    "catamin_stages",       # 貓薄荷關卡
    "legend_quest",         # 傳說任務
    "aku",                  # 暗黑之章（Aku 章節）
    "zero_legends",         # Zero Legends
    "dojo",                 # 道場
    "dojo_chapters",        # 道場章節（新版本）
    "tower",                # 貓之塔
    "challenge",            # 挑戰關卡
    "gauntlets",            # 突擊模式
    "collab_gauntlets",     # 合作突擊
    "enigma_clears",        # 謎題通關
    "enigma",               # 謎題
    "behemoth_culling",     # Behemoth 討伐

    # ── 寶物 ─────────────────────────────────────────────────────────────
    # 寶物已包含在 story 中（StoryChapters 包含 treasure 數據）

    # ── 貨幣 & 道具 ──────────────────────────────────────────────────────
    "catfood",              # 貓罐頭
    "xp",                   # 經驗值
    "normal_tickets",       # 普通轉蛋券
    "rare_tickets",         # 稀有轉蛋券
    "platinum_tickets",     # 白金轉蛋券
    "legend_tickets",       # 傳說轉蛋券
    "np",                   # NP（天賦點數）
    "platinum_shards",      # 白金碎片
    "leadership",           # 統率力（Leadership）
    "hundred_million_ticket",  # 一億輸入券
    "catfruit",             # 貓果實
    "catseyes",             # 貓眼石
    "catamins",             # 貓維他命
    "lucky_tickets",        # 幸運票
    "battle_items",         # 戰鬥道具（速攻砲、工人貓升級等）
    "talent_orbs",          # 天賦寶珠
    "scheme_items",         # 計畫道具
    "treasure_chests",      # 寶箱

    # ── 特殊技能（研究員、助攻貓等） ─────────────────────────────────────
    "special_skills",

    # ── 排名 & 獎勵 ───────────────────────────────────────────────────────
    "user_rank_rewards",    # 使用者等級獎勵
    "combo_unlocks",        # 組合解鎖
    "combo_unlocked_10k_ur",

    # ── 探險 & 工廠 ───────────────────────────────────────────────────────
    "gamatoto",             # 加馬圖圖（探險）
    "ototo",                # 工廠（Ototo）

    # ── 每日 & 登入 ───────────────────────────────────────────────────────
    "logins",               # 登入獎勵

    # ── 任務 ─────────────────────────────────────────────────────────────
    "missions",             # 任務系統

    # ── 神社 ─────────────────────────────────────────────────────────────
    "cat_shrine",           # 貓神社

    # ── 活動 & 轉蛋 ──────────────────────────────────────────────────────
    "gatya",                # 轉蛋種子
    "event_capsules",       # 活動扭蛋膠囊
    "event_capsules_counter",
    "event_capsules_2",

    # ── 勳章 ─────────────────────────────────────────────────────────────
    "medals",               # 勳章

    # ── 其他進度 ─────────────────────────────────────────────────────────
    "outbreaks",            # 殭屍爆發
    "map_resets",           # 地圖重置
    "cleared_slots",        # 已清除的戰鬥槽位
    "cleared_eoc_1",        # 世界篇第一章完成旗標
    "itf1_complete",        # 未來篇第一章完成旗標
    "itf1_ending",          # 未來篇結局旗標
    "cotc_1_complete",      # 宇宙篇第一章完成旗標
    "unlocked_ending",      # 解鎖結局
    "enemy_guide",          # 敵人圖鑑
    "unit_drops",           # 單位掉落記錄

    # ── 雜項 ─────────────────────────────────────────────────────────────
    "stamp_data",           # 印章數據
    "officer_pass",         # 高階通行證
    "wildcat_slots",        # 狂貓槽（老虎機活動）
    "cat_scratcher",        # 貓咪老虎機
    "beacon_base",          # 信標基地
    "item_pack",            # 道具包
    "labyrinth_medals",     # 迷宮勳章
    "dojo_3x_speed",        # 道場 3 倍速
]


def load_save(path: str) -> SaveFile:
    """讀取並解析存檔，自動偵測地區碼（CC）。"""
    file_path = core.Path(path)
    if not file_path.exists():
        print(f"[ERROR] 找不到存檔：{path}", file=sys.stderr)
        sys.exit(1)

    raw_data = core.Data.from_file(file_path)
    print(f"[INFO] 正在載入存檔：{path}  ({len(raw_data)} bytes)")

    save = SaveFile(dt=raw_data)
    print(
        f"[INFO]   地區碼: {save.cc.get_code()}"
        f"  |  版本: {save.game_version.game_version}"
    )
    return save


def check_compatibility(source: SaveFile, target: SaveFile) -> bool:
    """
    版本相容性檢查。

    規則：
    - 地區碼（CC）必須相同（JP/EN/KR/TW...）。
    - 來源版本 >= 目標版本：通常可移植（新數據格式向下相容）。
    - 來源版本 < 目標版本：存在風險，但允許（會發出警告）。
    """
    src_cc = source.cc.get_code()
    tgt_cc = target.cc.get_code()
    src_gv = source.game_version.game_version
    tgt_gv = target.game_version.game_version

    compatible = True

    if src_cc != tgt_cc:
        print(
            f"[WARNING] 地區碼不相同！來源={src_cc}，目標={tgt_cc}。\n"
            "          不同地區的存檔移植可能導致遊戲崩潰或資料毀損。",
            file=sys.stderr,
        )
        compatible = False

    if src_gv > tgt_gv:
        print(
            f"[INFO] 版本差異：來源({src_gv}) > 目標({tgt_gv})。\n"
            "       舊版遊戲讀取較新格式的存檔可能有問題，建議先更新目標設備的遊戲版本。"
        )
    elif src_gv < tgt_gv:
        print(
            f"[WARNING] 版本差異：來源({src_gv}) < 目標({tgt_gv})。\n"
            "          較新版本的遊戲讀取舊格式存檔通常沒問題，但請注意新功能欄位可能遺失。"
        )
    else:
        print(f"[INFO] 版本一致：{src_gv} ✓")

    return compatible


def backup_identity(target: SaveFile) -> dict:
    """從目標存檔擷取並返回所有身份識別欄位的快照。"""
    snapshot = {}
    for field in IDENTITY_FIELDS:
        if hasattr(target, field):
            val = getattr(target, field)
            # 深複製以防止被後續操作修改
            snapshot[field] = copy.deepcopy(val)
    return snapshot


def restore_identity(target: SaveFile, snapshot: dict) -> None:
    """將備份的身份識別欄位還原回目標存檔。"""
    for field, value in snapshot.items():
        if hasattr(target, field):
            setattr(target, field, value)


def transplant_progress(source: SaveFile, target: SaveFile) -> None:
    """
    將來源存檔的「進度欄位」深複製到目標存檔中。
    僅複製目標存檔版本所具有的欄位（hasattr 防呆）。
    """
    transplanted = []
    skipped = []

    for field in PROGRESS_FIELDS:
        if hasattr(source, field) and hasattr(target, field):
            val = copy.deepcopy(getattr(source, field))
            setattr(target, field, val)
            transplanted.append(field)
        else:
            skipped.append(field)

    print(f"\n[INFO] 已移植 {len(transplanted)} 個進度欄位：")
    # 分組打印（每行 5 個）
    for i in range(0, len(transplanted), 5):
        print("       " + ", ".join(transplanted[i : i + 5]))

    if skipped:
        print(
            f"\n[INFO] 已跳過 {len(skipped)} 個欄位（版本差異或不適用）：\n"
            "       " + ", ".join(skipped)
        )


def save_output(target: SaveFile, output_path: str) -> None:
    """
    將修改後的目標存檔序列化並寫入檔案。
    to_data() 會自動重新計算 Checksum（MD5 Hash）。
    """
    out_path = core.Path(output_path)
    out_path.parent().generate_dirs()

    print(f"\n[INFO] 正在序列化並計算 Checksum...")
    data = target.to_data()  # 內部已呼叫 set_hash()

    print(f"[INFO] 正在寫入：{output_path}  ({len(data)} bytes)")
    data.to_file(out_path)
    print(f"[SUCCESS] 輸出完成：{output_path}")


def print_summary(source: SaveFile, target: SaveFile, identity_snapshot: dict) -> None:
    """打印移植摘要。"""
    print("\n" + "=" * 60)
    print("  移植摘要")
    print("=" * 60)
    print(f"  來源存檔 CC={source.cc.get_code()}, GV={source.game_version.game_version}")
    print(f"  目標存檔 CC={target.cc.get_code()}, GV={target.game_version.game_version}")
    print()
    print("  [ 保留的身份識別資訊（來自目標存檔）]")
    print(f"    inquiry_code       : {identity_snapshot.get('inquiry_code', '(N/A)')}")
    print(f"    transfer_code      : {identity_snapshot.get('transfer_code', '(N/A)')}")
    print(f"    confirmation_code  : {identity_snapshot.get('confirmation_code', '(N/A)')}")
    print(f"    password_refresh_token: {'(已保留)' if identity_snapshot.get('password_refresh_token') else '(空)'}")
    print(f"    player_id          : {identity_snapshot.get('player_id', '(N/A)')}")
    print()
    print("  [ 移植的進度資源（來自來源存檔）]")
    print(f"    貓罐頭 (catfood)   : {getattr(source, 'catfood', 'N/A')}")
    print(f"    XP                 : {getattr(source, 'xp', 'N/A')}")
    print(f"    普通票 (normal_tickets) : {getattr(source, 'normal_tickets', 'N/A')}")
    print(f"    稀有票 (rare_tickets)   : {getattr(source, 'rare_tickets', 'N/A')}")
    print(f"    白金票 (platinum_tickets): {getattr(source, 'platinum_tickets', 'N/A')}")
    print(f"    NP                 : {getattr(source, 'np', 'N/A')}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="將強帳存檔進度移植到新帳存檔（保留新帳身份識別）。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "source",
        help="來源存檔路徑（強帳，提供進度）",
    )
    parser.add_argument(
        "target",
        help="目標存檔路徑（新帳，提供 Inquiry Code / Token）",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="SAVE_DATA_EDITED",
        help="輸出存檔路徑（預設：SAVE_DATA_EDITED）",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="忽略地區碼不相容警告，強制移植",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Battle Cats 存檔進度移植工具")
    print("=" * 60)

    # 1. 載入存檔
    print("\n[STEP 1] 載入存檔...")
    source = load_save(args.source)
    target = load_save(args.target)

    # 2. 版本相容性檢查
    print("\n[STEP 2] 版本相容性檢查...")
    compatible = check_compatibility(source, target)
    if not compatible and not args.force:
        print(
            "\n[ABORT] 地區碼不相容，已終止。\n"
            "        若仍要強制移植，請加上 --force 參數。",
            file=sys.stderr,
        )
        sys.exit(1)

    # 3. 備份目標存檔的身份識別資訊
    print("\n[STEP 3] 備份目標存檔的身份識別資訊...")
    identity_snapshot = backup_identity(target)
    print(
        f"         inquiry_code = {identity_snapshot.get('inquiry_code', '(空)')!r}"
    )

    # 4. 移植進度數據
    print("\n[STEP 4] 移植進度數據...")
    transplant_progress(source, target)

    # 5. 還原身份識別資訊
    print("\n[STEP 5] 還原目標存檔的身份識別資訊...")
    restore_identity(target, identity_snapshot)
    print(
        f"         inquiry_code = {getattr(target, 'inquiry_code', '(空)')!r}  ✓"
    )

    # 6. 打印摘要
    print_summary(source, target, identity_snapshot)

    # 7. 序列化並輸出
    print("\n[STEP 6] 輸出修改後的存檔...")
    save_output(target, args.output)

    print(
        "\n完成！請將輸出檔案 (SAVE_DATA_EDITED) 複製到遊戲的存檔目錄，\n"
        "然後使用目標帳號登入（使用原本的 Inquiry Code + Confirmation Code）。"
    )


if __name__ == "__main__":
    main()
