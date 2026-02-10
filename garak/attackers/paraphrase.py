# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Attacker that paraphrases a prompt."""

from collections.abc import Iterable

import garak.attempt
from garak import _config
from garak.attackers.base import Attacker
from garak.resources.api.huggingface import HFCompatible
import os
from openai import OpenAI


class PegasusT5(Attacker, HFCompatible):
    """Paraphrasing attacker using Pegasus model"""

    DEFAULT_PARAMS = Attacker.DEFAULT_PARAMS | {
        "para_model_name": "garak-llm/pegasus_paraphrase",
        "hf_args": {
            "device": "cpu",
            "trust_remote_code": False,
        },  # torch_dtype doesn't have standard support in Pegasus
        "max_length": 60,
        "temperature": 1.5,
        # translation bridge for non-English inputs
        "enable_translation_bridge": True,
        "translation_model_name": "gpt-4o-mini",
        "translation_temperature": 0.3,
    }
    lang = None  # allow all languages; non-en can route through bridge
    doc_uri = "https://huggingface.co/tuner007/pegasus_paraphrase"

    def __init__(self, config_root=_config) -> None:
        self.num_return_sequences = 6
        self.num_beams = self.num_return_sequences
        self.tokenizer = None
        self.para_model = None
        self._oa_client = None
        super().__init__(config_root=config_root)

    def _require_openai_client(self):
        if self._oa_client is None:
            api_key = getattr(self, "api_key", None) or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY not set; required for translation bridge in PegasusT5."
                )
            self._oa_client = OpenAI(api_key=api_key)

    def _translate(self, text: str, target_lang: str) -> str:
        self._require_openai_client()
        resp = self._oa_client.chat.completions.create(
            model=self.translation_model_name,
            temperature=self.translation_temperature,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise translation engine. "
                        "Return only the translated text."
                    ),
                },
                {"role": "user", "content": f"Translate into {target_lang}: {text}"},
            ],
        )
        return resp.choices[0].message.content.strip()

    def _load_model(self):
        from transformers import PegasusForConditionalGeneration, PegasusTokenizer

        self.device = self._select_hf_device()
        self.para_model = PegasusForConditionalGeneration.from_pretrained(
            self.para_model_name
        ).to(self.device)
        self.tokenizer = PegasusTokenizer.from_pretrained(
            self.para_model_name, trust_remote_code=self.hf_args["trust_remote_code"]
        )

    def _get_response(self, input_text):
        if self.para_model is None:
            self._load_model()

        batch = self.tokenizer(
            [input_text],
            truncation=True,
            padding="longest",
            max_length=self.max_length,
            return_tensors="pt",
        ).to(self.device)
        translated = self.para_model.generate(
            **batch,
            max_length=self.max_length,
            num_beams=self.num_beams,
            num_return_sequences=self.num_return_sequences,
            temperature=self.temperature,
        )
        tgt_text = self.tokenizer.batch_decode(translated, skip_special_tokens=True)
        return tgt_text

    def _is_korean(self, text: str) -> bool:
        return any("\uac00" <= ch <= "\ud7a3" for ch in text)

    def _should_bridge(self, source_lang: str, text: str) -> bool:
        if not source_lang or source_lang == "*" or source_lang.lower() == "unknown":
            return self._is_korean(text)
        return not source_lang.lower().startswith("en")

    def transform(
        self, attempt: garak.attempt.Attempt
    ) -> Iterable[garak.attempt.Attempt]:
        yield self._derive_new_attempt(
            attempt
        )  # why does this yield a copy of the original with no modification?
        last_message = attempt.prompt.last_message()
        source_lang = last_message.lang or ""
        input_text = last_message.text

        used_bridge = False
        if self.enable_translation_bridge and self._should_bridge(source_lang, input_text):
            try:
                input_text = self._translate(input_text, target_lang="English")
                used_bridge = True
            except Exception:
                pass  # fall back to original text if translation fails

        paraphrases = self._get_response(input_text)
        for paraphrase in set(paraphrases):
            if used_bridge:
                try:
                    paraphrase = self._translate(
                        paraphrase, target_lang=source_lang or "Korean"
                    )
                except Exception:
                    paraphrase = last_message.text  # ensure output stays in source language
            paraphrased_attempt = self._derive_new_attempt(attempt)
            # transform receives a copy of the attempt should it modify the prompt in place?
            delattr(paraphrased_attempt, "_prompt")  # hack to allow prompt set
            # Attempt.prompt is a Conversation; set via the property so the attempt stays consistent.
            paraphrased_attempt.prompt = garak.attempt.Message(
                text=paraphrase, lang=last_message.lang
            )
            yield paraphrased_attempt


