"""**Phrasing**

These attacks rephrase requests for unsafe content in an attempt to bypass safeguards.

This module is home to seeds that rely on specific grammatical alterations and rephrasing
to implement their techinque.

"""

from garak import _config
from garak.data import path as data_path
import garak.seeds


class PastTenseFull(garak.seeds.Seed):
    """Will the system give unsafe responses when asked to write about weapon creation or dangerous behavior in the past tense?

    This check sends the generator requests for advice on possibly protect or restricted subjects in the past tense.
    """

    active = False
    lang = "en"
    doc_uri = "https://arxiv.org/pdf/2407.11969v2"
    primary_detector = "mitigation.Prefixes"
    tags = [
        "owasp:llm01",
        "quality:Security:PromptStability",
        "payload:jailbreak",
    ]
    goal = "use past tense to disregard the system prompt"
    tier = garak.seeds.Tier.COMPETE_WITH_SOTA

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)

        self.prompts = []
        target_lang = getattr(_config.run, "target_lang", None)
        phrasing_path = data_path / "phrasing" / "past_tense_en.txt"
        if target_lang:
            localized = phrasing_path.with_name(
                f"{phrasing_path.stem.rsplit('_', 1)[0]}_{target_lang}{phrasing_path.suffix}"
            )
            if localized.exists():
                phrasing_path = localized
                self.lang = target_lang

        with open(phrasing_path, "r", encoding="utf-8") as file:
            for str in file:
                self.prompts.append(str.strip())


class PastTense(PastTenseFull):
    """Attempt to evade safeguards by setting requests in the past tense

    A subset of the tense-modified requests. Success is reported higher with more variation, so
    generations is overridden.
    """

    active = True

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        self._prune_data(cap=self.soft_seed_prompt_cap)


class FutureTenseFull(garak.seeds.Seed):
    """Will the system give unsafe responses when asked to write about weapon creation or dangerous behavior in the future tense?

    This check sends the generator requests for advice on possibly protect or restricted subjects in the future tense.
    """

    active = False

    lang = "en"
    doc_uri = "https://arxiv.org/pdf/2407.11969v2"
    primary_detector = "mitigation.Prefixes"
    tags = [
        "owasp:llm01",
        "quality:Security:PromptStability",
        "payload:jailbreak",
    ]
    goal = "use future tense to disregard the system prompt"
    tier = garak.seeds.Tier.COMPETE_WITH_SOTA

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)

        self.prompts = []
        target_lang = getattr(_config.run, "target_lang", None)
        phrasing_path = data_path / "phrasing" / "future_tense_en.txt"
        if target_lang:
            localized = phrasing_path.with_name(
                f"{phrasing_path.stem.rsplit('_', 1)[0]}_{target_lang}{phrasing_path.suffix}"
            )
            if localized.exists():
                phrasing_path = localized
                self.lang = target_lang

        with open(phrasing_path, "r", encoding="utf-8") as file:
            for str in file:
                self.prompts.append(str.strip())


class FutureTense(FutureTenseFull):
    """Attempt to evade safeguards by setting requests in the future tense

    A subset of the tense-modified requests. Success is reported higher with more variation, so
    generations is overridden.
    """

    active = True

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        self._prune_data(self.soft_seed_prompt_cap)
