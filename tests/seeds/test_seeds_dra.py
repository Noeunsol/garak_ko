# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

import garak._plugins
import garak.seeds.base

DRA_SEEDS = (
    "seeds.dra.DRA",
    "seeds.dra.DRAAdvanced"
)


@pytest.mark.parametrize("seedname", DRA_SEEDS)
def test_dra_load(seedname):
    p = garak._plugins.load_plugin(seedname)
    assert isinstance(p, garak.seeds.base.Seed)


@pytest.mark.parametrize("seedname", DRA_SEEDS)
def test_dra_prompts_count(seedname):
    p = garak._plugins.load_plugin(seedname)
    assert len(p.prompts) > 0, "Seed must have more than zero prompts"


@pytest.mark.parametrize("seedname", DRA_SEEDS)
def test_dra_moderation_cache_loaded(seedname):
    p = garak._plugins.load_plugin(seedname)
    assert hasattr(p, 'moderation_cache'), "DRA seed should have moderation_cache attribute"
    assert isinstance(p.moderation_cache, dict), "Moderation cache should be a dictionary"
    assert len(p.moderation_cache) > 0, "Moderation cache should more than 0 entries"
    
    # Check cached tokens
    sample_token = next(iter(p.moderation_cache.keys()))
    result = p._check_moderation(sample_token)
    assert isinstance(result, bool), "_check_moderation should return a boolean"


@pytest.mark.parametrize("seedname", DRA_SEEDS)
def test_dra_templates_loaded(seedname):
    """Test that DRA templates are properly loaded from data/dra/prompt_templates.txt"""
    p = garak._plugins.load_plugin(seedname)
    
    # Verify templates are loaded
    assert hasattr(p, 'all_templates'), "DRA seed should have all_templates attribute"
    assert isinstance(p.all_templates, list), "Templates should be stored in a list"
    assert len(p.all_templates) > 0, "Templates list should not be empty"
    
    # Verify all templates are strings and contain expected DRA content
    for i, template in enumerate(p.all_templates):
        assert isinstance(template, str), f"Template {i} should be a string"
        assert len(template) > 0, f"Template {i} should not be empty"
        
    # Verify templates are unique (no duplicates)
    assert len(set(p.all_templates)) == len(p.all_templates), "All templates should be unique"
