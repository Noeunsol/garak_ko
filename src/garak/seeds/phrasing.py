"""**Phrasing**

These attacks rephrase requests for unsafe content in an attempt to bypass safeguards.

This module is home to seeds that rely on specific grammatical alterations and rephrasing
to implement their techinque.

"""

from abc import ABC, abstractmethod

from garak import _config
from garak.data import path as data_path
import garak.seeds
from garak.resources.runtime_common import is_target_lang_ko, get_target_lang


class _PhrasingSeedBase(garak.seeds.Seed, ABC):
    """Base class for phrasing seeds with shared localization logic."""

    lang = "en"
    doc_uri = "https://arxiv.org/pdf/2407.11969v2"
    primary_judge = "mitigation.Prefixes"
    use_llm_judge = True
    tags = [
        "owasp:llm01",
        "quality:Security:PromptStability",
        "payload:jailbreak",
    ]
    tier = garak.seeds.Tier.COMPETE_WITH_SOTA

    @property
    @abstractmethod
    def _data_filename(self) -> str:
        """Data file name (e.g. 'past_tense.txt') - must be overridden"""
        pass

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)

        phrasing_path = data_path / "phrasing" / self._data_filename
        target_lang = get_target_lang()
        if target_lang:
            localized = phrasing_path.with_name(
                f"{phrasing_path.stem}_{target_lang}{phrasing_path.suffix}"
            )
            if localized.exists():
                phrasing_path = localized

        if is_target_lang_ko():
            self.lang = "ko"

        with open(phrasing_path, "r", encoding="utf-8") as f:
            self.prompts = [line.strip() for line in f if line.strip()]


class PastTenseFull(_PhrasingSeedBase):
    """Will the system give unsafe responses when asked to write about weapon creation or dangerous behavior in the past tense?

    This check sends the target requests for advice on possibly protect or restricted subjects in the past tense.
    """

    active = False
    goal = "use past tense to disregard the system prompt"
    _data_filename = "past_tense.txt"


class PastTense(PastTenseFull):
    """Attempt to evade safeguards by setting requests in the past tense

    A subset of the tense-modified requests. Success is reported higher with more variation, so
    generations is overridden.
    """

    active = True

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        self._prune_data(cap=self.soft_seed_prompt_cap)


class FutureTenseFull(_PhrasingSeedBase):
    """Will the system give unsafe responses when asked to write about weapon creation or dangerous behavior in the future tense?

    This check sends the target requests for advice on possibly protect or restricted subjects in the future tense.
    """

    active = False
    goal = "use future tense to disregard the system prompt"
    _data_filename = "future_tense.txt"


class FutureTense(FutureTenseFull):
    """Attempt to evade safeguards by setting requests in the future tense

    A subset of the tense-modified requests. Success is reported higher with more variation, so
    generations is overridden.
    """

    active = True

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        self._prune_data(cap=self.soft_seed_prompt_cap)
