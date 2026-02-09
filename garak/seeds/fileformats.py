# SPDX-FileCopyrightText: Portions Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""**File formats**

Look at files associated with the target for potentially vulnerable items.

Seeds in this module should examine files associated with the target, rather than inference.

The seeds check in the model background for file types that may have known weaknesses."""

import logging
from typing import Iterable

import huggingface_hub
import tqdm

from garak import _config
import garak.attempt
import garak.seeds
import garak.resources.theme


class HF_Files(garak.seeds.Seed):
    """Get a manifest of files associated with a Hugging Face generator

    This seed returns a list of filenames associated with a Hugging Face
    generator, if that applies to the generator. Not enabled for all types,
    e.g. some endpoints."""

    lang = "*"
    tags = ["owasp:llm05"]
    goal = "get a list of files associated with the model"
    tier = garak.seeds.Tier.OF_CONCERN

    # default detector to run, if the primary/extended way of doing it is to be used (should be a string formatted like recommended_detector)
    primary_detector = "fileformats.FileIsPickled"
    extended_detectors = [
        "fileformats.FileIsExecutable",
        "fileformats.PossiblePickleName",
    ]
    active = False

    supported_generators = {"Model", "Pipeline", "LLaVA"}

    # support mainstream any-to-any large models
    # legal element for str list `modality['in']`: 'text', 'image', 'audio', 'video', '3d'
    # refer to Table 1 in https://arxiv.org/abs/2401.13601
    # we focus on LLM input for seed
    modality: dict = {"in": {"text"}}

    def __init__(self, config_root=_config):
        self._load_config(config_root)
        super().__init__(config_root=config_root)

    def seed(self, generator) -> Iterable[garak.attempt.Attempt]:
        """attempt to gather target generator model file list, returning a list of results"""
        logging.debug("seed execute: %s", self)

        package_path = generator.__class__.__module__
        if package_path.split(".")[-1] != "huggingface":
            return []
        if generator.__class__.__name__ not in self.supported_generators:
            return []
        attempt = self._mint_attempt(generator.name)

        repo_filenames = huggingface_hub.list_repo_files(generator.name)
        local_filenames = []
        for repo_filename in tqdm.tqdm(
            repo_filenames,
            leave=False,
            desc=f"Gathering files in {generator.name}",
            colour=f"#{garak.resources.theme.SEED_RGB}",
        ):
            local_filename = huggingface_hub.hf_hub_download(
                generator.name, repo_filename, force_download=False
            )
            local_filenames.append(local_filename)

        # Limit attempts per seed using run.soft_seed_prompt_cap [추후 제거 가능]
        if self.soft_seed_prompt_cap:
            local_filenames = local_filenames[: self.soft_seed_prompt_cap]

        attempt.notes["format"] = "local filename"
        attempt.outputs = local_filenames

        logging.debug("seed return: %s with %s filenames", self, len(local_filenames))

        return [attempt]
