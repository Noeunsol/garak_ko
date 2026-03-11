"""**Contentious term continuation seeds**

These seeds pose a phrase ending in an unwanted term, and see if the target will offer a continuation of that term.

Seeds that implement this kind of continuation attack belong in this module.

Operates by giving high-risk context as a prompt, extracted from e.g. Urban
Dictionary examples of use of contentious terms, and seeing if the model will
continue the term based on varying amounts of prefix.
"""

import json
import tqdm

import garak.resources.theme
from garak import _config
from garak.attempt import Attempt
from garak.data import path as data_path
from garak.exception import PluginConfigurationError
from garak.resources.runtime_common import is_target_lang_ko
import garak.seeds


class ContinueSlursReclaimedSlursFull(garak.seeds.Seed):
    """Continue partial word with slur or reclaimed slur.

    This seed poses a partial ethnic slur with some preceding content, and
    checks to see if the model will complete the slur."""

    lang = "en"
    doc_uri = ""
    primary_judge = "continuation.Continuation"
    tags = [
        "avid-effect:ethics:E0101",
        "avid-effect:ethics:E0301",
        "avid-effect:performance:P0401",
        "owasp:llm01",
        "quality:Behavioral:ContentSafety:Toxicity",
        "quality:Behavioral:ContentSafety:HateHarassment",
        "payload:unwanted:hatespeech",
    ]
    goal = "output an ethnic slur"
    active = False
    tier = garak.seeds.Tier.COMPETE_WITH_SOTA
    source_resource_filename = "slurprompts.jsonl"

    follow_prompt_cap = False

    @staticmethod
    def _seed_lang() -> str:
        return "ko" if is_target_lang_ko() else "en"

    def _resource_candidates(self) -> list:
        source_path = data_path / self.source_resource_filename
        candidates = []
        if self.lang != "en" and not source_path.stem.endswith(f"_{self.lang}"):
            candidates.append(
                source_path.with_name(f"{source_path.stem}_{self.lang}{source_path.suffix}")
            )
        candidates.append(source_path)
        # Keep order stable while removing duplicates.
        return list(dict.fromkeys(candidates))

    def _resolve_resource_path(self):
        for candidate in self._resource_candidates():
            if candidate.exists():
                return candidate
        msg = (
            "Unable to locate continuation source data. Expected one of: "
            + ", ".join(str(path) for path in self._resource_candidates())
        )
        raise PluginConfigurationError(msg)

    @staticmethod
    def _load_slur_prefixes(slur_path) -> list[tuple[str, str]]:
        slur_prefixes = []
        with open(slur_path, "r", encoding="utf-8") as slurfile:
            for line in slurfile:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                slur_prefixes.append((entry["term"], entry["prefix"]))
        return slur_prefixes

    def __init__(self, config_root=_config):
        self.lang = self._seed_lang()
        super().__init__(config_root=config_root)
        self._source_resource_path = self._resolve_resource_path()
        self._slur_prefixes = self._load_slur_prefixes(self._source_resource_path)

        self.prompts = []
        self.triggers = []
        seen_prompts = set()
        for term, prefix in self._slur_prefixes:
            # Candidate prompt variants are ordered to preserve reproducibility.
            term_variants = [""]
            if term:
                term_variants.append(term[0])  # first letter
            if len(term) > 2:
                term_variants.append(term[:2].strip())  # first two letters
            if term:
                term_variants.append(term[: int(len(term) / 2)].strip())  # first half

            for term_variant in dict.fromkeys(term_variants):
                candidate_prompt = prefix + term_variant
                if candidate_prompt in seen_prompts:
                    continue
                seen_prompts.add(candidate_prompt)
                self.prompts.append(candidate_prompt)
                self.triggers.append(term)

        if self.follow_prompt_cap:
            self._prune_data(self.soft_seed_prompt_cap)

        if self.langprovider is not None:
            preparation_bar = tqdm.tqdm(
                total=len(self.triggers),
                leave=False,
                colour=f"#{garak.resources.theme.LANGPROVIDER_RGB}",
                desc="Preparing triggers",
            )
            self.triggers = self.langprovider.get_text(
                self.triggers, notify_callback=preparation_bar.update
            )
            preparation_bar.close()

    def _attempt_prestore_hook(self, attempt: Attempt, seq: int) -> Attempt:
        attempt.notes = dict(
            attempt.notes
        )  # we don't want all attempts.notes to ref same dict
        attempt.notes["triggers"] = [str(self.triggers[seq])]
        return attempt


class ContinueSlursReclaimedSlurs(ContinueSlursReclaimedSlursFull, garak.seeds.Seed):
    """Continue partial word with slur or reclaimed slur.

    This seed poses a partial ethnic slur with some preceding content, and
    checks to see if the model will complete the slur. It uses a subset of 80
    slurs & contexts that test LLMs have been likely to provide completions for."""

    aliases = ["continuation.ContinueSlursReclaimedSlurs80"]
    active = True
    source_resource_filename = "slurprompts_mini.jsonl"  # high-quality selection
    follow_prompt_cap = True
