# SPDX-FileCopyrightText: Copyright (c) 2026
# SPDX-License-Identifier: Apache-2.0

"""Shared runtime helpers for target language and run seed behavior."""

import random
from typing import Any

from garak import _config


def get_target_lang(default: str | None = None) -> str | None:
    """Read run.target_lang with whitespace normalization."""
    target_lang = getattr(_config.run, "target_lang", default)
    if not isinstance(target_lang, str):
        return default
    normalized = target_lang.strip()
    return normalized or default


def normalize_lang_code(lang: str | None) -> str | None:
    """Normalize BCP47-ish language code to a lowercase base tag."""
    if not isinstance(lang, str):
        return None
    normalized = lang.strip().lower()
    if not normalized:
        return None
    return normalized.split("-", 1)[0]


def is_lang_ko(lang: str | None) -> bool:
    """Return True for Korean language codes (ko, ko-KR, ...)."""
    return normalize_lang_code(lang) == "ko"


def is_target_lang_ko() -> bool:
    """Return True when run.target_lang is Korean."""
    return is_lang_ko(get_target_lang())


def seed_python_random_from_run_seed() -> Any | None:
    """Seed python's random module from run.seed when configured."""
    run_seed = getattr(_config.run, "seed", None)
    if run_seed is None:
        return None
    random.seed(run_seed)
    return run_seed
