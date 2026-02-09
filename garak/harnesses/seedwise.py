# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Seedwise harness

Selects detectors to run for each seed based on that seed's recommendations
"""

import logging
from colorama import Fore, Style

from garak.detectors.base import Detector
from garak.harnesses.base import Harness

from garak import _config, _plugins


class SeedwiseHarness(Harness):
    def _load_detector(self, detector_name: str) -> Detector:
        detector = _plugins.load_plugin(
            "detectors." + detector_name, break_on_fail=False
        )
        if detector:
            return detector
        else:
            print(f" detector load failed: {detector_name}, skipping >>")
            logging.error(f" detector load failed: {detector_name}, skipping >>")
        return False

    def run(self, model, seednames, evaluator, attacker_names=None):
        """Execute a seed-by-seed scan

        Seeds are executed in name order. For each seed, the detectors
        recommended by that seed are loaded and used to provide scores
        of the results. The detector(s) to be used are determined with the
        following formula:
        * if the seed specifies a ``primary_detector``; ``_config.args`` is
        set; and ``_config.args.extended_detectors`` is true; the union of
        ``primary_detector`` and ``extended_detectors`` are used.
        * if the seed specifices a ``primary_detector`` and ``_config.args.extended_detectors``
        if false, or ``_config.args`` is not set, then only the detector in
        ``primary_detector`` is used.
        * if the seed does not specify ``primary_detector`` value, or this is
        ``None``, then detectors are queued based on the from the seed's
        ``recommended_detectors`` value; see :class:`garak.seeds.base.Seed` for the defaults.

        :param model: an instantiated generator providing an interface to the model to be examined
        :type model: garak.generators.base.Generator
        :param seednames: a list of seed names to be run
        :type seednames: List[str]
        :param evaluator: an instantiated evaluator for judging detector results
        :type evaluator: garak.evaluators.base.Evaluator
        :param attacker_names: a list of attacker names to be used this run
        :type attacker_names: List[str]
        """

        if attacker_names is None:
            attacker_names = []

        if not seednames:
            msg = "No seeds, nothing to do"
            logging.warning(msg)
            if hasattr(_config.system, "verbose") and _config.system.verbose >= 2:
                print(msg)
            raise ValueError(msg)

        self._load_attackers(attacker_names)

        seednames = sorted(seednames)
        print(
            f"🕵️  queue of {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}seeds:{Style.RESET_ALL} "
            + ", ".join([name.replace("seeds.", "") for name in seednames])
        )
        logging.info("seed queue: %s", " ".join(seednames))
        for seedname in seednames:
            try:
                seed = _plugins.load_plugin(seedname)
            except Exception as e:
                print(f"failed to load seed {seedname}")
                logging.warning("failed to load seed %s:", repr(e))
                continue
            if not seed:
                continue
            detectors = []

            if seed.primary_detector:
                d = self._load_detector(seed.primary_detector)
                if d:
                    detectors = [d]
                if _config.plugins.extended_detectors is True:
                    for detector_name in sorted(seed.extended_detectors):
                        d = self._load_detector(detector_name)
                        if d:
                            detectors.append(d)

            else:
                # Fallback for edge cases where migration didn't occur
                from garak import command
                command.deprecation_notice(
                    f"recommended_detector in seed {seedname} (fallback path)",
                    "0.9.0.6",
                    logging=logging,
                )
                for detector_name in sorted(seed.recommended_detector):
                    d = self._load_detector(detector_name)
                    if d:
                        detectors.append(d)

            super().run(model, [seed], detectors, evaluator, announce_seed=False)
            # del seed, h, detectors
