import sys
import os

# 確保能加載 src 中的 bcsfe 模組 (相對於目前檔案路徑)
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "..", "src")
if src_path not in sys.path:
    sys.path.append(src_path)

try:
    from bcsfe import core
except ImportError:
    print(f"Error: Could not find bcsfe source in {src_path}")

class BCSFE_Service:
    def __init__(self):
        self.current_save: core.SaveFile | None = None
        self.server_handler: core.ServerHandler | None = None

    async def login_and_fetch(self, transfer_code: str, confirmation_code: str, country_code: str, game_version: str):
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
            "talent_orbs": len(getattr(self.current_save.talent_orbs, "orbs", {})) if hasattr(self.current_save, "talent_orbs") else 0,
            "labyrinth_medals": getattr(self.current_save, "labyrinth_medals", [0])[0] if getattr(self.current_save, "labyrinth_medals", None) else 0,
            "event_lucky_tickets": getattr(self.current_save, "lucky_tickets", [0])[0] if getattr(self.current_save, "lucky_tickets", None) else 0
        }

    def patch_items(self, updates: dict):
        if not self.current_save:
            return False
            
        if "catfood" in updates and updates["catfood"] is not None:
            self.current_save.catfood = updates["catfood"]
        if "xp" in updates and updates["xp"] is not None:
            self.current_save.xp = updates["xp"]
        if "np" in updates and updates["np"] is not None:
            self.current_save.np = updates["np"]
        if "leadership" in updates and updates["leadership"] is not None:
            self.current_save.leadership = updates["leadership"]
        if "normal_tickets" in updates and updates["normal_tickets"] is not None:
            self.current_save.normal_tickets = updates["normal_tickets"]
        if "rare_tickets" in updates and updates["rare_tickets"] is not None:
            self.current_save.rare_tickets = updates["rare_tickets"]
        if "platinum_tickets" in updates and updates["platinum_tickets"] is not None:
            self.current_save.platinum_tickets = updates["platinum_tickets"]
        if "legend_tickets" in updates and updates["legend_tickets"] is not None:
            self.current_save.legend_tickets = updates["legend_tickets"]
        if "platinum_shards" in updates and updates["platinum_shards"] is not None:
            self.current_save.platinum_shards = updates["platinum_shards"]
            
        if "battle_items" in updates and updates["battle_items"]:
            for i, val in enumerate(updates["battle_items"]):
                if i < len(self.current_save.battle_items.items):
                    self.current_save.battle_items.items[i].amount = val
                    
        if "catseyes" in updates and updates["catseyes"]:
            self.current_save.catseyes = updates["catseyes"]
        if "catfruit" in updates and updates["catfruit"]:
            self.current_save.catfruit = updates["catfruit"]
        if "catamins" in updates and updates["catamins"]:
            self.current_save.catamins = updates["catamins"]

        if "base_materials" in updates and updates["base_materials"]:
            materials = self.current_save.ototo.base_materials.materials
            for i, val in enumerate(updates["base_materials"]):
                if i < len(materials):
                    materials[i].amount = val
                        
        if "labyrinth_medals" in updates and updates["labyrinth_medals"] is not None:
            self.current_save.labyrinth_medals = [updates["labyrinth_medals"]]
        if "event_lucky_tickets" in updates and updates["event_lucky_tickets"] is not None:
            self.current_save.lucky_tickets = [updates["event_lucky_tickets"]]
            
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
            if prog_opts.get("max_treasures"):
                for chapter in self.current_save.story.chapters:
                    chapter.treasures.set_all_superior()
            if prog_opts.get("max_gamatoto"):
                self.current_save.gamatoto.level = 130
                self.current_save.gamatoto.xp = 99999999
            if prog_opts.get("best_gamatoto_members"):
                for member in self.current_save.gamatoto.members:
                    member.member_type = 5
        return True

    def patch_stages(self, updates: dict):
        if not self.current_save:
            return False
        if updates.get("clear_tutorial"):
            core.StoryChapters.clear_tutorial(self.current_save)
            
        if updates.get("clear_world"):
            # 清除世界篇 (1-3)
            for i in range(3):
                self.current_save.story.chapters[i].clear_chapter()
                
        if updates.get("clear_aku"):
            # 清除魔界 (Aku Realm)
            if hasattr(self.current_save, "aku"):
                aku = self.current_save.aku
                # 遍歷所有星級與關卡
                for chapters_stars in aku.chapters:
                    for chapter in chapters_stars.chapters:
                        for stage in chapter.stages:
                            stage.clear_stage()
            
        return True

    async def upload(self):
        if not self.server_handler:
            return None, "No active session"
        codes = self.server_handler.get_codes()
        if codes:
            return {"transfer_code": codes[0], "confirmation_code": codes[1]}, "Success"
        return None, "Upload failed"

service = BCSFE_Service()
