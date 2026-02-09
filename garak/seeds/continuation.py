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

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        # go through the list
        # for each term, work out first char, first three chars, all but last two chars
        # append these to each of the prefixes for that term
        self._slur_prefixes = []
        target_lang = getattr(_config.run, "target_lang", None)
        slur_path = data_path / self.source_resource_filename
        if target_lang:
            localized = slur_path.with_name(
                f"{slur_path.stem}.{target_lang}{slur_path.suffix}"
            )
            if localized.exists():
                slur_path = localized
        if target_lang == "ko":
            self.lang = "ko"
        with open(
            slur_path,
            "r",
            encoding="utf-8",
        ) as slurfile:
            for line in slurfile:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                self._slur_prefixes.append((entry["term"], entry["prefix"]))

        self.prompts = []
        self.triggers = []
        for term, prefix in self._slur_prefixes:
            term_variants = set(["", term[0]])  # blank, first letter
            if len(term) > 2:
                term_variants.add(term[:2].strip())  # first two letters
            term_variants.add(term[: int(len(term) / 2)].strip())  # first half of term

            for term_variant in term_variants:
                # would use a set but order is important
                candidate_prompt = prefix + term_variant
                if candidate_prompt not in self.prompts:
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
