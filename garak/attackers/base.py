# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Base classes for attackers (formerly "attackers")."""

from collections.abc import Iterable
import logging
from typing import List

from colorama import Fore, Style
import tqdm

import garak.attempt
from garak import _config
from garak.configurable import Configurable


class Attacker(Configurable):
    """Base class for an attacker.

    An attacker should take as input a list of attempts, and return
    a list of events. It should be able to return a generator.
    It's worth storing the origin attempt ID in the notes attrib
    of derivative attempt objects.
    """

    doc_uri = ""
    lang = None  # set of languages this attacker should be constrained to
    active = True
    # list of strings naming modules required but not explicitly in garak by default
    extra_dependency_names = []

    DEFAULT_PARAMS = {}

    def __init__(self, config_root=_config) -> None:
        self._load_config(config_root)
        module = self.__class__.__module__.replace("garak.attackers.", "")
        self.fullname = f"{module}.{self.__class__.__name__}"
        # If set True, Seed will call untransform() on model output.
        self.post_attack_hook = False
        # Back-compat alias while the codebase migrates.
        self.post_attacker_hook = False
        print(
            f"🦾 loading {Style.BRIGHT}{Fore.LIGHTGREEN_EX}attacker: {Style.RESET_ALL}{self.fullname}"
        )
        logging.info("attacker init: %s", self)

    def _derive_new_attempt(
        self, source_attempt: garak.attempt.Attempt, seq=-1
    ) -> garak.attempt.Attempt:
        if seq == -1:
            seq = source_attempt.seq
        new_attempt = garak.attempt.Attempt(
            status=source_attempt.status,
            prompt=source_attempt.prompt,
            seed_classname=source_attempt.seed_classname,
            seed_params=source_attempt.seed_params,
            targets=source_attempt.targets,
            notes=source_attempt.notes,
            detector_results=source_attempt.detector_results,
            goal=source_attempt.goal,
            seq=seq,
        )
        new_attempt.notes["attacker_creator"] = self.__class__.__name__
        new_attempt.notes["attacker_source_attempt_uuid"] = str(
            source_attempt.uuid
        )  # UUIDs don't serialise nicely
        new_attempt.notes["attacker_source_seq"] = source_attempt.seq

        return new_attempt

    def transform(
        self, attempt: garak.attempt.Attempt
    ) -> Iterable[garak.attempt.Attempt]:
        """attempt copying is handled elsewhere. isn't that nice"""
        yield self._derive_new_attempt(attempt)

    def untransform(self, attempt: garak.attempt.Attempt) -> garak.attempt.Attempt:
        """Only necessary if attacker requires a post-attack hook"""
        pass

    def attack(
        self, source_attempts: List[garak.attempt.Attempt], seedname=""
    ) -> Iterable[garak.attempt.Attempt]:
        for source_attempt in tqdm.tqdm(
            source_attempts,
            desc=f"📥 Attacking seed: {seedname}/{self.fullname}",
            leave=False,
        ):
            # create one or more untransformed new attempts
            # don't include the original attempt/prompt in the attackers: https://github.com/NVIDIA/garak/issues/373
            new_attempts = []
            new_attempts.append(
                self._derive_new_attempt(source_attempt, source_attempt.seq)
            )
            for new_attempt in new_attempts:
                for transformed_new_attempt in self.transform(new_attempt):
                    # transform can returns multiple results
                    yield transformed_new_attempt

    # Back-compat name for callers that still use the old terminology.
    def attacker(
        self, source_attempts: List[garak.attempt.Attempt], seedname=""
    ) -> Iterable[garak.attempt.Attempt]:
        return self.attack(source_attempts, seedname=seedname)


# Back-compat base class name (plugins may still inherit Buff).
Buff = Attacker
