# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

from garak import _config
from garak import _plugins
import garak.targets.base
import garak.targets.nvcf

PLUGINS = ("NvcfChat", "NvcfCompletion")


@pytest.mark.parametrize("klassname", PLUGINS)
def test_instantiate(klassname):
    _config.plugins.targets["nvcf"] = {}
    _config.plugins.targets["nvcf"][klassname] = {}
    _config.plugins.targets["nvcf"][klassname]["name"] = "placeholder name"
    _config.plugins.targets["nvcf"][klassname]["api_key"] = "placeholder key"
    g = _plugins.load_plugin(f"targets.nvcf.{klassname}")
    assert isinstance(g, garak.targets.base.Target)


@pytest.mark.parametrize("klassname", PLUGINS)
def test_version_endpoint(klassname):
    name = "feedfacedeadbeef"
    version = "cafebabe"
    _config.plugins.targets["nvcf"] = {}
    _config.plugins.targets["nvcf"][klassname] = {}
    _config.plugins.targets["nvcf"][klassname]["name"] = name
    _config.plugins.targets["nvcf"][klassname]["api_key"] = "placeholder key"
    _config.plugins.targets["nvcf"][klassname]["version_id"] = version
    g = _plugins.load_plugin(f"targets.nvcf.{klassname}")
    assert g.invoke_uri == f"{g.invoke_uri_base}{name}/versions/{version}"


@pytest.mark.parametrize("klassname", PLUGINS)
def test_custom_keys(klassname):
    from garak.attempt import Message, Turn, Conversation

    name = "feedfacedeadbeef"
    params = {"n": 1, "model": "secret/model_1.8t"}
    _config.plugins.targets["nvcf"] = {}
    _config.plugins.targets["nvcf"][klassname] = {}
    _config.plugins.targets["nvcf"][klassname]["name"] = name
    _config.plugins.targets["nvcf"][klassname]["api_key"] = "placeholder key"
    _config.plugins.targets["nvcf"][klassname]["extra_params"] = params
    g = _plugins.load_plugin(f"targets.nvcf.{klassname}")
    conv = Conversation([Turn("user", Message("whatever prompt"))])
    test_payload = g._build_payload(conv)
    for k, v in params.items():
        assert test_payload[k] == v
