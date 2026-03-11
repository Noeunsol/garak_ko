# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

from garak import _config, _plugins
import garak.resources.ansi
import garak.seeds.ansiescape as ansiescape


@pytest.fixture(autouse=True)
def restore_target_lang():
    original_target_lang = getattr(_config.run, "target_lang", "en")
    try:
        yield
    finally:
        _config.run.target_lang = original_target_lang


def test_ansiescaped_localized_prompts_ko():
    _config.run.target_lang = "ko"
    seed = _plugins.load_plugin("seeds.ansiescape.AnsiEscaped")

    parts = ansiescape.LOCALIZED_PROMPT_PARTS["ko"]
    expected_count = len(parts["asks"]) * len(parts["tasks"]) + len(
        parts["repeat_stubs"]
    ) * len(garak.resources.ansi.ESCAPED_PAYLOADS)

    assert seed.lang == "ko"
    assert len(seed.prompts) == expected_count
    assert any("터미널 ANSI 코드로" in prompt for prompt in seed.prompts)
    assert any("다음을 출력해:" in prompt for prompt in seed.prompts)


def test_ansiraw_localized_prompts_ko():
    _config.run.target_lang = "ko"
    seed = _plugins.load_plugin("seeds.ansiescape.AnsiRaw")

    parts = ansiescape.LOCALIZED_PROMPT_PARTS["ko"]
    expected_count = (
        len(parts["asks"]) * len(parts["tasks"])
        + len(parts["repeat_stubs"]) * len(garak.resources.ansi.LIVE_PAYLOADS)
        + len(parts["unescape_stubs"]) * len(garak.resources.ansi.ESCAPED_PAYLOADS)
    )

    assert seed.lang == "ko"
    assert len(seed.prompts) == expected_count
    assert any("raw bytes로 디코드해:" in prompt for prompt in seed.prompts)


def test_ansiescaped_default_prompts_en():
    _config.run.target_lang = "en"
    seed = _plugins.load_plugin("seeds.ansiescape.AnsiEscaped")

    assert seed.lang == "en"
    assert any("What's terminal ANSI code to" in prompt for prompt in seed.prompts)
