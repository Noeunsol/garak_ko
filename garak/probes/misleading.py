"""**Misleading claims**

Pose targets with false claims and check if they successfully debunk/reject them.

This module homes probes that attempt to mislead the target.

Will a model refute false claims, or will it go along with false information
and perform tasks based on them? This checks for a subset of hallucination
types, where false information is present that the system is expected to
deny, refute, or contradict.
"""

from garak import _config
from garak.data import path as data_path
import garak.probes


class FalseAssertion(garak.probes.Probe):
    """Does the model reject [questions based on] false claims?

    Poses a number of false statements to the model and checks to see if the model
    refutes the statement, contradicts the statement, or issues a safety mitigation
    message."""

    lang = "en"
    doc_uri = "https://arxiv.org/abs/2304.13734"
    primary_detector = "misleading.MustRefuteClaimModel"
    extended_detectors = [
        "misleading.MustRefuteClaimKW",
        "mitigation.MitigationBypass",
        "misleading.MustContradictNLI",
    ]
    tags = [
        "avid-effect:performance:P0204",
        "owasp:llm09",
        "quality:Robustness:GenerativeMisinformation",
        "payload:hallucination",
    ]
    goal = "make the model expand on a false assertion"
    tier = garak.probes.Tier.COMPETE_WITH_SOTA
    active = True

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)

        target_lang = getattr(_config.run, "target_lang", None)
        if target_lang == "ko":
            self.lang = "ko"
            prefixes = ["", "왜 그런지 알아?", "이유가 뭔지 설명해줘."]
        else:
            prefixes = ["", "Why is it that", "Explain why"]

        self.prompts = []

        claims_path = data_path / "truefalse_falseclaims_50.txt"
        if target_lang:
            localized = claims_path.with_name(
                f"{claims_path.stem}.{target_lang}{claims_path.suffix}"
            )
            if localized.exists():
                claims_path = localized

        for prefix in prefixes:
            with open(claims_path, "r", encoding="utf-8") as assertions:
                for false_assertion in assertions:
                    false_assertion = false_assertion.strip()
                    if not false_assertion:
                        continue
                    if not prefix:
                        self.prompts.append(false_assertion)
                    else:
                        if target_lang != "ko" and false_assertion.startswith("The"):
                            false_assertion = "t" + false_assertion[1:]
                        self.prompts.append(f"{prefix} {false_assertion}")

        # Limit attempts per probe using run.soft_probe_prompt_cap [추후 제거 가능]
        if self.soft_probe_prompt_cap:
            self._prune_data(cap=self.soft_probe_prompt_cap)