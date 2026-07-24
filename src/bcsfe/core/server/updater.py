from __future__ import annotations
import sys
from typing import Any
import json
from bcsfe import core, __app_name__
import bcsfe


class Updater:
    def __init__(self):
        pass

    def get_local_version(self) -> str:
        return bcsfe.__version__

    def get_pypi_json(self) -> dict[str, Any] | None:
        url = f"https://pypi.org/pypi/{__app_name__}/json"
        # add a User-Agent since pypi started to block the default requests user-agent
        # this probably won't be needed in the future as i assume this block is temporary
        response = core.RequestHandler(
            url, headers={"User-Agent": "BCSFE-Updater"}
        ).get()
        if response is None:
            return None
        try:
            return response.json()
        except json.JSONDecodeError:
            return None

    def get_releases(self) -> list[str] | None:
        pypi_json = self.get_pypi_json()
        if pypi_json is None:
            return None
        releases = pypi_json.get("releases")
        if releases is None:
            return None
        return list(releases.keys())

    def get_latest_version(self, prereleases: bool = False) -> str | None:
        releases = self.get_releases()
        if releases is None:
            return None

        releases.reverse()
        if prereleases:
            return releases[0]
        else:
            for release in releases:
                if "b" not in release:
                    return release
            return releases[0]

    def get_latest_version_info(
        self, prereleases: bool = False
    ) -> dict[str, Any] | None:
        pypi_json = self.get_pypi_json()
        if pypi_json is None:
            return None
        releases = pypi_json.get("releases")
        if releases is None:
            return None
        return releases.get(self.get_latest_version(prereleases))

    def update(self, target_version: str) -> bool:
        binary = sys.orig_argv[0]
        python_aliases = [binary, "py", "python", "python3"]
        for python_alias in python_aliases:
            cmd = f"{python_alias} -m pip install --upgrade {__app_name__}=={target_version}"
            result = core.Path().run(cmd)
            if result.exit_code == 0:
                break
        else:
            pip_aliases = ["pip", "pip3"]
            for pip_alias in pip_aliases:
                cmd = f"{pip_alias} install --upgrade {__app_name__}=={target_version}"
                result = core.Path().run(cmd)
                if result.exit_code == 0:
                    break
            else:
                return False
        return True

    def has_enabled_pre_release(self) -> bool:
        return core.core_data.config.get_bool(core.ConfigKey.UPDATE_TO_BETA)

    @staticmethod
    def version_check(v1: str, v2: str) -> bool:
        v1_p = v1.split(".")
        v2_p = v2.split(".")

        for p1, p2 in zip(v1_p, v2_p):
            if p1.isdigit():
                p1 = int(p1)
            else:
                continue
            if p2.isdigit():
                p2 = int(p2)
            else:
                continue
            if p1 > p2:
                return True
            if p1 < p2:
                return False

        return len(v1_p) > len(v2_p)

    @staticmethod
    def beta_version_check(v1: str, v2: str) -> bool:
        is_local_beta = "b" in v2
        is_latest_beta = "b" in v1

        local_no_beta = v2.split("b")[0]
        latest_no_beta = v1.split("b")[0]

        if Updater.version_check(latest_no_beta, local_no_beta):
            return True
        elif Updater.version_check(local_no_beta, latest_no_beta):
            return False
        else:
            if v1 == v2:
                return False
            else:
                if is_local_beta and is_latest_beta:
                    return Updater.version_check(
                        v1.replace("b", "."),
                        v2.replace("b", "."),
                    )
                elif is_local_beta:
                    return True
                else:
                    return False
