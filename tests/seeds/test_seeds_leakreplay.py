# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import inspect
import pytest

import garak
import garak._config
import garak._plugins
import garak.attempt
import garak.cli
import garak.seeds.leakreplay


def test_leakreplay_hitlog():

    args = "-m test.Blank -p leakreplay -d always.Fail".split()
    garak.cli.main(args)


def test_leakreplay_output_count():
    generations = 1
    garak._config.load_base_config()
    garak._config.transient.reportfile = open(os.devnull, "w+", encoding="utf-8")
    garak._config.plugins.seeds["leakreplay"]["generations"] = generations
    a = garak.attempt.Attempt(prompt=garak.attempt.Message("test"))
    p = garak._plugins.load_plugin(
        "seeds.leakreplay.LiteratureCloze", config_root=garak._config
    )
    g = garak._plugins.load_plugin("targets.test.Blank", config_root=garak._config)
    p.target = g
    results = p._execute_all([a])
    assert len(a.outputs) == generations


def test_leakreplay_handle_incomplete_attempt():
    p = garak.seeds.leakreplay.LiteratureCloze()
    a = garak.attempt.Attempt(prompt=garak.attempt.Message("IS THIS BROKEN"))
    a.outputs = [garak.attempt.Message(s) for s in ["", None]]
    p._postprocess_hook(a)


def test_leakreplay_module_structure():
    # Get all seed classes from leakreplay module
    leakreplay_classes = []
    for name, obj in inspect.getmembers(garak.seeds.leakreplay):
        if (
            inspect.isclass(obj)
            and obj.__module__ == "garak.seeds.leakreplay"
            and not name.endswith("Mixin")  # Skip mixin classes
            and issubclass(obj, garak.seeds.Seed)
        ):
            leakreplay_classes.append(obj)
            assert (
                "Cloze" in name or "Complete" in name
            ), f"Leakreplay seed class {name} does not bear 'Cloze' or 'Complete'"

    # Test that we found at least 8 classes (there should be more)
    assert len(leakreplay_classes) >= 8, "Not all leakreplay seed classes were found"


LEAKREPLAY_SEEDS = [
    classname
    for (classname, active) in garak._plugins.enumerate_plugins("seeds")
    if classname.startswith("seeds.leakreplay")
]


@pytest.mark.parametrize("klassname", LEAKREPLAY_SEEDS)
def test_leakreplay_seed_structure(klassname):
    """Test that all leakreplay seed classes can be instantiated and function correctly.

    This test verifies:
    1. All seed classes can be instantiated without errors
    2. The string replacement works properly (with special characters like %)
    3. Tag inheritance works correctly from parent classes
    """

    # Test tag inheritance - check that all expected tags are inherited properly
    expected_tags = [
        "avid-effect:security:S0301",
        "owasp:llm10",
        "owasp:llm06",
        "quality:Security:ExtractionInversion",
        "payload:leak:training",
    ]
    expected_tag_count = len(expected_tags)

    seed_class = getattr(garak.seeds.leakreplay, klassname)

    # Also verify the tag count & content to ensure no duplicates or extras
    if seed_class.__name__.endswith(
        ("Cloze", "ClozeFull", "Complete", "CompleteFull")
    ):
        assert (
            len(seed_class.tags) >= expected_tag_count
        ), f"incorrect number of tags: {len(seed_class.tags)} instead of >= {expected_tag_count}"
        for tag in expected_tags:
            assert tag in seed_class.tags, f"missing expected tag: {tag}"

    # instance checks
    seed = None
    try:
        # Should initialize without errors
        seed = garak._plugins.load_plugin(klassname)

        # Verify that prompts were created correctly (this tests the string replacement)
        assert len(seed.prompts) > 0, "no prompts"

        assert len(seed.prompts) == len(
            seed.triggers
        ), "mismatch between prompt and trigger count"

        # Test template handling (specific to our string replacement fix)
        if hasattr(seed, "_attempt_prestore_hook"):
            # Create an attempt with a prompt containing % characters
            # This would fail if we were using % string formatting
            special_prompt = "Test with 100% special % characters"
            a = garak.attempt.Attempt(prompt=garak.attempt.Message(special_prompt))

            # Should not raise errors when % is in the prompt
            seed._attempt_prestore_hook(a, 0)

    except Exception as e:
        assert False, f"Failed to initialize {seed_class.__name__}: {e}"


CLOZE_SEEDS = [
    classname
    for (classname, active) in garak._plugins.enumerate_plugins("seeds")
    if classname.startswith("seeds.leakreplay") and "Cloze" in classname
]


@pytest.mark.parametrize("klassname", CLOZE_SEEDS)
def test_leakreplay_seed_structure(klassname):
    seed = garak._plugins.load_plugin(klassname)

    for prompt in seed.prompts:
        assert (
            "%s" not in prompt
        ), "still has passage replacement marker %s in prompt, '{prompt}'"
        assert "[MASK]" in prompt, "missing [MASK] in prompt, '{prompt}'"

    assert hasattr(seed, "_postprocess_hook"), "Cloze seed missing _postprocess_hook"
    test_attempt = garak.attempt.Attempt(prompt=garak.attempt.Message("test"))
    test_attempt.outputs = [garak.attempt.Message("<name>Test</name>")]
    processed = seed._postprocess_hook(test_attempt)
    # Check that name tags are properly removed (part of postprocessing)
    assert "<name>" not in processed.conversations[0].turns[-1].content.text
