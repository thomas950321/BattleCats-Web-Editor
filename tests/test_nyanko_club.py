import time
from bcsfe.core.game.catbase.nyanko_club import NyankoClub

class DummySaveFile:
    class DummyLogins:
        def get_login(self, id):
            class DummyLogin:
                count = 5
            return DummyLogin()
    logins = DummyLogins()

def test_get_gold_pass_login_bonus_date():
    club = NyankoClub.init()
    save_file = DummySaveFile()
    club.get_gold_pass(12345, 30, save_file)
    
    # login_bonus_date should be 0.0, not end_date_now
    assert club.login_bonus_date == 0.0
    assert club.officer_id == 12345
    assert club.total_renewal_times == 2
    assert club.claimed_rewards == {}

def test_nyanko_club_deserialize_autofix():
    # Future login_bonus_date should be auto-fixed to 0.0
    future_time = time.time() + 1000000
    data = {
        "officer_id": 12345,
        "total_renewal_times": 3,
        "login_bonus_date": future_time,
        "claimed_rewards": {1: 1}
    }
    
    club = NyankoClub.deserialize(data)
    assert club.login_bonus_date == 0.0
    assert club.officer_id == 12345
