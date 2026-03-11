# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

import garak._plugins
from garak import _config
from garak._plugins import PluginProvider

import garak.seeds.base
import garak.attempt

CONTINUATION_SEEDS = (
    "seeds.continuation.ContinueSlursReclaimedSlursFull",
    "seeds.continuation.ContinueSlursReclaimedSlurs",
)


@pytest.fixture(autouse=True)
def restore_target_lang():
    original_target_lang = getattr(_config.run, "target_lang", "en")
    try:
        yield
    finally:
        _config.run.target_lang = original_target_lang
        PluginProvider.clear_cache()


def _load_seed(seedname):
    PluginProvider.clear_cache()
    return garak._plugins.load_plugin(seedname)


@pytest.mark.parametrize("seedname", CONTINUATION_SEEDS)
def test_continuation_load(seedname):
    p = _load_seed(seedname)
    assert isinstance(p, garak.seeds.base.Seed)


@pytest.mark.parametrize("seedname", CONTINUATION_SEEDS)
def test_continuation_counts_valid(seedname):
    p = _load_seed(seedname)
    assert len(p.prompts) > 0, "Seed must have more than zero prompts"

    if seedname.endswith("Full"):
        assert len(p.prompts) >= len(
            p._slur_prefixes
        ), "Seed should have at least one prompt per slur prefix"

    if seedname.endswith("Full"):
        assert len(p.prompts) == len(
            p.triggers
        ), "Prompt count and trigger count should match"
    else:
        assert len(p.prompts) <= len(
            p.triggers
        ), "Must be enough triggers for all the prompts"


@pytest.mark.parametrize("seedname", CONTINUATION_SEEDS)
def test_continuation_continuations_valid(seedname):
    p = _load_seed(seedname)

    for seq, prompt in enumerate(p.prompts):
        if not prompt.endswith(" "):

            trigger = p.triggers[seq]
            candidate_matches = [trigger[1:n] for n in range(len(trigger) - 1)]
            matched = False
            for candidate_match in candidate_matches:
                if prompt.endswith(candidate_match):
                    matched = True
            assert (
                matched == True
            ), "Prompts should end with starting substring of trigger"


def test_continuation_localization_ko():
    _config.run.target_lang = "ko"
    p = _load_seed("seeds.continuation.ContinueSlursReclaimedSlurs")
    assert p.lang == "ko"
    assert p._source_resource_path.name == "slurprompts_mini_ko.jsonl"


def test_continuation_localization_en():
    _config.run.target_lang = "en"
    p = _load_seed("seeds.continuation.ContinueSlursReclaimedSlurs")
    assert p.lang == "en"
    assert p._source_resource_path.name == "slurprompts_mini.jsonl"
