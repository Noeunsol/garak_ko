# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

import garak._plugins

import garak.seeds.base
import garak.attempt

CONTINUATION_SEEDS = (
    "seeds.continuation.ContinueSlursReclaimedSlursFull",
    "seeds.continuation.ContinueSlursReclaimedSlurs",
)


@pytest.mark.parametrize("seedname", CONTINUATION_SEEDS)
def test_continuation_load(seedname):
    p = garak._plugins.load_plugin(seedname)
    assert isinstance(p, garak.seeds.base.Seed)


@pytest.mark.parametrize("seedname", CONTINUATION_SEEDS)
def test_continuation_counts_valid(seedname):
    p = garak._plugins.load_plugin(seedname)
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
    p = garak._plugins.load_plugin(seedname)

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
