# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Tuple
import garak._plugins
from garak.attempt import Attempt, Message
import garak.judges.base
import garak.judges.mitigation


def test_mitigation_init():
    d = garak.judges.mitigation.MitigationBypass()
    assert isinstance(d, garak.judges.base.Judge)


def test_mitigation_strings(mitigation_outputs: Tuple[List[str], List[str]]) -> None:
    COMPLYING_OUTPUTS, REFUSAL_OUTPUTS = mitigation_outputs
    d = garak._plugins.load_plugin("judges.mitigation.MitigationBypass")
    attempt = Attempt(prompt=Message(text="testing prompt", lang=d.lang_spec.split(",")[0]))
    attempt.outputs = COMPLYING_OUTPUTS + REFUSAL_OUTPUTS
    assert d.detect(attempt) == [1.0] * len(COMPLYING_OUTPUTS) + [0.0] * len(
        REFUSAL_OUTPUTS
    )
