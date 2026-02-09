"""**Snowball seed**

Checks if the system gives wrong answers to complex reasoning questions,
instead of giving the right answer or no answer.

Seeds here should be based on the Snowball paper.

Further info:

* https://arxiv.org/abs/2305.13534

"""

import json

from garak import _config
from garak.data import path as data_path
import garak.seeds


def _is_ko_target() -> bool:
    return getattr(_config.run, "target_lang", None) == "ko"


class GraphConnectivityFull(garak.seeds.Seed):
    """Seed asking for impossible flight routings

    This seed attempts to catch models generating false claims by asking for a solution
    to an impossible problem, couched as a flight routing question"""

    lang = "en"
    doc_uri = "https://github.com/Nanami18/Snowballed_Hallucination"
    primary_detector = "snowball.DontStartYes"
    tags = [
        "avid-effect:performance:P0204",
        "owasp:llm09",
        "quality:Robustness:GenerativeMisinformation",
        "payload:hallucination",
    ]
    goal = "trick the model into saying an impossible flight routing is possible"
    active = False
    tier = garak.seeds.Tier.COMPETE_WITH_SOTA

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        target_lang = getattr(_config.run, "target_lang", None)
        graph_path = data_path / "graph_connectivity.json"
        if target_lang:
            localized = graph_path.with_name(
                f"{graph_path.stem}.{target_lang}{graph_path.suffix}"
            )
            if localized.exists():
                graph_path = localized
                self.lang = target_lang
        if _is_ko_target():
            self.primary_detector = "snowball.DontStartYesKO"
        with open(
            graph_path,
            "r",
            encoding="utf-8",
        ) as f:
            self.prompts = json.load(f)
        # Limit attempts per seed using run.soft_seed_prompt_cap [추후 제거 가능]
        if self.soft_seed_prompt_cap:
            self._prune_data(cap=self.soft_seed_prompt_cap)


class GraphConnectivity(GraphConnectivityFull, garak.seeds.Seed):
    __doc__ = GraphConnectivityFull.__doc__ + " - limited number of examples"
    active = True

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        self.prompts = self.prompts[-100:]


class PrimesFull(garak.seeds.Seed):
    """Ask model to check a list of higher primes

    This seed checks if a model is prone to generating false claims by asking if a given
    number is or isn't prime."""

    lang = "en"
    doc_uri = "https://github.com/Nanami18/Snowballed_Hallucination"
    primary_detector = "snowball.DontStartNo"
    tags = [
        "avid-effect:performance:P0204",
        "owasp:llm09",
        "quality:Robustness:GenerativeMisinformation",
        "payload:hallucination",
    ]
    goal = "trick the model into saying a prime number isn't prime"
    active = False
    tier = garak.seeds.Tier.INFORMATIONAL

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        target_lang = getattr(_config.run, "target_lang", None)
        prime_path = data_path / "primality_testing.json"
        if target_lang:
            localized = prime_path.with_name(
                f"{prime_path.stem}.{target_lang}{prime_path.suffix}"
            )
            if localized.exists():
                prime_path = localized
                self.lang = target_lang
        if _is_ko_target():
            self.primary_detector = "snowball.DontStartNoKO"
        with open(
            prime_path,
            "r",
            encoding="utf-8",
        ) as f:
            dataset = json.load(f)
            self.prompts = [entry["question"] for entry in dataset]
        # Limit attempts per seed using run.soft_seed_prompt_cap [추후 제거 가능]
        if self.soft_seed_prompt_cap:
            self._prune_data(cap=self.soft_seed_prompt_cap)


class Primes(PrimesFull, garak.seeds.Seed):
    __doc__ = PrimesFull.__doc__ + " - limited number of examples"
    active = False

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        self.prompts = self.prompts[-100:]


class SenatorsFull(garak.seeds.Seed):
    """Asking for senators that don't exist

    This seed attempts to find generators prone to generating false claims by
    requesting the name of a US senator given constraints for which there isn't
    a senator"""

    lang = "en"
    doc_uri = "https://github.com/Nanami18/Snowballed_Hallucination"
    primary_detector = "snowball.DontStartYes"
    tags = [
        "avid-effect:performance:P0204",
        "owasp:llm09",
        "quality:Robustness:GenerativeMisinformation",
        "payload:hallucination",
    ]
    goal = "trick the model into saying a fictitious senator exists"
    active = False
    tier = garak.seeds.Tier.INFORMATIONAL

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        target_lang = getattr(_config.run, "target_lang", None)
        senator_path = data_path / "senator_search.json"
        if target_lang:
            localized = senator_path.with_name(
                f"{senator_path.stem}.{target_lang}{senator_path.suffix}"
            )
            if localized.exists():
                senator_path = localized
                self.lang = target_lang
        if _is_ko_target():
            self.primary_detector = "snowball.DontStartYesKO"
        with open(
            senator_path,
            "r",
            encoding="utf-8",
        ) as f:
            self.prompts = json.load(f)
        # Limit attempts per seed using run.soft_seed_prompt_cap [추후 제거 가능]
        if self.soft_seed_prompt_cap:
            self._prune_data(cap=self.soft_seed_prompt_cap)


class Senators(SenatorsFull, garak.seeds.Seed):
    __doc__ = SenatorsFull.__doc__ + " - limited number of examples"
    active = False

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        self.prompts = self.prompts[-100:]
