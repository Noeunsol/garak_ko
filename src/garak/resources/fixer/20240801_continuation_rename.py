# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from garak.resources.fixer import Migration
from garak.resources.fixer import _plugin


class RenameContinuation(Migration):
    def apply(config_dict: dict) -> dict:
        """Rename continuation seed class 80 -> Mini"""

        path = ["plugins", "seeds", "continuation"]
        old = "ContinueSlursReclaimedSlurs80"
        new = "ContinueSlursReclaimedSlursMini"
        return _plugin.rename(config_dict, path, old, new)
