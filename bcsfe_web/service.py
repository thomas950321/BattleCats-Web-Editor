import sys
import os
import uuid
import time
import threading

# 確保能加載 src 中的 bcsfe 模組 (相對於目前檔案路徑)
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "..", "src")
if src_path not in sys.path:
    sys.path.append(src_path)

try:
    from bcsfe import core
except ImportError as e:
    print(f"Error: Could not import bcsfe. If the path is correct ({src_path}), check for missing dependencies.")
    print(f"Traceback: {e}")

class BCSFE_Service:
    def __init__(self):
        self.current_save: core.SaveFile | None = None
        self.server_handler: core.ServerHandler | None = None
        self.tutorial_auto_skipped = False

    async def login_and_fetch(self, transfer_code: str, confirmation_code: str, country_code: str, game_version: str):
        self.tutorial_auto_skipped = False
        if transfer_code == "TEST" and confirmation_code == "0000":
            # 優先搜尋專案內的測試數據 (適用於雲端部署)
            test_save_path = core.Path(os.path.join(current_dir, "test_data", "SAVE_DATA"))
            # 退而求其次搜尋本地存檔路徑 (相容本地運行)
            local_save_path = core.Path.get_data_folder().add("saves").add("SAVE_DATA")
            
            target_path = test_save_path if test_save_path.exists() else local_save_path
            
            if target_path.exists():
                try:
                    data = target_path.read()
                    # 模擬模式下，如果解析失敗，提供更詳細的錯誤資訊
                    self.current_save = core.SaveFile(dt=data)
                    self.server_handler = None  # 模擬模式不連接伺服器
                    return True, "模擬測試存檔已載入"
                except Exception as e:
                    import traceback
                    error_detail = traceback.format_exc()
                    print(f"Simulation Load Error: {error_detail}", flush=True)
                    return False, f"載入測試存檔失敗 (核心錯誤): {str(e)}"
            else:
                return False, f"未找到測試用的 SAVE_DATA 檔案 (嘗試路徑: {target_path})"

        cc = core.CountryCode.from_code(country_code)
        gv = core.GameVersion.from_string(game_version)
        
        # 呼叫核心下載邏輯
        server_handler, result = core.ServerHandler.from_codes(
            transfer_code, 
            confirmation_code, 
            cc, 
            gv, 
            print=False, 
            save_backup=False # 在 Render 上不保存備份檔案
        )
        
        if server_handler is None:
            if result is None:
                # response is None → 無法連線到伺服器
                reason = "無法連線至遊戲伺服器（網路逾時或防火牆阻擋）"
            else:
                # HTTP 回應不是 octet-stream → 伺服器拒絕請求（T-011：statusCode 中文對照）
                resp = result.response
                status = getattr(resp, 'status_code', '?')
                try:
                    body_json = resp.json() if resp else {}
                    ponos_code = body_json.get('statusCode', 0)
                except Exception:
                    ponos_code = 0

                # PONOS statusCode 中文對照表
                PONOS_ERROR_MAP = {
                    101: "認證失敗：轉移碼或認證碼錯誤，請重新確認後再試。",
                    111: "帳號驗證失敗：請確認地區（TW/JP/EN/KR）與遊戲版本是否正確。",
                    104: "帳號不存在：此轉移碼已失效或從未被使用過。",
                    107: "伺服器維護中：請稍後再試。",
                    400: "請求格式錯誤：請確認代碼格式（轉移碼為9位英數字）。",
                    429: "請求過於頻繁：請稍等幾分鐘後再試（防刷機制）。",
                }
                zh_reason = PONOS_ERROR_MAP.get(
                    ponos_code,
                    f"伺服器拒絕（HTTP {status}，代碼 {ponos_code}）"
                )
                reason = zh_reason
            print(f"[login] FAILED: {reason}", flush=True)
            return False, f"登入失敗：{reason}"
            
        self.server_handler = server_handler
        self.current_save = server_handler.save_file

        # 自動跳過新手教學邏輯
        if self.current_save and getattr(self.current_save, "tutorial_state", 0) == 0:
            core.StoryChapters.clear_tutorial(self.current_save)
            self.tutorial_auto_skipped = True
            print("[login] Tutorial auto-skipped for new account.", flush=True)

        return True, "成功"

    def get_talent_orbs_list(self):
        talent_orbs_list = []
        try:
            from bcsfe.core.game.catbase.talent_orbs import OrbInfoList
            orb_info_list = OrbInfoList.create(self.current_save)
            if orb_info_list:
                # ── 屬性限定 S 級本能珠（依目標種族分組） ──────────────
                groups = {}
                for i, orb in enumerate(orb_info_list.orb_info_list):
                    if not orb.target or orb.rank != "S":
                        continue

                    target = orb.target
                    if target not in groups:
                        groups[target] = {
                            "name": f"全 S【{target}】本能珠",
                            "amount": 0
                        }

                    if hasattr(self.current_save.talent_orbs, "orbs") and i in self.current_save.talent_orbs.orbs:
                        if groups[target]["amount"] == 0:
                            groups[target]["amount"] = self.current_save.talent_orbs.orbs[i].value

                for target, info in groups.items():
                    talent_orbs_list.append({
                        "id": f"ATTR_{target}",
                        "name": info["name"],
                        "amount": info["amount"]
                    })

                # ── 通用 S 級本能珠（無目標屬性，依效果名稱分組） ─────
                univ_groups = {}
                for i, orb in enumerate(orb_info_list.orb_info_list):
                    if orb.rank != "S" or orb.target:
                        continue

                    effect = orb.effect
                    if effect not in univ_groups:
                        univ_groups[effect] = {
                            "name": f"全 S【通用】{effect}",
                            "amount": 0
                        }

                    if hasattr(self.current_save.talent_orbs, "orbs") and i in self.current_save.talent_orbs.orbs:
                        if univ_groups[effect]["amount"] == 0:
                            univ_groups[effect]["amount"] = self.current_save.talent_orbs.orbs[i].value

                for effect, info in univ_groups.items():
                    talent_orbs_list.append({
                        "id": f"UNIV_{effect}",
                        "name": info["name"],
                        "amount": info["amount"]
                    })

                talent_orbs_list.sort(key=lambda x: x["name"])

        except Exception as e:
            print(f"Exception in get_talent_orbs_list: {e}", flush=True)
            import traceback
            traceback.print_exc()
        return talent_orbs_list

    def get_save_data(self):
        if not self.current_save:
            return None
            
        return {
            "inquiry_code": getattr(self.current_save, "inquiry_code", ""),
            "catfood": getattr(self.current_save, "catfood", 0),
            "xp": getattr(self.current_save, "xp", 0),
            "np": getattr(self.current_save, "np", 0),
            "leadership": getattr(self.current_save, "leadership", 0),
            "normal_tickets": getattr(self.current_save, "normal_tickets", 0),
            "rare_tickets": getattr(self.current_save, "rare_tickets", 0),
            "platinum_tickets": getattr(self.current_save, "platinum_tickets", 0),
            "legend_tickets": getattr(self.current_save, "legend_tickets", 0),
            "platinum_shards": getattr(self.current_save, "platinum_shards", 0),
            "tutorial_cleared": getattr(self.current_save, "tutorial_state", 0) > 0,
            "battle_items": [item.amount for item in getattr(self.current_save.battle_items, "items", [])] if hasattr(self.current_save, "battle_items") else [],
            "catamins": list(getattr(self.current_save, "catamins", []) or []),
            "catseyes": list(getattr(self.current_save, "catseyes", []) or []),
            "catfruit": list(getattr(self.current_save, "catfruit", []) or []),
            "base_materials": [item.amount for item in self.current_save.ototo.base_materials.materials] if hasattr(self.current_save, "ototo") and self.current_save.ototo and hasattr(self.current_save.ototo, "base_materials") and self.current_save.ototo.base_materials else [],
            "talent_orbs": self.get_talent_orbs_list(),
            "labyrinth_medals": list(getattr(self.current_save, "labyrinth_medals", []) or []),
            "event_lucky_tickets": getattr(self.current_save, "lucky_tickets", [0])[0] if getattr(self.current_save, "lucky_tickets", None) else 0,
            "play_time": getattr(self.current_save.officer_pass, "play_time", 0) // 30 // 3600 if hasattr(self.current_save, "officer_pass") else 0,
            "gold_pass_renewal_times": getattr(
                getattr(getattr(self.current_save, "officer_pass", None), "gold_pass", None),
                "total_renewal_times",
                0,
            ),
            "banned": getattr(self.current_save, "show_ban_message", False),
            "tutorial_auto_skipped": self.tutorial_auto_skipped
        }

    def _clamp(self, val, max_val, min_val=0):
        """核心安全性限制器，確保數值不溢出且不小於最小值"""
        try:
            v = int(val)
            mv = int(max_val)
            if v > mv:
                return mv
            if v < min_val:
                return min_val
            return v
        except (ValueError, TypeError):
            return min_val

    def patch_items(self, updates: dict):
        if not self.current_save:
            return False
            
        max_vals = core.core_data.max_value_manager

        # 基礎物資與貨幣
        if "catfood" in updates and updates["catfood"] is not None:
            # 貓罐頭強制上限 45,000 以維護安全
            self.current_save.catfood = self._clamp(updates["catfood"], max_vals.get("catfood") or 45000)
            
        if "xp" in updates and updates["xp"] is not None:
            self.current_save.xp = self._clamp(updates["xp"], max_vals.get("xp"))
        if "np" in updates and updates["np"] is not None:
            self.current_save.np = self._clamp(updates["np"], max_vals.get("np"))
        if "leadership" in updates and updates["leadership"] is not None:
            self.current_save.leadership = self._clamp(updates["leadership"], max_vals.get("leadership"))
            
        if "normal_tickets" in updates and updates["normal_tickets"] is not None:
            self.current_save.normal_tickets = self._clamp(updates["normal_tickets"], max_vals.get("normal_tickets"))
        if "rare_tickets" in updates and updates["rare_tickets"] is not None:
            self.current_save.rare_tickets = self._clamp(updates["rare_tickets"], 299)
        if "platinum_tickets" in updates and updates["platinum_tickets"] is not None:
            self.current_save.platinum_tickets = self._clamp(updates["platinum_tickets"], max_vals.get("platinum_tickets"))
        if "legend_tickets" in updates and updates["legend_tickets"] is not None:
            self.current_save.legend_tickets = self._clamp(updates["legend_tickets"], max_vals.get("legend_tickets"))
        if "platinum_shards" in updates and updates["platinum_shards"] is not None:
            # 白金碎片上限 99
            self.current_save.platinum_shards = self._clamp(updates["platinum_shards"], 99)
            
        if "battle_items" in updates and updates["battle_items"]:
            limit = max_vals.get("battle_items")
            for i, val in enumerate(updates["battle_items"]):
                if i < len(self.current_save.battle_items.items):
                    self.current_save.battle_items.items[i].amount = self._clamp(val, limit)
                    
        if "catseyes" in updates and updates["catseyes"]:
            limit = max_vals.get("catseyes")
            self.current_save.catseyes = [self._clamp(val, limit) for val in updates["catseyes"]]
            
        if "catfruit" in updates and updates["catfruit"]:
            limit = max_vals.get_new("catfruit") or 998
            self.current_save.catfruit = [self._clamp(val, limit) for val in updates["catfruit"]]
            
        if "catamins" in updates and updates["catamins"]:
            limit = max_vals.get("catamins")
            self.current_save.catamins = [self._clamp(val, limit) for val in updates["catamins"]]

        if "base_materials" in updates and updates["base_materials"]:
            materials = self.current_save.ototo.base_materials.materials
            limit = max_vals.get("base_materials")
            for i, val in enumerate(updates["base_materials"]):
                if i < len(materials):
                    materials[i].amount = self._clamp(val, limit)
                    
        if "talent_orbs" in updates and updates["talent_orbs"]:
            from bcsfe.core.game.catbase.talent_orbs import OrbInfoList
            orb_info_list = OrbInfoList.create(self.current_save)
            limit = max_vals.get("talent_orbs") or 998
            
            for key, val in updates["talent_orbs"].items():
                if isinstance(key, str) and key.startswith("ATTR_"):
                    # 屬性分組處理（種族限定 S 級）
                    target_attr = key.replace("ATTR_", "")
                    for i, orb in enumerate(orb_info_list.orb_info_list):
                        if orb.rank == "S" and orb.target == target_attr:
                            if hasattr(self.current_save, "talent_orbs"):
                                self.current_save.talent_orbs.set_orb(i, self._clamp(val, limit))
                elif isinstance(key, str) and key.startswith("UNIV_"):
                    # 通用 S 級本能珠（無目標屬性，依效果名稱匹配）
                    effect_name = key.replace("UNIV_", "")
                    for i, orb in enumerate(orb_info_list.orb_info_list):
                        if orb.rank == "S" and not orb.target and orb.effect == effect_name:
                            if hasattr(self.current_save, "talent_orbs"):
                                self.current_save.talent_orbs.set_orb(i, self._clamp(val, limit))
                else:
                    # 原始 ID 處理 (相容性)
                    if hasattr(self.current_save, "talent_orbs"):
                        try:
                            self.current_save.talent_orbs.set_orb(int(key), self._clamp(val, limit))
                        except (ValueError, TypeError):
                            continue
                        
        if "labyrinth_medals" in updates and updates["labyrinth_medals"]:
            limit = max_vals.get("labyrinth_medals")
            self.current_save.labyrinth_medals = [self._clamp(val, limit) for val in updates["labyrinth_medals"]]
            
        if "event_lucky_tickets" in updates and updates["event_lucky_tickets"] is not None:
            limit = max_vals.get("event_tickets")
            self.current_save.lucky_tickets = [self._clamp(updates["event_lucky_tickets"], limit)]
        
        if "play_time" in updates and updates["play_time"] is not None:
            # Convert hours back to frames (1 hour = 3600 seconds * 30 FPS)
            if hasattr(self.current_save, "officer_pass"):
                # 設定遊玩時間安全上限 (例如 99999 小時)
                self.current_save.officer_pass.play_time = self._clamp(updates["play_time"], 99999) * 3600 * 30
            
        if (
            "gold_pass_renewal_times" in updates
            and updates["gold_pass_renewal_times"] is not None
            and hasattr(self.current_save, "officer_pass")
            and hasattr(self.current_save.officer_pass, "gold_pass")
            and self.current_save.officer_pass.gold_pass is not None
        ):
            club = self.current_save.officer_pass.gold_pass
            try:
                val = int(updates["gold_pass_renewal_times"])
            except (ValueError, TypeError):
                val = 0
            
            if val < 0:
                if hasattr(club, "remove_gold_pass"):
                    club.remove_gold_pass(self.current_save)
            else:
                club.total_renewal_times = self._clamp(val, 99999)
                
                officer_id = getattr(club, "officer_id", -1)
                if officer_id <= 0:
                    club.officer_id = core.NyankoClub.get_random_officer_id()
                
                import time
                import datetime
                start_date_now = int(time.time())
                total_days = 30
                end_date_now = start_date_now + int(datetime.timedelta(days=total_days).total_seconds())
                end_date_total = start_date_now + int(datetime.timedelta(days=total_days * 2).total_seconds())
                
                club.start_date_now = float(start_date_now)
                club.end_date_now = float(end_date_now)
                club.start_date_next = float(end_date_now)
                club.end_date_next = float(end_date_total)
                club.start_date_total = float(start_date_now)
                club.end_date_total = float(end_date_total)
                club.time_error_end = float(start_date_now)
                club.total_state_updates = club.total_renewal_times
                
                club.login_bonus_date = 0.0
                club.remaing_days_popup = 0.0
                club.first_popup_flag = True
                club.badge_flag = False
                club.claimed_rewards = {}
                
                if hasattr(self.current_save, "logins") and self.current_save.logins is not None:
                    login = self.current_save.logins.get_login(5100)
                    if login is not None:
                        login.count = 0

        return True

    async def patch_advanced(self, advanced: dict):
        if not self.current_save:
            return False
            
        cat_opts = advanced.get("cats")
        if cat_opts:
            if cat_opts.get("unlock_all"):
                for cat in self.current_save.cats.cats:
                    cat.unlock(self.current_save)
            if cat_opts.get("max_level"):
                max_lv = core.Upgrade(base=80, plus=0)
                for cat in self.current_save.cats.cats:
                    if cat.unlocked:
                        cat.set_upgrade(self.current_save, max_lv)
            if cat_opts.get("true_form"):
                for cat in self.current_save.cats.cats:
                    if cat.unlocked:
                        cat.set_form(2, self.current_save)
            if cat_opts.get("fourth_form"):
                for cat in self.current_save.cats.cats:
                    if cat.unlocked:
                        cat.set_form(3, self.current_save)
            if cat_opts.get("max_talents"):
                for cat in self.current_save.cats.cats:
                    if cat.unlocked and cat.talents:
                        for talent in cat.talents:
                            talent.level = 10
            
            # 獲得特定貓咪 (批次) — T-010：加入結構化驗證與錯誤回報
            cat_ids_to_unlock = cat_opts.get("unlock_cat_ids")
            if cat_ids_to_unlock and isinstance(cat_ids_to_unlock, list):
                total_cats = len(self.current_save.cats.cats)
                unlock_results = []  # 收集每個 ID 的處理結果

                for raw_entry in cat_ids_to_unlock:
                    raw_str = str(raw_entry).strip()
                    if not raw_str:
                        continue

                    try:
                        # 驗證格式：只允許 "數字" 或 "數字-數字"
                        parts = raw_str.split("-")
                        if not parts[0].isdigit():
                            unlock_results.append({"id": raw_str, "ok": False, "msg": "格式錯誤（應為 ID 或 ID-形態）"})
                            continue

                        cat_id = int(parts[0])
                        target_form = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1

                        # 驗證 ID 範圍
                        if cat_id < 0 or cat_id >= total_cats:
                            unlock_results.append({
                                "id": raw_str, "ok": False,
                                "msg": f"ID {cat_id} 超出範圍（此存檔最大為 {total_cats - 1}）"
                            })
                            continue

                        # 驗證形態範圍
                        if target_form < 1 or target_form > 4:
                            unlock_results.append({"id": raw_str, "ok": False, "msg": f"形態 {target_form} 無效（需為 1~4）"})
                            continue

                        cat = self.current_save.cats.cats[cat_id]
                        cat.unlock(self.current_save)

                        # 同步等級與形態
                        if target_form >= 4:
                            cat.set_upgrade(self.current_save, core.Upgrade(base=60, plus=0))
                        elif target_form >= 3:
                            cat.set_upgrade(self.current_save, core.Upgrade(base=30, plus=0))
                        elif target_form >= 2:
                            cat.set_upgrade(self.current_save, core.Upgrade(base=10, plus=0))

                        if target_form > 1:
                            cat.set_form(target_form - 1, self.current_save)

                        unlock_results.append({"id": raw_str, "ok": True, "msg": f"ID {cat_id} 解鎖成功（形態 {target_form}）"})

                    except Exception as e:
                        unlock_results.append({"id": raw_str, "ok": False, "msg": f"未知錯誤：{str(e)}"})

                # 記錄結果至 instance 供 API 層讀取
                self._last_unlock_results = unlock_results
                failed = [r for r in unlock_results if not r["ok"]]
                if failed:
                    print(f"[patch_advanced] 以下貓咪解鎖失敗：{failed}", flush=True)

        tech_opts = advanced.get("tech")
        if tech_opts and tech_opts.get("max_all_tech"):
            max_tech = core.Upgrade(base=30, plus=10)
            for skill in self.current_save.special_skills.skills:
                skill.upgrade = max_tech

        prog_opts = advanced.get("progress")
        if prog_opts:
            if prog_opts.get("max_gamatoto"):
                # 校準 Gamatoto 上限至 130
                self.current_save.gamatoto.level = 130
                self.current_save.gamatoto.xp = 99999999
            elif "gamatoto_level" in prog_opts:
                self.current_save.gamatoto.level = self._clamp(prog_opts["gamatoto_level"], 130)
            if prog_opts.get("best_gamatoto_members"):
                members_name = core.GamatotoMembersName(self.current_save)
                legend_members = members_name.get_all_rarity(4)
                helpers = []
                if legend_members:
                    # 取前 10 個傳說級隊員
                    for member in legend_members[:10]:
                        helpers.append(core.Helper(member.member_id))
                self.current_save.gamatoto.helpers = core.Helpers(helpers)

        special_opts = advanced.get("special")
        if special_opts:
            if special_opts.get("all_cat_full"):
                max_lv = core.Upgrade(base=80, plus=0)
                for cat in self.current_save.cats.cats:
                    cat.unlock(self.current_save)
                    cat.set_upgrade(self.current_save, max_lv)
                    cat.set_form(3, self.current_save)
            if special_opts.get("max_tech_full"):
                max_tech = core.Upgrade(base=30, plus=10)
                for skill in self.current_save.special_skills.skills:
                    skill.upgrade = max_tech

        return True

    def patch_stages(self, updates: dict):
        if not self.current_save:
            return False
        if updates.get("clear_tutorial"):
            core.StoryChapters.clear_tutorial(self.current_save)
            
        if updates.get("clear_world"):
            for i in range(3):
                if i < len(self.current_save.story.chapters):
                    self.current_save.story.chapters[i].clear_chapter()
                    
        if updates.get("clear_future"):
            for i in range(4, 7):
                if i < len(self.current_save.story.chapters):
                    self.current_save.story.chapters[i].clear_chapter()
                    
        if updates.get("clear_cosmos"):
            for i in range(7, 10):
                if i < len(self.current_save.story.chapters):
                    self.current_save.story.chapters[i].clear_chapter()
                
        if updates.get("clear_aku"):
            if hasattr(self.current_save, "aku"):
                aku = self.current_save.aku
                for chapters_stars in aku.chapters:
                    for chapter in chapters_stars.chapters:
                        for stage in chapter.stages:
                            stage.clear_stage()

        if updates.get("max_treasures_world"):
            for i in range(3):
                if i < len(self.current_save.story.chapters):
                    chapter = self.current_save.story.chapters[i]
                    for stage in chapter.get_valid_treasure_stages():
                        stage.set_treasure(3)
                        
        if updates.get("max_treasures_future"):
            for i in range(4, 7):
                if i < len(self.current_save.story.chapters):
                    chapter = self.current_save.story.chapters[i]
                    for stage in chapter.get_valid_treasure_stages():
                        stage.set_treasure(3)

        if updates.get("max_treasures_cosmos"):
            for i in range(7, 10):
                if i < len(self.current_save.story.chapters):
                    chapter = self.current_save.story.chapters[i]
                    for stage in chapter.get_valid_treasure_stages():
                        stage.set_treasure(3)

        if updates.get("unlock_medals"):
            medal_names = core.core_data.get_medal_names(self.current_save)
            if medal_names and medal_names.medal_names:
                total_medals = len(medal_names.medal_names)
                for i in range(total_medals):
                    # 再次確認 medals 物件存在
                    if hasattr(self.current_save, "medals") and self.current_save.medals:
                        self.current_save.medals.add_medal(i)

        return True

    async def upload(self):
        ret_codes = None
        if not self.server_handler:
            if self.current_save:
                # 模擬上傳成功
                ret_codes = ("TEST-SUCCESS", "0000")
            else:
                return None, "目前無活動工作階段 (請重新登入)"
        else:
            ret_codes = self.server_handler.get_codes()
            
        if ret_codes:
            # 確保內容也會印在伺服器日誌中，防止重新整理遺失
            print(f"\n[SUCCESS] 上傳成功！", flush=True)
            print(f"新轉移碼 (Transfer Code): {ret_codes[0]}", flush=True)
            print(f"新認證碼 (Confirmation Code): {ret_codes[1]}", flush=True)
            print(f"請務必保存以上資訊，以免遺失。\n", flush=True)
            
            # 將每次修改/上傳後的存檔完全儲存至 SQLite 資料庫中
            try:
                from bcsfe_web.database import insert_save_history
                save_file = self.current_save
                save_data_b64 = save_file.to_data().to_base_64()
                inquiry_code = getattr(save_file, "inquiry_code", "")
                cc = save_file.cc.get_code() if hasattr(save_file, "cc") else "tw"
                gv = save_file.game_version.to_string() if hasattr(save_file, "game_version") else "15.3.0"
                
                # 建立歷史存檔摘要以供後台展示
                summary = {
                    "catfood": getattr(save_file, "catfood", 0),
                    "xp": getattr(save_file, "xp", 0),
                    "np": getattr(save_file, "np", 0),
                    "user_rank": save_file.calculate_user_rank() if hasattr(save_file, "calculate_user_rank") else 0,
                    "leadership": getattr(save_file, "leadership", 0),
                    "normal_tickets": getattr(save_file, "normal_tickets", 0),
                    "rare_tickets": getattr(save_file, "rare_tickets", 0),
                    "platinum_tickets": getattr(save_file, "platinum_tickets", 0),
                    "legend_tickets": getattr(save_file, "legend_tickets", 0),
                    "play_time": getattr(save_file.officer_pass, "play_time", 0) // 30 // 3600 if hasattr(save_file, "officer_pass") else 0,
                    "cats_count": len([c for c in save_file.cats.cats if c.unlocked]) if hasattr(save_file, "cats") else 0,
                }

                insert_save_history(
                    inquiry_code=inquiry_code,
                    transfer_code=ret_codes[0],
                    confirmation_code=ret_codes[1],
                    country_code=cc,
                    game_version=gv,
                    save_data_b64=save_data_b64,
                    summary=summary
                )
            except Exception as db_err:
                print(f"Error saving save history to DB: {db_err}", flush=True)

            return {"transfer_code": ret_codes[0], "confirmation_code": ret_codes[1]}, "成功"
        return None, "上傳至遊戲伺服器失敗，請稍後再試"


    async def transplant_account(
        self,
        source_tc: str, source_cc: str,
        target_tc: str, target_cc: str,
        country_code: str, game_version: str,
    ):
        """
        高安全性數據內容移植 (Safe Transplant Pro Max)：
        1. 下載來源帳與目標帳的進度物件。
        2. 以「目標帳」為基底，保留所有身分標識與隱藏指紋。
        3. 將「來源帳」的核心進度欄位 (PROGRESS_FIELDS) 用 deepcopy 覆蓋至目標帳。
        4. 數據清理：重設所有時間軸欄位為目前時間，消除邏輯死角與封號標記。
        5. 重新簽署存檔 (set_hash)。
        """
        import copy
        import time

        # ── Step 1：下載來源帳號 ───────────────────────────────────────
        success, msg = await self.login_and_fetch(
            source_tc, source_cc, country_code, game_version
        )
        if not success:
            return None, f"來源帳號登入失敗：{msg}"
        source_save = self.current_save

        # ── Step 2：下載目標帳號 ───────────────────────────────────────
        success, msg = await self.login_and_fetch(
            target_tc, target_cc, country_code, game_version
        )
        if not success:
            return None, f"目標帳號登入失敗：{msg}"
        target_save = self.current_save
        
        # 取得目標帳號的 handler (用於稍後上傳)
        target_handler = self.server_handler

        # ── Step 3：執行安全注入 (精準覆蓋所有進度與狀態) ─────────────
        # 定義必須從「目標空殼帳號」保留的身分關鍵欄位 (絕對不可被覆蓋)
        IDENTITY_FIELDS = [
            "inquiry_code", "password_refresh_token", "player_id", "os_value", 
            "full_gameversion", "save_data_4_hash", "backup_counter", "backup_frame", 
            "order_ids", "usl1", "usl2", "transfer_code", "confirmation_code",
            "data", "save_path", "package_name", "cc", "game_version",
            "energy_penalty_timestamp", "last_checked_energy_recovery_time", "date_int",
            "server_handler"
        ]
        
        # 需要重置為目前時間的欄位 (稍後獨立處理)
        TIME_FIELDS = [
            "timestamp", "g_timestamp", "g_servertimestamp", "date", "server_timestamp",
            "g_timestamp_2", "g_servertimestamp_2", "m_gettimesave", "m_gettimesave_2",
            "m_dGetTimeSave2", "m_dGetTimeSave3", "unknown_timestamp", "last_checked_reward_time",
            "last_checked_expedition_time", "last_checked_zombie_time", "last_checked_castle_time",
            "year", "month", "day"
        ]

        # 1. 拷貝所有【非身分】與【非時間】的欄位從 source 到 target
        for field, src_val in vars(source_save).items():
            if field in IDENTITY_FIELDS or field in TIME_FIELDS:
                continue
            try:
                setattr(target_save, field, copy.deepcopy(src_val))
            except Exception as e:
                print(f"[transplant] skip copying field '{field}': {e}", flush=True)

        # 2. 刪除 target 中有但 source 中沒有的【非身分】欄位 (抹除目標帳號多出的解鎖殘留)
        for field in list(vars(target_save).keys()):
            if field not in IDENTITY_FIELDS and field not in TIME_FIELDS:
                if not hasattr(source_save, field):
                    try:
                        delattr(target_save, field)
                    except Exception as e:
                        pass

        # ── Step 4：數據指紋清理 (Data Scrubbing) ──────────────────────
        current_time = time.time()
        
        # 需要重置為目前時間的欄位
        TIME_FIELDS = [
            "timestamp", "g_timestamp", "g_servertimestamp", "date", "server_timestamp",
            "g_timestamp_2", "g_servertimestamp_2", "m_gettimesave", "m_gettimesave_2",
            "m_dGetTimeSave2", "m_dGetTimeSave3", "unknown_timestamp", "last_checked_reward_time",
            "last_checked_expedition_time", "last_checked_zombie_time", "last_checked_castle_time"
        ]
        
        for t_field in TIME_FIELDS:
            if hasattr(target_save, t_field):
                old_val = getattr(target_save, t_field)
                if isinstance(old_val, float):
                    setattr(target_save, t_field, float(current_time))
                elif isinstance(old_val, int):
                    setattr(target_save, t_field, int(current_time))
                elif hasattr(old_val, "year") and hasattr(old_val, "month"): # Is datetime
                    import datetime
                    setattr(target_save, t_field, datetime.datetime.fromtimestamp(current_time))
                    
        # 也手動更新獨立的時間欄位
        if hasattr(target_save, "year"):
            import datetime
            now = datetime.datetime.fromtimestamp(current_time)
            target_save.year = now.year
            target_save.month = now.month
            target_save.day = now.day

        # 消除潛在的封號標記與連線警告
        if hasattr(target_save, "show_ban_message"):
            target_save.show_ban_message = False
        if hasattr(target_save, "banned"):
            target_save.banned = False

        # 同步新手教學狀態：如果來源帳號已過教學，目標帳號也必須清除
        if getattr(source_save, "tutorial_state", 0) > 0:
            core.StoryChapters.clear_tutorial(target_save)

        # ── Step 5：重新計算校驗碼 ─────────────────────────────────────
        target_save.set_hash()

        # 更新狀態準備上傳
        self.current_save = target_save
        if target_handler:
            target_handler.save_file = target_save
            self.server_handler = target_handler

        # ── Step 6：執行上傳到目標帳號 ─────────────────────────────────
        codes, msg_up = await self.upload()
        if not codes:
            return None, f"移植後上傳失敗：{msg_up}"

        return {
            "new_transfer_code":     codes["transfer_code"],
            "new_confirmation_code": codes["confirmation_code"],
        }, "數據內容移植成功！進度已完全轉移至目標帳號。"

    async def restore_save_to_account(
        self,
        record_id: int,
        target_tc: str, target_cc: str,
        country_code: str, game_version: str,
    ):
        """
        還原資料庫中的存檔紀錄到指定的目標帳號（空殼）。
        除 inquiry_code 等身分識別欄位外，完全複製進度。
        """
        import copy
        import time
        import base64
        from bcsfe_web.database import get_save_record

        # 1. 從資料庫讀取來源存檔
        record = get_save_record(record_id)
        if not record:
            return None, "找不到指定的存檔紀錄"
        
        save_data_b64 = record["save_data_b64"]
        try:
            # 解碼並載入存檔
            save_bytes = base64.b64decode(save_data_b64)
            source_save = core.SaveFile(dt=core.Data(save_bytes))
        except Exception as e:
            return None, f"解析儲存的存檔失敗: {str(e)}"

        # 2. 下載目標帳號
        success, msg = await self.login_and_fetch(
            target_tc, target_cc, country_code, game_version
        )
        if not success:
            return None, f"目標帳號登入失敗：{msg}"
        target_save = self.current_save
        target_handler = self.server_handler

        # 3. 複製欄位（除身分與時間欄位外）
        IDENTITY_FIELDS = [
            "inquiry_code", "password_refresh_token", "player_id", "os_value", 
            "full_gameversion", "save_data_4_hash", "backup_counter", "backup_frame", 
            "order_ids", "usl1", "usl2", "transfer_code", "confirmation_code",
            "data", "save_path", "package_name", "cc", "game_version",
            "energy_penalty_timestamp", "last_checked_energy_recovery_time", "date_int",
            "server_handler"
        ]
        
        TIME_FIELDS = [
            "timestamp", "g_timestamp", "g_servertimestamp", "date", "server_timestamp",
            "g_timestamp_2", "g_servertimestamp_2", "m_gettimesave", "m_gettimesave_2",
            "m_dGetTimeSave2", "m_dGetTimeSave3", "unknown_timestamp", "last_checked_reward_time",
            "last_checked_expedition_time", "last_checked_zombie_time", "last_checked_castle_time",
            "year", "month", "day"
        ]

        for field, src_val in vars(source_save).items():
            if field in IDENTITY_FIELDS or field in TIME_FIELDS:
                continue
            try:
                setattr(target_save, field, copy.deepcopy(src_val))
            except Exception as e:
                print(f"[restore] skip copying field '{field}': {e}", flush=True)

        for field in list(vars(target_save).keys()):
            if field not in IDENTITY_FIELDS and field not in TIME_FIELDS:
                if not hasattr(source_save, field):
                    try:
                        delattr(target_save, field)
                    except Exception as e:
                        pass

        # 4. 資料指紋清理
        current_time = time.time()
        for t_field in TIME_FIELDS:
            if hasattr(target_save, t_field):
                old_val = getattr(target_save, t_field)
                if isinstance(old_val, float):
                    setattr(target_save, t_field, float(current_time))
                elif isinstance(old_val, int):
                    setattr(target_save, t_field, int(current_time))
                elif hasattr(old_val, "year") and hasattr(old_val, "month"):
                    import datetime
                    setattr(target_save, t_field, datetime.datetime.fromtimestamp(current_time))
                    
        if hasattr(target_save, "year"):
            import datetime
            now = datetime.datetime.fromtimestamp(current_time)
            target_save.year = now.year
            target_save.month = now.month
            target_save.day = now.day

        if hasattr(target_save, "show_ban_message"):
            target_save.show_ban_message = False
        if hasattr(target_save, "banned"):
            target_save.banned = False

        if getattr(source_save, "tutorial_state", 0) > 0:
            core.StoryChapters.clear_tutorial(target_save)

        # 5. 重新簽署並上傳
        target_save.set_hash()
        self.current_save = target_save
        if target_handler:
            target_handler.save_file = target_save
            self.server_handler = target_handler

        codes, msg_up = await self.upload()
        if not codes:
            return None, f"還原後上傳失敗：{msg_up}"

        return {
            "new_transfer_code":     codes["transfer_code"],
            "new_confirmation_code": codes["confirmation_code"],
        }, "存檔還原成功！"

class SessionManager:
    def __init__(self, timeout_minutes=30):
        self._sessions: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._timeout = timeout_minutes * 60

    def create(self) -> str:
        session_id = str(uuid.uuid4())
        with self._lock:
            self._sessions[session_id] = {
                "service": BCSFE_Service(),
                "created_at": time.time(),
                "last_access": time.time(),
            }
        return session_id

    def get(self, session_id: str) -> BCSFE_Service | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            session["last_access"] = time.time()
            return session["service"]

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def cleanup_expired(self) -> int:
        now = time.time()
        with self._lock:
            expired = [
                sid for sid, s in self._sessions.items()
                if now - s["last_access"] > self._timeout
            ]
            for sid in expired:
                del self._sessions[sid]
        return len(expired)

session_manager = SessionManager()
