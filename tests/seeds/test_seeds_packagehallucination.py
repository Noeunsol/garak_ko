# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib
import pytest
from garak import _plugins
import garak.seeds.packagehallucination

SEEDS = [
    classname
    for (classname, active) in _plugins.enumerate_plugins("seeds")
    if classname.startswith("seeds.packagehallucination")
]


@pytest.fixture(autouse=True)
def reload_config(request):
    # reload config before and after each test
    def reload():
        importlib.reload(garak._config)

    reload()
    request.addfinalizer(reload)


@pytest.mark.parametrize("classname", SEEDS)
def test_soft_promptcount(classname):
    language_seed = _plugins.load_plugin(classname)

    expected_count = garak._config.run.soft_seed_prompt_cap

    assert (
        len(language_seed.prompts) == expected_count
    ), f"{language_seed.__name__} prompt count mismatch. Expected {expected_count}, got {len(language_seed.prompts)}"


@pytest.mark.parametrize("classname", SEEDS)
def test_full_promptcount(classname):
    garak._config.run.soft_seed_prompt_cap = float("inf")

    language_seed = _plugins.load_plugin(classname)

    expected_count = len(garak.seeds.packagehallucination.stub_prompts) * len(
        garak.seeds.packagehallucination.code_tasks
    )

    assert (
        len(language_seed.prompts) == expected_count
    ), f"{language_seed.__name__} prompt count mismatch. Expected {expected_count}, got {len(language_seed.prompts)}"
