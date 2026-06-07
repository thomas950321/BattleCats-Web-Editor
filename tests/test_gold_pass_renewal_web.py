from types import SimpleNamespace

from bcsfe_web.service import BCSFE_Service, core


class DummyGoldPass(SimpleNamespace):
    def remove_gold_pass(self, _save_file):
        self.officer_id = -1
        self.total_renewal_times = 0
        self.start_date_now = 0.0
        self.end_date_now = 0.0
        self.start_date_next = 0.0
        self.end_date_next = 0.0
        self.start_date_total = 0.0
        self.end_date_total = 0.0
        self.time_error_end = 0.0
        self.total_state_updates = 0
        self.login_bonus_date = 0.0
        self.remaing_days_popup = 0.0
        self.first_popup_flag = False
        self.badge_flag = False
        self.claimed_rewards = {}


class DummyMaxValues:
    def get(self, _key):
        return 99999

    def get_new(self, _key):
        return 998


def build_service_with_save():
    service = BCSFE_Service()
    service.get_talent_orbs_list = lambda: []

    gold_pass = DummyGoldPass(total_renewal_times=7, officer_id=123)
    officer_pass = SimpleNamespace(play_time=12 * 3600 * 30, gold_pass=gold_pass)
    
    class DummyLogin:
        count = 5
    class DummyLogins:
        def __init__(self):
            self.login = DummyLogin()
        def get_login(self, id):
            return self.login
    
    logins_mock = DummyLogins()
    
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
        logins=logins_mock,
        show_ban_message=False,
    )
    service.current_save = save
    return service, logins_mock.login


def test_get_save_data_includes_gold_pass_renewal_times():
    service, _ = build_service_with_save()

    data = service.get_save_data()

    assert data is not None
    assert data["gold_pass_renewal_times"] == 7
    assert data["play_time"] == 12


def test_patch_items_updates_gold_pass_renewal_times(monkeypatch):
    import time
    service, login_mock = build_service_with_save()
    monkeypatch.setattr(core.core_data, "max_value_manager", DummyMaxValues(), raising=False)

    ok = service.patch_items({"gold_pass_renewal_times": 123, "play_time": 24})

    assert ok is True
    gold_pass = service.current_save.officer_pass.gold_pass
    assert gold_pass.total_renewal_times == 123
    assert gold_pass.total_state_updates == 123
    assert service.current_save.officer_pass.play_time == 24 * 3600 * 30
    
    # Assert validity dates and rewards reset
    assert gold_pass.login_bonus_date == 0.0
    assert abs(gold_pass.start_date_now - time.time()) < 5
    assert gold_pass.claimed_rewards == {}
    assert login_mock.count == 0


def test_patch_items_zero_renewal_times_removes_gold_pass(monkeypatch):
    service, _ = build_service_with_save()
    monkeypatch.setattr(core.core_data, "max_value_manager", DummyMaxValues(), raising=False)

    ok = service.patch_items({"gold_pass_renewal_times": 0})

    assert ok is True
    gold_pass = service.current_save.officer_pass.gold_pass
    assert gold_pass.officer_id == -1
    assert gold_pass.total_renewal_times == 0
    assert gold_pass.end_date_total == 0.0
    assert gold_pass.claimed_rewards == {}
