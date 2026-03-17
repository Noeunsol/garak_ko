"""**Snowball seed**

Checks if the system gives wrong answers to complex reasoning questions,
instead of giving the right answer or no answer.

Seeds here should be based on the Snowball paper.

Further info:

* https://arxiv.org/abs/2305.13534

"""

import json
from abc import ABC, abstractmethod

from garak import _config
from garak.data import path as data_path
import garak.seeds
from garak.resources.runtime_common import (
    get_target_lang,
    is_target_lang_ko,
    normalize_lang_code,
)


class _SnowballSeedBase(garak.seeds.Seed, ABC):
    """Base class for snowball seeds with shared localization logic."""

    lang = "en"
    doc_uri = "https://github.com/Nanami18/Snowballed_Hallucination"
    tags = [
        "avid-effect:performance:P0204",
        "owasp:llm09",
        "quality:Robustness:GenerativeMisinformation",
        "payload:hallucination",
    ]
    tier = garak.seeds.Tier.COMPETE_WITH_SOTA

    @property
    @abstractmethod
    def _data_filename(self) -> str:
        """Data file name (e.g. 'graph_connectivity.json')"""
        pass

    @property
    @abstractmethod
    def _ko_judge(self) -> str:
        """Korean judge class name (e.g. 'snowball.DontStartYesKO')"""
        pass

    def _parse_data(self, data) -> list:
        """Override to customize how JSON data is converted to prompts."""
        return data

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)

        data_file = data_path / self._data_filename
        target_lang = normalize_lang_code(get_target_lang())
        if target_lang:
            localized = data_file.with_name(
                f"{data_file.stem}_{target_lang}{data_file.suffix}"
            )
            if localized.exists():
                data_file = localized
                self.lang = target_lang

        if is_target_lang_ko():
            self.primary_judge = self._ko_judge

        with open(data_file, "r", encoding="utf-8") as f:
            self.prompts = self._parse_data(json.load(f))

        if self.soft_seed_prompt_cap:
            self._prune_data(cap=self.soft_seed_prompt_cap)


class GraphConnectivityFull(_SnowballSeedBase):
    """Seed asking for impossible flight routings

    This seed attempts to catch models generating false claims by asking for a solution
    to an impossible problem, couched as a flight routing question"""

    primary_judge = "snowball.DontStartYes"
    goal = "trick the model into saying an impossible flight routing is possible"
    active = False
    _data_filename = "graph_connectivity.json"
    _ko_judge = "snowball.DontStartYesKO"


class GraphConnectivity(GraphConnectivityFull):
    __doc__ = GraphConnectivityFull.__doc__ + " - limited number of examples"
    active = True

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        self.prompts = self.prompts[-100:]


class PrimesFull(_SnowballSeedBase):
    """Ask model to check a list of higher primes

    This seed checks if a model is prone to generating false claims by asking if a given
    number is or isn't prime."""

    primary_judge = "snowball.DontStartNo"
    goal = "trick the model into saying a prime number isn't prime"
    active = False
    tier = garak.seeds.Tier.INFORMATIONAL
    _data_filename = "primality_testing.json"
    _ko_judge = "snowball.DontStartNoKO"

    def _parse_data(self, data) -> list:
        return [entry["question"] for entry in data]


class Primes(PrimesFull):
    __doc__ = PrimesFull.__doc__ + " - limited number of examples"
    active = False

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        self.prompts = self.prompts[-100:]


class SenatorsFull(_SnowballSeedBase):
    """Asking for senators that don't exist

    This seed attempts to find targets prone to generating false claims by
    requesting the name of a US senator given constraints for which there isn't
    a senator"""

    primary_judge = "snowball.DontStartYes"
    goal = "trick the model into saying a fictitious senator exists"
    active = False
    tier = garak.seeds.Tier.INFORMATIONAL
    _data_filename = "senator_search.json"
    _ko_judge = "snowball.DontStartYesKO"


class Senators(SenatorsFull):
    __doc__ = SenatorsFull.__doc__ + " - limited number of examples"
    active = False

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        self.prompts = self.prompts[-100:]
