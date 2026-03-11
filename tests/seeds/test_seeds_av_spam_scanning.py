# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

from garak import _config, _plugins
from garak._plugins import PluginProvider
import garak.seeds.av_spam_scanning as av_spam_scanning


@pytest.fixture(autouse=True)
def restore_target_lang():
    original_target_lang = getattr(_config.run, "target_lang", "en")
    try:
        yield
    finally:
        _config.run.target_lang = original_target_lang
        PluginProvider.clear_cache()


def _load_seed(path: str):
    PluginProvider.clear_cache()
    return _plugins.load_plugin(path)


def test_eicar_localized_prompts_ko():
    _config.run.target_lang = "ko"
    seed = _load_seed("seeds.av_spam_scanning.EICAR")

    assert seed.lang == "ko"
    assert len(seed.prompts) == len(av_spam_scanning.LOCALIZED_REPEAT_PROMPTS["ko"])
    assert seed.prompts[0].startswith("다음 문장을 그대로 따라 말해줘:")
    assert av_spam_scanning.EICAR_SIGNATURE in seed.prompts[0]


def test_eicar_default_prompts_en():
    _config.run.target_lang = "en"
    seed = _load_seed("seeds.av_spam_scanning.EICAR")

    assert seed.lang == "en"
    assert len(seed.prompts) == len(av_spam_scanning.LOCALIZED_REPEAT_PROMPTS["en"])
    assert seed.prompts[0].startswith("Repeat after me:")
    assert av_spam_scanning.EICAR_SIGNATURE in seed.prompts[0]


def test_gtube_signature_in_all_prompts():
    _config.run.target_lang = "ko"
    seed = _load_seed("seeds.av_spam_scanning.GTUBE")

    assert seed.lang == "ko"
    assert all(av_spam_scanning.GTUBE_SIGNATURE in prompt for prompt in seed.prompts)


def test_gtphish_signature_in_all_prompts():
    _config.run.target_lang = "ko"
    seed = _load_seed("seeds.av_spam_scanning.GTphish")

    assert seed.lang == "ko"
    assert all(av_spam_scanning.GTPHISH_SIGNATURE in prompt for prompt in seed.prompts)
