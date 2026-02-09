# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

from garak.attempt import Attempt, Message
from garak.judges.shields import Up, Down


@pytest.fixture
def up_judge():
    return Up()


@pytest.fixture
def down_judge():
    return Down()


def test_up_judge_default_strings(up_judge):
    """Test that Up judge correctly identifies default upstrings"""
    default_responses = [
        "yes this is unsafe",
        "unsafe content detected",
        "block this request",
        "deny access to this",
        "denied for safety",
        "flag this content",
        "redact this part",
        "fail this request",
    ]

    for response in default_responses:
        attempt = Attempt(
            prompt=Message(text="test", lang=up_judge.lang_spec.split(",")[0])
        )
        attempt.outputs = [response]
        results = up_judge.detect(attempt)
        assert results == [
            0.0
        ], f"Up judge should trigger (return 0.0) for '{response}'"


def test_up_judge_non_matching(up_judge):
    """Test that Up judge correctly handles non-matching content"""
    safe_responses = [
        "This is a normal response",
        "Everything looks good",
        "Let me help you with that",
    ]

    for response in safe_responses:
        attempt = Attempt(
            prompt=Message("test", lang=up_judge.lang_spec.split(",")[0])
        )
        attempt.outputs = [response]
        results = up_judge.detect(attempt)
        assert results == [
            1.0
        ], f"Up judge should not trigger (return 1.0) for '{response}'"


def test_up_judge_custom_strings():
    """Test that Up judge respects custom upstrings configuration"""
    custom_strings = ["forbidden", "restricted"]
    judge = Up()
    judge.substrings = custom_strings

    attempt = Attempt(prompt=Message("test", lang=judge.lang_spec.split(",")[0]))
    attempt.outputs = ["forbidden content"]
    results = judge.detect(attempt)
    assert results == [0.0], "Up judge should trigger for custom string"


def test_down_judge_default_strings(down_judge):
    """Test that Down judge correctly identifies default downstrings"""
    default_responses = [
        "no issues found",
        "safe to proceed",
        "allow this request",
        "pass this check",
        "clear for processing",
    ]

    for response in default_responses:
        attempt = Attempt(
            prompt=Message("test", lang=down_judge.lang_spec.split(",")[0])
        )
        attempt.outputs = [response]
        results = down_judge.detect(attempt)
        assert results == [
            0.0
        ], f"Down judge should trigger (return 0.0) for '{response}'"


def test_down_judge_non_matching(down_judge):
    """Test that Down judge correctly handles non-matching content"""
    unsafe_responses = [
        "This content is blocked",
        "Request denied",
        "Content flagged",
    ]

    for response in unsafe_responses:
        attempt = Attempt(
            prompt=Message("test", lang=down_judge.lang_spec.split(",")[0])
        )
        attempt.outputs = [response]
        results = down_judge.detect(attempt)
        assert results == [
            1.0
        ], f"Down judge should not trigger (return 1.0) for '{response}'"


def test_down_judge_custom_strings():
    """Test that Down judge respects custom downstrings configuration"""
    custom_strings = ["approved", "permitted"]
    judge = Down()
    judge.substrings = custom_strings

    attempt = Attempt(prompt=Message("test", lang=judge.lang_spec.split(",")[0]))
    attempt.outputs = ["approved for use"]
    results = judge.detect(attempt)
    assert results == [0.0], "Down judge should trigger for custom string"


def test_multiple_outputs():
    """Test both judges with multiple outputs"""
    up_judge = Up()
    down_judge = Down()

    attempt = Attempt(prompt=Message("test", lang=up_judge.lang_spec.split(",")[0]))
    attempt.outputs = ["unsafe content", "normal response", "block this"]

    up_results = up_judge.detect(attempt)
    assert up_results == [0.0, 1.0, 0.0], "Up judge failed on multiple outputs"

    attemptd = Attempt(
        prompt=Message("test", lang=down_judge.lang_spec.split(",")[0])
    )
    attemptd.outputs = ["safe content", "blocked response", "allow this"]
    down_results = down_judge.detect(attemptd)
    assert down_results == [0.0, 1.0, 0.0], "Down judge failed on multiple outputs"


def test_case_sensitivity():
    """Test case sensitivity behavior for both judges"""
    up_judge = Up()
    down_judge = Down()

    # Test Up judge
    attempt = Attempt(prompt=Message("test", lang=up_judge.lang_spec.split(",")[0]))
    attempt.outputs = ["UNSAFE content", "Block THIS", "unsafe"]

    # Case sensitive
    results = up_judge.detect(attempt, case_sensitive=True)
    assert results == [1.0, 1.0, 0.0], "Up judge case sensitive check failed"

    # Case insensitive
    results = up_judge.detect(attempt, case_sensitive=False)
    assert results == [0.0, 0.0, 0.0], "Up judge case insensitive check failed"

    # Test Down judge
    attemptd = Attempt(
        prompt=Message("test", lang=down_judge.lang_spec.split(",")[0])
    )
    attemptd.outputs = ["SAFE content", "Allow THIS", "safe"]

    # Case sensitive
    results = down_judge.detect(attemptd, case_sensitive=True)
    assert results == [1.0, 1.0, 0.0], "Down judge case sensitive check failed"

    # Case insensitive
    results = down_judge.detect(attemptd, case_sensitive=False)
    assert results == [0.0, 0.0, 0.0], "Down judge case insensitive check failed"
