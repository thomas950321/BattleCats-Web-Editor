import sys
import os

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

    async def login_and_fetch(self, transfer_code: str, confirmation_code: str, country_code: str, game_version: str):
        if transfer_code == "TEST" and confirmation_code == "0000":
            save_path = core.Path.get_documents_folder().add("saves").add("SAVE_DATA")
            if save_path.exists():
                try:
                    data = save_path.read()
                    self.current_save = core.SaveFile(dt=data)
                    self.server_handler = None  # 測試就不發送上傳/認證
                    return True, "Loaded local test save"
                except Exception as e:
                    return False, f"Failed to load TEST save: {str(e)}"
            else:
                return False, "Local SAVE_DATA backup not found for test"

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
            return False, "Invalid codes or connection error"
            
        self.server_handler = server_handler
        self.current_save = server_handler.save_file

        return True, "Success"

    def get_talent_orbs_list(self):
        talent_orbs_list = []
        try:
            from bcsfe.core.game.catbase.talent_orbs import OrbInfoList
            orb_info_list = OrbInfoList.create(self.current_save)
            if orb_info_list:
                for i, orb in enumerate(orb_info_list.orb_info_list):
                    if not orb.target:
                        continue # 過濾無屬性對象的冗餘數據
                    
                    effect_text = orb.effect.replace("%@", orb.rank)
                    effect_text += f" ({orb.target})"
                    
                    count = 0
                    if hasattr(self.current_save.talent_orbs, "orbs") and i in self.current_save.talent_orbs.orbs:
                        count = self.current_save.talent_orbs.orbs[i].value
                    
                    talent_orbs_list.append({
                        "id": i,
                        "name": effect_text,
                        "amount": count
                    })
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
            "leadership": getattr(self.current_save, "current_energy", 0),
            "normal_tickets": getattr(self.current_save, "normal_tickets", 0),
            "rare_tickets": getattr(self.current_save, "rare_tickets", 0),
            "platinum_tickets": getattr(self.current_save, "platinum_tickets", 0),
            "legend_tickets": getattr(self.current_save, "legend_tickets", 0),
            "platinum_shards": getattr(self.current_save, "platinum_shards", 0),
            "tutorial_cleared": getattr(self.current_save, "tutorial_state", 0) > 0,
            "battle_items": [item.amount for item in self.current_save.battle_items.items],
            "catamins": getattr(self.current_save, "catamins", []),
            "catseyes": getattr(self.current_save, "catseyes", []),
            "catfruit": getattr(self.current_save, "catfruit", []),
            "base_materials": [item.amount for item in self.current_save.ototo.base_materials.materials] if hasattr(self.current_save, "ototo") else [],
            "talent_orbs": self.get_talent_orbs_list(),
            "labyrinth_medals": getattr(self.current_save, "labyrinth_medals", [0])[0] if getattr(self.current_save, "labyrinth_medals", None) else 0,
            "event_lucky_tickets": getattr(self.current_save, "lucky_tickets", [0])[0] if getattr(self.current_save, "lucky_tickets", None) else 0,
            "play_time": getattr(self.current_save.officer_pass, "play_time", 0) // 30 // 3600 if hasattr(self.current_save, "officer_pass") else 0
        }

    def patch_items(self, updates: dict):
        if not self.current_save:
            return False
            
        max_vals = core.core_data.max_value_manager

        if "catfood" in updates and updates["catfood"] is not None:
            self.current_save.catfood = min(updates["catfood"], max_vals.get("catfood"))
        if "xp" in updates and updates["xp"] is not None:
            self.current_save.xp = min(updates["xp"], max_vals.get("xp"))
        if "np" in updates and updates["np"] is not None:
            self.current_save.np = min(updates["np"], max_vals.get("np"))
        if "leadership" in updates and updates["leadership"] is not None:
            self.current_save.leadership = min(updates["leadership"], max_vals.get("leadership"))
            
        if "normal_tickets" in updates and updates["normal_tickets"] is not None:
            self.current_save.normal_tickets = min(updates["normal_tickets"], max_vals.get("normal_tickets"))
        if "rare_tickets" in updates and updates["rare_tickets"] is not None:
            self.current_save.rare_tickets = min(updates["rare_tickets"], max_vals.get("rare_tickets"))
        if "platinum_tickets" in updates and updates["platinum_tickets"] is not None:
            self.current_save.platinum_tickets = min(updates["platinum_tickets"], max_vals.get("platinum_tickets"))
        if "legend_tickets" in updates and updates["legend_tickets"] is not None:
            self.current_save.legend_tickets = min(updates["legend_tickets"], max_vals.get("legend_tickets"))
        if "platinum_shards" in updates and updates["platinum_shards"] is not None:
            self.current_save.platinum_shards = updates["platinum_shards"] # Shards limit is fine usually
            
        if "battle_items" in updates and updates["battle_items"]:
            max_val = max_vals.get("battle_items")
            for i, val in enumerate(updates["battle_items"]):
                if i < len(self.current_save.battle_items.items):
                    self.current_save.battle_items.items[i].amount = min(val, max_val)
                    
        if "catseyes" in updates and updates["catseyes"]:
            max_val = max_vals.get("catseyes")
            self.current_save.catseyes = [min(val, max_val) for val in updates["catseyes"]]
            
        if "catfruit" in updates and updates["catfruit"]:
            max_val = max_vals.get_new("catfruit") or 998
            self.current_save.catfruit = [min(val, max_val) for val in updates["catfruit"]]
            
        if "catamins" in updates and updates["catamins"]:
            max_val = max_vals.get("catamins")
            self.current_save.catamins = [min(val, max_val) for val in updates["catamins"]]

        if "base_materials" in updates and updates["base_materials"]:
            materials = self.current_save.ototo.base_materials.materials
            max_val = max_vals.get("base_materials")
            for i, val in enumerate(updates["base_materials"]):
                if i < len(materials):
                    materials[i].amount = min(val, max_val)
                    
        if "talent_orbs" in updates and updates["talent_orbs"]:
            max_val = max_vals.get("talent_orbs") or 998
            for i, val in enumerate(updates["talent_orbs"]):
                if hasattr(self.current_save, "talent_orbs"):
                    self.current_save.talent_orbs.set_orb(i, min(val, max_val))
                        
        if "labyrinth_medals" in updates and updates["labyrinth_medals"] is not None:
            max_val = max_vals.get("labyrinth_medals")
            self.current_save.labyrinth_medals = [min(updates["labyrinth_medals"], max_val)]
            
        if "event_lucky_tickets" in updates and updates["event_lucky_tickets"] is not None:
            max_val = max_vals.get("event_tickets")
            self.current_save.lucky_tickets = [min(updates["event_lucky_tickets"], max_val)]
        
        if "play_time" in updates and updates["play_time"] is not None:
            # Convert hours back to frames (1 hour = 3600 seconds * 30 FPS)
            if hasattr(self.current_save, "officer_pass"):
                self.current_save.officer_pass.play_time = updates["play_time"] * 3600 * 30
            
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

        tech_opts = advanced.get("tech")
        if tech_opts and tech_opts.get("max_all_tech"):
            max_tech = core.Upgrade(base=30, plus=10)
            for skill in self.current_save.special_skills.special_skills:
                skill.upgrade = max_tech

        prog_opts = advanced.get("progress")
        if prog_opts:
            if prog_opts.get("max_gamatoto"):
                self.current_save.gamatoto.level = 130
                self.current_save.gamatoto.xp = 99999999
            if prog_opts.get("best_gamatoto_members"):
                for member in self.current_save.gamatoto.members:
                    member.member_type = 5

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
                for skill in self.current_save.special_skills.special_skills:
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
            for i in range(3, 6):
                if i < len(self.current_save.story.chapters):
                    self.current_save.story.chapters[i].clear_chapter()
                    
        if updates.get("clear_cosmos"):
            for i in range(6, 9):
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
                    if hasattr(chapter, "treasures") and chapter.treasures:
                        chapter.treasures.set_all_superior()
                        
        if updates.get("max_treasures_future"):
            for i in range(3, 6):
                if i < len(self.current_save.story.chapters):
                    chapter = self.current_save.story.chapters[i]
                    if hasattr(chapter, "treasures") and chapter.treasures:
                        chapter.treasures.set_all_superior()

        if updates.get("max_treasures_cosmos"):
            for i in range(6, 9):
                if i < len(self.current_save.story.chapters):
                    chapter = self.current_save.story.chapters[i]
                    if hasattr(chapter, "treasures") and chapter.treasures:
                        chapter.treasures.set_all_superior()
                
        if updates.get("unlock_medals"):
            medal_names = core.core_data.get_medal_names(self.current_save)
            if medal_names and medal_names.medal_names:
                for i in range(len(medal_names.medal_names)):
                    self.current_save.medals.add_medal(i)
            
        return True

    async def upload(self):
        if not self.server_handler:
            if self.current_save:
                return {"transfer_code": "TEST-SUCCESS", "confirmation_code": "0000"}, "Success"
            return None, "No active session"
        codes = self.server_handler.get_codes()
        if codes:
            return {"transfer_code": codes[0], "confirmation_code": codes[1]}, "Success"
        return None, "Upload failed"

service = BCSFE_Service()
