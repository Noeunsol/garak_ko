# SPDX-FileCopyrightText: Portions Copyright (c) 2026
# SPDX-License-Identifier: Apache-2.0

import garak.attempt
from garak.attackers import paraphrase


def _mk_attempt(text: str = "hello", lang: str = "en") -> garak.attempt.Attempt:
    conv = garak.attempt.Conversation(
        [garak.attempt.Turn("user", garak.attempt.Message(text=text, lang=lang))]
    )
    return garak.attempt.Attempt(prompt=conv, seed_classname="garak.seeds.test.Dummy")


def test_paraphrase_fast_sets_prompt_as_conversation(mocker):
    attacker = paraphrase.Fast()
    attacker.enable_translation_bridge = False
    mocker.patch.object(attacker, "_get_response", return_value=["hi there"])

    attempt = _mk_attempt()
    out_attempts = list(attacker.transform(attempt))
    assert len(out_attempts) >= 2  # includes unmodified copy + paraphrases

    for out in out_attempts:
        assert isinstance(out.prompt, garak.attempt.Conversation)
        assert isinstance(out.prompt.last_message(), garak.attempt.Message)


def test_paraphrase_pegasust5_sets_prompt_as_conversation(mocker):
    attacker = paraphrase.PegasusT5()
    attacker.enable_translation_bridge = False
    mocker.patch.object(attacker, "_get_response", return_value=["hi there"])

    attempt = _mk_attempt()
    out_attempts = list(attacker.transform(attempt))
    assert len(out_attempts) >= 2

    for out in out_attempts:
        assert isinstance(out.prompt, garak.attempt.Conversation)
        assert isinstance(out.prompt.last_message(), garak.attempt.Message)

