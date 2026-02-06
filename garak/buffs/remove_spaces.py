# SPDX-FileCopyrightText: Copyright (c) 2026
# SPDX-License-Identifier: Apache-2.0

"""Buff that strips all whitespace from the prompt (useful for Korean-space variants)."""

from collections.abc import Iterable

import garak.attempt
from garak.buffs.base import Buff


class RemoveSpaces(Buff):
    """Remove all whitespace characters from the last user message."""

    lang = None  # works for any language; intended for ko

    def transform(
        self, attempt: garak.attempt.Attempt
    ) -> Iterable[garak.attempt.Attempt]:
        last_message = attempt.prompt.last_message()
        delattr(attempt, "_prompt")  # allow prompt reset
        stripped = "".join(last_message.text.split())
        attempt.prompt = garak.attempt.Message(text=stripped, lang=last_message.lang)
        yield attempt