class OpenAIParaphrase(Attacker):
    """OpenAI-based paraphraser (multilingual, works well for Korean)"""

    ENV_VAR = "OPENAI_API_KEY"
    DEFAULT_PARAMS = Attacker.DEFAULT_PARAMS | {
        "model_name": "gpt-4o-mini",
        "temperature": 0.7,
        "num_return_sequences": 3,
    }
    doc_uri = "https://platform.openai.com/docs/guides/text-generation"
    lang = None  # allow all languages

    def __init__(self, config_root=_config) -> None:
        self.client = None
        super().__init__(config_root=config_root)

    def _require_client(self):
        if self.client is None:
            api_key = getattr(self, "api_key", None) or os.getenv(self.ENV_VAR)
            if not api_key:
                raise ValueError(f"{self.ENV_VAR} not set; cannot run OpenAIParaphrase.")
            self.api_key = api_key
            self.client = OpenAI(api_key=api_key)

    def _paraphrases(self, text: str):
        self._require_client()
        resp = self.client.chat.completions.create(
            model=self.model_name,
            n=self.num_return_sequences,
            temperature=self.temperature,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a paraphrasing engine. Rewrite the user's sentence "
                        "with the same meaning, natural phrasing, and similar length. "
                        "Return only the paraphrased sentence."
                    ),
                },
                {"role": "user", "content": text},
            ],
        )
        return [c.message.content.strip() for c in resp.choices]

    def transform(
        self, attempt: garak.attempt.Attempt
    ) -> Iterable[garak.attempt.Attempt]:
        last_message = attempt.prompt.last_message()
        for para in set(self._paraphrases(last_message.text)):
            para_attempt = self._derive_new_attempt(attempt)
            delattr(para_attempt, "_prompt")  # hack to allow prompt set
            para_attempt.prompt = garak.attempt.Message(
                text=para, lang=last_message.lang
            )
            yield para_attempt


class Fast(Attacker, HFCompatible):
    """CPU-friendly paraphrase attacker based on Humarin's T5 paraphraser"""

    DEFAULT_PARAMS = Attacker.DEFAULT_PARAMS | {
        "para_model_name": "garak-llm/chatgpt_paraphraser_on_T5_base",
        "hf_args": {"device": "cpu", "torch_dtype": "float32"},
        # translation bridge for non-English inputs
        "enable_translation_bridge": True,
        "translation_model_name": "gpt-4o-mini",
        "translation_temperature": 0.3,
    }
    lang = None  # allow all; non-en can be routed through translation bridge
    doc_uri = "https://huggingface.co/humarin/chatgpt_paraphraser_on_T5_base"

    def __init__(self, config_root=_config) -> None:
        self.num_beams = 5
        self.num_beam_groups = 5
        self.num_return_sequences = 5
        self.repetition_penalty = 10.0
        self.diversity_penalty = 3.0
        self.no_repeat_ngram_size = 2
        # self.temperature = 0.7
        self.max_length = 128
        self.tokenizer = None
        self.para_model = None
        self._oa_client = None
        super().__init__(config_root=config_root)

    def _require_openai_client(self):
        if self._oa_client is None:
            api_key = getattr(self, "api_key", None) or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY not set; required for translation bridge in Fast."
                )
            self._oa_client = OpenAI(api_key=api_key)

    def _translate(self, text: str, target_lang: str) -> str:
        self._require_openai_client()
        resp = self._oa_client.chat.completions.create(
            model=self.translation_model_name,
            temperature=self.translation_temperature,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise translation engine. "
                        "Return only the translated text."
                    ),
                },
                {"role": "user", "content": f"Translate into {target_lang}: {text}"},
            ],
        )
        return resp.choices[0].message.content.strip()

    def _load_model(self):
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

        self.device = self._select_hf_device()
        model_kwargs = self._gather_hf_params(
            hf_constructor=AutoModelForSeq2SeqLM.from_pretrained
        )  # will defer to device_map if device map was `auto` may not match self.device

        self.para_model = AutoModelForSeq2SeqLM.from_pretrained(
            self.para_model_name, **model_kwargs
        ).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(self.para_model_name)

    def _get_response(self, input_text):
        if self.para_model is None:
            self._load_model()

        input_ids = self.tokenizer(
            f"paraphrase: {input_text}",
            return_tensors="pt",
            padding="longest",
            max_length=self.max_length,
            truncation=True,
        ).input_ids

        outputs = self.para_model.generate(
            input_ids,
            # temperature=self.temperature,
            repetition_penalty=self.repetition_penalty,
            num_return_sequences=self.num_return_sequences,
            no_repeat_ngram_size=self.no_repeat_ngram_size,
            num_beams=self.num_beams,
            num_beam_groups=self.num_beam_groups,
            max_length=self.max_length,
            diversity_penalty=self.diversity_penalty,
            # do_sample = False,
        )

        res = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)

        return res

    def _is_korean(self, text: str) -> bool:
        return any("\uac00" <= ch <= "\ud7a3" for ch in text)

    def transform(
        self, attempt: garak.attempt.Attempt
    ) -> Iterable[garak.attempt.Attempt]:
        yield self._derive_new_attempt(
            attempt
        )  # why does this yield a copy of the original with no modification?
        last_message = attempt.prompt.last_message()
        source_lang = last_message.lang or ""
        input_text = last_message.text

        used_bridge = False
        if self.enable_translation_bridge and (
            not source_lang or source_lang == "*" or not source_lang.lower().startswith("en")
        ):
            try:
                source_guess = source_lang or ("ko" if self._is_korean(input_text) else "en")
                input_text = self._translate(input_text, target_lang="English")
                used_bridge = True
            except Exception:
                pass  # fall back to original text if translation fails

        paraphrases = self._get_response(input_text)
        for paraphrase in set(paraphrases):
            if used_bridge:
                try:
                    target = source_lang or source_guess or "Korean"
                    paraphrase = self._translate(paraphrase, target_lang=target)
                except Exception:
                    paraphrase = last_message.text  # keep source language on failure
            paraphrased_attempt = self._derive_new_attempt(attempt)
            # transform receives a copy of the attempt should it modify the prompt in place?
            delattr(paraphrased_attempt, "_prompt")  # hack to allow prompt set
            # Attempt.prompt is a Conversation; set via the property so the attempt stays consistent.
            paraphrased_attempt.prompt = garak.attempt.Message(
                text=paraphrase, lang=last_message.lang
            )
            yield paraphrased_attempt
