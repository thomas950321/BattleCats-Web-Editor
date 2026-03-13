from pydantic import BaseModel
from typing import Optional, List, Dict

class SaveLogin(BaseModel):
    transfer_code: str
    confirmation_code: str
    country_code: str = "en"
    game_version: str = "13.0.0"

class ItemUpdate(BaseModel):
    catfood: Optional[int] = None
    xp: Optional[int] = None
    np: Optional[int] = None
    leadership: Optional[int] = None
    normal_tickets: Optional[int] = None
    rare_tickets: Optional[int] = None
    platinum_tickets: Optional[int] = None
    legend_tickets: Optional[int] = None
    platinum_shards: Optional[int] = None
    battle_items: Optional[List[int]] = None
    catamins: Optional[List[int]] = None
    catseyes: Optional[List[int]] = None
    catfruit: Optional[List[int]] = None
    base_materials: Optional[List[int]] = None
    labyrinth_medals: Optional[int] = None
    event_lucky_tickets: Optional[int] = None

class AdvancedOptions(BaseModel):
    cats: Optional[Dict[str, bool]] = None
    tech: Optional[Dict[str, bool]] = None
    progress: Optional[Dict[str, bool]] = None
    talent_orbs_option: Optional[str] = None

class StageOptions(BaseModel):
    clear_tutorial: Optional[bool] = None
    clear_world: Optional[bool] = None
    clear_aku: Optional[bool] = None

class SavePatchRequest(BaseModel):
    items: Optional[ItemUpdate] = None
    stages: Optional[StageOptions] = None
    advanced: Optional[AdvancedOptions] = None

class SaveDataResponse(BaseModel):
    inquiry_code: str
    catfood: int
    xp: int
    np: int
    leadership: int
    normal_tickets: int
    rare_tickets: int
    platinum_tickets: int
    legend_tickets: int
    platinum_shards: int
    tutorial_cleared: bool
    battle_items: List[int]
    catamins: List[int]
    catseyes: List[int]
    catfruit: List[int]
    base_materials: List[int]
    talent_orbs: int
    labyrinth_medals: int
    event_lucky_tickets: int
