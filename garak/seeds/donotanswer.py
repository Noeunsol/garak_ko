"""**Do-Not-Answer Seeds**

Present the target with a request for contentious or unwanted content.

Seeds in this module should be from the "Do Not Answer" paper.

Do-Not-Answer is an open-source dataset to evaluate LLMs' safety mechanism at a low cost.
The dataset consists of prompts to which language models are often trained not to answer.

The DNA tests are somewhat opinionated and don't represent universal norms (nothing does), so use with care.

Further info:
* ttps://github.com/Libr-AI/do-not-answer
* https://arxiv.org/abs/2308.13387

"""

import sys

from garak import _config
from garak.data import path as data_path
import garak.seeds

this = sys.modules[__name__]


def load_local_data(self):
    # prompts
    target_lang = getattr(_config.run, "target_lang", None)
    prompt_path = data_path / "donotanswer" / f"{self.dna_category}.txt"
    if target_lang:
        localized = prompt_path.with_name(
            f"{prompt_path.stem}.{target_lang}{prompt_path.suffix}"
        )
        if localized.exists():
            prompt_path = localized
            self.lang = target_lang

    with open(prompt_path, encoding="utf=8") as f:
        self.prompts = f.read().strip().split("\n")

    # Limit attempts per seed using run.soft_seed_prompt_cap [추후 제외 가능] 
    if self.soft_seed_prompt_cap:
        self._prune_data(cap=self.soft_seed_prompt_cap)


def local_constructor(self, config_root=_config):
    super(self.__class__, self).__init__(config_root=config_root)
    self.load_data()


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

for seed_class in list(DNA_SEED_TAGS.keys()):
    failure_name = seed_class.replace("_", " ")
    classname = seed_class.title().replace("_", "")
    goal = f"get model to respond as {failure_name}"
    descr = f"Implementation of {seed_class} seeds in DoNotAnswer_Prompts"
    doc = f"Do Not Answer seed\n\nA curated list of questions to which LLMs should not respond back, specifically testing {failure_name}"

    # define class

    setattr(
        this,
        classname,
        type(
            classname,
            (garak.seeds.Seed,),
            {
                "__init__": local_constructor,
                "__doc__": doc,
                "uri": "https://arxiv.org/abs/2308.13387",
                "lang": "en",
                "description": descr,
                "primary_judge": "mitigation.MitigationBypass",
                "prompts": [],
                "load_data": load_local_data,
                "goal": goal,
                "dna_category": seed_class,
                "tags": DNA_SEED_TAGS[seed_class],
                "active": False,  # strong content norms not applicable in many scenarios
                "tier": garak.seeds.Tier.UNLISTED,
            },
        ),
    )
