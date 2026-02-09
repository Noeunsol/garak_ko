# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

from garak.attempt import Attempt, Message
import garak._plugins
import garak.judges.base

ALWAYS_JUDGE_NAMES = [
    classname
    for (classname, active) in garak._plugins.enumerate_plugins("judges")
    if ".always." in classname
]


@pytest.mark.parametrize("judgename", ALWAYS_JUDGE_NAMES)
def test_load(judgename):
    d = garak._plugins.load_plugin(judgename)
    assert isinstance(d, garak.judges.base.Judge)


def test_fail():
    d = garak._plugins.load_plugin("judges.always.Fail")
    a = Attempt(prompt=Message())
    a.outputs = [""]
    d.detect(a)
    assert d.detect(a) == [1.0]


def test_pass():
    d = garak._plugins.load_plugin("judges.always.Pass")
    a = Attempt(prompt=Message())
    a.outputs = [""]
    assert d.detect(a) == [0.0]


def test_passthru():
    d = garak._plugins.load_plugin("judges.always.Passthru")
    a = Attempt(prompt=Message())
    a.outputs = [""]
    a.judge_results = {"always.Fail": [0.5]}
    assert d.detect(a) == [0.5]
