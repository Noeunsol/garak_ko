# SPDX-FileCopyrightText: Copyright (c) 2026
# SPDX-License-Identifier: Apache-2.0

"""Shared OpenAI translation helpers for attackers."""

import os

from openai import OpenAI

DEFAULT_TRANSLATION_SYSTEM_PROMPT = (
    "You are a precise translation engine. Return only the translated text."
)


def get_openai_client(
    api_key: str | None,
    *,
    env_var: str = "OPENAI_API_KEY",
    error_context: str,
) -> tuple[OpenAI, str]:
    """Create an OpenAI client with a consistent API-key lookup policy."""
    resolved_api_key = api_key or os.getenv(env_var)
    if not resolved_api_key:
        raise ValueError(f"{env_var} not set; required for {error_context}.")
    return OpenAI(api_key=resolved_api_key), resolved_api_key


def translate_with_openai(
    *,
    client: OpenAI,
    text: str,
    target_lang: str,
    model_name: str,
    temperature: float,
    system_prompt: str = DEFAULT_TRANSLATION_SYSTEM_PROMPT,
    user_prompt_template: str = "Translate into {target_lang}: {text}",
) -> str:
    """Translate text with a chat-completions request."""
    resp = client.chat.completions.create(
        model=model_name,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": user_prompt_template.format(
                    target_lang=target_lang, text=text
                ),
            },
        ],
    )
    return (resp.choices[0].message.content or "").strip()


def is_korean_text(text: str) -> bool:
    """Return True when text contains Hangul syllables."""
    return any("\uac00" <= ch <= "\ud7a3" for ch in text)


def is_korean_lang(lang: str | None) -> bool:
    """Return True when language code starts with 'ko'."""
    return (lang or "").lower().startswith("ko")
