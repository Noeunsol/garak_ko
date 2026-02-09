# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

from garak import _plugins

ATTACKERS = [
    classname
    for (classname, active) in _plugins.enumerate_plugins("attackers")
    if classname.startswith("attackers.paraphrase.")
]


@pytest.mark.parametrize("klassname", ATTACKERS)
def test_attacker_results(klassname):
    b = _plugins.load_plugin(klassname)
    b._load_model()
    paraphrases = b._get_response("The rain in Spain falls mainly in the plains.")
    assert len(paraphrases) > 0, "paraphrase attackers must return paraphrases"
    assert len(paraphrases) == len(
        set(paraphrases)
    ), "Paraphrases should not have dupes"
    assert not any([i == "" for i in paraphrases]), "No paraphrase may be empty"
