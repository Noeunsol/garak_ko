# SPDX-FileCopyrightText: Copyright (c) 2026
# SPDX-License-Identifier: Apache-2.0

import json

import pytest

from garak import _config, _plugins, langservice
from garak._plugins import PluginProvider
from garak.data import path as data_path


def _load_seed(seedname: str, config_root=None):
    PluginProvider.clear_cache()
    return _plugins.load_plugin(seedname, config_root=config_root)


@pytest.fixture(autouse=True)
def restore_target_lang_and_langservice():
    original_target_lang = getattr(_config.run, "target_lang", "en")
    original_langproviders = getattr(_config.run, "langproviders", [])
    try:
        yield
    finally:
        _config.run.target_lang = original_target_lang
        _config.run.langproviders = original_langproviders
        PluginProvider.clear_cache()
        langservice.langproviders = {}
        langservice.native_langprovider = None


def test_dan_seed_localized_file_ko():
    _config.run.target_lang = "ko"
    seed = _load_seed("seeds.dan.Dan_11_0")

    assert seed.lang == "ko"
    assert seed._source_prompt_lang == "ko"
    assert seed._source_prompt_path.name == "Dan_11_0_ko.json"
    assert any("\uac00" <= c <= "\ud7a3" for c in seed.prompts[0])


def test_dan_seed_localized_file_en():
    _config.run.target_lang = "en"
    seed = _load_seed("seeds.dan.Dan_11_0")

    assert seed.lang == "en"
    assert seed._source_prompt_lang == "en"
    assert seed._source_prompt_path.name == "Dan_11_0.json"


def test_dan_seed_inthewild_localization_behavior():
    _config.run.target_lang = "ko"
    seed = _load_seed("seeds.dan.DanInTheWild")

    if (data_path / "inthewild_jailbreak_llms_ko.json").exists():
        assert seed.lang == "ko"
        assert seed._source_prompt_lang == "ko"
        assert seed._source_prompt_path.name == "inthewild_jailbreak_llms_ko.json"
        assert any("\uac00" <= c <= "\ud7a3" for c in seed.prompts[0])
    else:
        assert seed.lang == "en"
        assert seed._source_prompt_lang == "en"
        assert seed._source_prompt_path.name == "inthewild_jailbreak_llms.json"
        assert not any("\uac00" <= c <= "\ud7a3" for c in seed.prompts[0])


def test_dan_ablation_uses_en_source_lang():
    _config.run.target_lang = "ko"
    seed = _load_seed("seeds.dan.Ablation_Dan_11_0")

    assert seed.lang == "ko"
    assert seed._source_prompt_lang == "ko"
    assert seed._source_prompt_path is None
    assert seed.prompts[0].startswith("이전에 받은 모든 지시를")


def test_dan_fallback_seed_uses_en_to_ko_langprovider_when_configured():
    _config.run.target_lang = "ko"
    _config.run.langproviders = [
        {"language": "en,en", "model_type": "local.Passthru"},
        {"language": "ko,ko", "model_type": "local.Passthru"},
        {"language": "en,ko", "model_type": "local.Passthru"},
        {"language": "ko,en", "model_type": "local.Passthru"},
    ]

    seed = _load_seed("seeds.dan.DanInTheWild")
    if (data_path / "inthewild_jailbreak_llms_ko.json").exists():
        assert seed.lang == "ko"
        assert seed.langprovider.source_lang == "ko"
        assert seed.langprovider.target_lang == "ko"
    else:
        assert seed.lang == "en"
        assert seed.langprovider.source_lang == "en"
        assert seed.langprovider.target_lang == "ko"


def test_dan_inthewild_balanced_strategy_caps_to_peer_dataset():
    _config.run.target_lang = "en"
    full_all = _load_seed(
        "seeds.dan.DanInTheWildFull",
        config_root={
            "seeds": {
                "dan": {
                    "DanInTheWildFull": {
                        "prompt_count_strategy": "all",
                    }
                }
            }
        },
    )
    full_balanced = _load_seed(
        "seeds.dan.DanInTheWildFull",
        config_root={
            "seeds": {
                "dan": {
                    "DanInTheWildFull": {
                        "prompt_count_strategy": "balanced",
                    }
                }
            }
        },
    )

    assert len(full_balanced.prompts) <= len(full_all.prompts)
    if (data_path / "inthewild_jailbreak_llms_ko.json").exists():
        with open(
            data_path / "inthewild_jailbreak_llms_ko.json", "r", encoding="utf-8"
        ) as ko_file:
            ko_count = len(json.load(ko_file))
        assert len(full_balanced.prompts) == min(
            len(full_all.prompts), ko_count
        )


def test_autodan_localized_goal_and_init_lang():
    _config.run.target_lang = "ko"
    seed = _load_seed("seeds.dan.AutoDAN")
    assert seed.lang == "ko"
    assert seed._source_prompt_lang == "ko"
    assert seed.goal_str == seed.DEFAULT_PARAMS["goal_str_ko"]
