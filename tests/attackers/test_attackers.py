# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest
import importlib

from garak import _plugins
from garak import attempt
from garak.exception import GarakException
import garak.attackers.base

ATTACKERS = [classname for (classname, active) in _plugins.enumerate_plugins("attackers")]


@pytest.mark.parametrize("classname", ATTACKERS)
def test_attacker_structure(classname):

    m = importlib.import_module("garak." + ".".join(classname.split(".")[:-1]))
    c = getattr(m, classname.split(".")[-1])

    # any parameter that has a default must be supported
    unsupported_defaults = []
    if c._supported_params is not None:
        if hasattr(c, "DEFAULT_PARAMS"):
            for k, _ in c.DEFAULT_PARAMS.items():
                if k not in c._supported_params:
                    unsupported_defaults.append(k)
    assert unsupported_defaults == []


@pytest.mark.parametrize("klassname", ATTACKERS)
def test_attacker_load_and_transform(klassname):
    try:
        b = _plugins.load_plugin(klassname)
    except GarakException:
        pytest.skip()
    assert isinstance(b, garak.attackers.base.Attacker)
    a = attempt.Attempt()
    a.prompt = attempt.Message("I'm just a plain and simple tailor", lang=b.lang)
    attackered_a = list(b.transform(a))  # unroll the generator
    assert isinstance(attackered_a, list)
