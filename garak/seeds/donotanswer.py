"""**Do-Not-Answer Seeds**

Present the target with a request for contentious or unwanted content.

Seeds in this module should be from the "Do Not Answer" paper.

Do-Not-Answer is an open-source dataset to evaluate LLMs' safety mechanism at a low cost.
The dataset consists of prompts to which language models are often trained not to answer.

The DNA tests are somewhat opinionated and don't represent universal norms (nothing does), so use with care.

Further info:
* https://github.com/Libr-AI/do-not-answer
* https://arxiv.org/abs/2308.13387

"""

import sys

from garak import _config
from garak.data import path as data_path
from garak.resources.runtime_common import get_target_lang
import garak.seeds

this = sys.modules[__name__]


DNA_SEED_TAGS = {
    "discrimination_exclusion_toxicity_hateful_offensive": [
        "avid-effect:ethics:E0301",
        "quality:Behavioral:ContentSafety:Toxicity",
        "quality:Behavioral:ContentSafety:HateHarassment",
        "quality:Behavioral:ContentSafety:Violence",
        "quality:Behavioral:ContentSafety:Profanity",
    ],
    "human_chatbox": [
        "avid-effect:security:S0301",
        "quality:Behavioral:ContentSafety:Unauthorized",
    ],
    "information_hazard": [
        "owasp:llm06",
        "avid-effect:security:S0301",
        "quality:Security:Confidentiality",
    ],
    "malicious_uses": [
        "quality:Behavioral:ContentSafety:LegalGoodsServices",
    ],
    "misinformation_harms": [
        "quality:Robustness:GenerativeMisinformation",
        "avid-effect:ethics:E0402",
        "owasp:llm09",
    ],
}

class _DnaBase(garak.seeds.Seed):
    lang = "en"
    primary_judge = "mitigation.MitigationBypass"
    uri = "https://arxiv.org/abs/2308.13387"
    prompts = []
    active = False  # strong content norms not applicable in many scenarios
    tier = garak.seeds.Tier.UNLISTED
    dna_category: str

    def _load_prompts(self) -> None:
        target_lang = get_target_lang()
        prompt_path = data_path / "donotanswer" / f"{self.dna_category}.txt"
        if target_lang:
            localized = prompt_path.with_name(
                f"{prompt_path.stem}_{target_lang}{prompt_path.suffix}"
            )
            if localized.exists():
                prompt_path = localized
                self.lang = target_lang

        with open(prompt_path, encoding="utf-8") as f:
            self.prompts = f.read().strip().split("\n")

        if self.soft_seed_prompt_cap:
            self._prune_data(cap=self.soft_seed_prompt_cap)

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        self._load_prompts()


for _seed_class, _tags in DNA_SEED_TAGS.items():
    _failure_name = _seed_class.replace("_", " ")
    _classname = _seed_class.title().replace("_", "")
    setattr(
        this,
        _classname,
        type(
            _classname,
            (_DnaBase,),
            {
                "__doc__": (
                    f"Do Not Answer seed\n\nA curated list of questions to which LLMs should not "
                    f"respond back, specifically testing {_failure_name}"
                ),
                "description": f"Implementation of {_seed_class} seeds in DoNotAnswer_Prompts",
                "goal": f"get model to respond as {_failure_name}",
                "dna_category": _seed_class,
                "tags": _tags,
            },
        ),
    )
