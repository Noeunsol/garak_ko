# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from garak import attempt
from garak.attackers import encoding


def test_encoding_attacker_base64_ko_message():
    a = attempt.Attempt()
    a.prompt = attempt.Message("테스트", lang="ko")
    b = encoding.Base64()
    out = list(b.transform(a))
    assert len(out) == 1
    assert out[0].prompt.last_message().lang == "ko"
    assert out[0].prompt.last_message().text.startswith("다음 지시문은 base64로 인코딩되어 있습니다:")


def test_encoding_attacker_charcode_ko_message():
    a = attempt.Attempt()
    a.prompt = attempt.Message("테스트", lang="ko")
    b = encoding.CharCode()
    out = list(b.transform(a))
    assert len(out) == 1
    assert out[0].prompt.last_message().lang == "ko"
    assert out[0].prompt.last_message().text.startswith("다음 지시문은 CharCode로 인코딩되어 있습니다:")

