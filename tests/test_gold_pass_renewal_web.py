from types import SimpleNamespace

from bcsfe_web.service import BCSFE_Service, core


class DummyMaxValues:
    def get(self, _key):
        return 99999

    def get_new(self, _key):
        return 998


def build_service_with_save():
    service = BCSFE_Service()
    service.get_talent_orbs_list = lambda: []

    gold_pass = SimpleNamespace(total_renewal_times=7)
    officer_pass = SimpleNamespace(play_time=12 * 3600 * 30, gold_pass=gold_pass)
    save = SimpleNamespace(
        inquiry_code="ABC123",
        catfood=10,
        xp=20,
        np=30,
        leadership=40,
        normal_tickets=1,
        rare_tickets=2,
        platinum_tickets=3,
        legend_tickets=4,
        platinum_shards=5,
        tutorial_state=1,
        battle_items=SimpleNamespace(items=[]),
        catamins=[],
        catseyes=[],
        catfruit=[],
        ototo=None,
        labyrinth_medals=[],
        lucky_tickets=[0],
        officer_pass=officer_pass,
        show_ban_message=False,
    )
    service.current_save = save
    return service


def test_get_save_data_includes_gold_pass_renewal_times():
    service = build_service_with_save()

    data = service.get_save_data()

    assert data is not None
    assert data["gold_pass_renewal_times"] == 7
    assert data["play_time"] == 12


def test_patch_items_updates_gold_pass_renewal_times(monkeypatch):
    service = build_service_with_save()
    monkeypatch.setattr(core.core_data, "max_value_manager", DummyMaxValues(), raising=False)

    ok = service.patch_items({"gold_pass_renewal_times": 123, "play_time": 24})

    assert ok is True
    assert service.current_save.officer_pass.gold_pass.total_renewal_times == 123
    assert service.current_save.officer_pass.play_time == 24 * 3600 * 30
