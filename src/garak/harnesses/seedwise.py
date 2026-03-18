# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Seedwise harness

Selects judges to run for each seed based on that seed's recommendations
"""

import logging
from colorama import Fore, Style

from garak.judges.base import Judge
from garak.harnesses.base import Harness

from garak import _config, _plugins


class SeedwiseHarness(Harness):
    def _load_judge(self, judge_name: str) -> Judge:
        judge = _plugins.load_plugin(
            "judges." + judge_name, break_on_fail=False
        )
        if judge:
            return judge
        else:
            print(f" judge load failed: {judge_name}, skipping >>")
            logging.error(f" judge load failed: {judge_name}, skipping >>")
        return False

    def run(self, model, seednames, evaluator, attacker_names=None):
        """Execute a seed-by-seed scan

        Seeds are executed in name order. For each seed, the judges
        recommended by that seed are loaded and used to provide scores
        of the results. The judge(s) to be used are determined with the
        following formula:
        * if the seed specifies a ``primary_judge``; ``_config.args`` is
        set; and ``_config.args.extended_judges`` is true; the union of
        ``primary_judge`` and ``extended_judges`` are used.
        * if the seed specifices a ``primary_judge`` and ``_config.args.extended_judges``
        if false, or ``_config.args`` is not set, then only the judge in
        ``primary_judge`` is used.
        * if the seed does not specify ``primary_judge`` value, or this is
        ``None``, then judges are queued based on the from the seed's
        ``recommended_judges`` value; see :class:`garak.seeds.base.Seed` for the defaults.

        :param model: an instantiated target providing an interface to the model to be examined
        :type model: garak.targets.base.Target
        :param seednames: a list of seed names to be run
        :type seednames: List[str]
        :param evaluator: an instantiated evaluator for judging judge results
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
            judges = []

            if seed.primary_judge:
                d = self._load_judge(seed.primary_judge)
                if d:
                    judges = [d]
                if _config.plugins.extended_judges is True:
                    for judge_name in sorted(seed.extended_judges):
                        d = self._load_judge(judge_name)
                        if d:
                            judges.append(d)

            else:
                # Fallback for edge cases where migration didn't occur
                from garak import command
                command.deprecation_notice(
                    f"recommended_judge in seed {seedname} (fallback path)",
                    "0.9.0.6",
                    logging=logging,
                )
                for judge_name in sorted(seed.recommended_judge):
                    d = self._load_judge(judge_name)
                    if d:
                        judges.append(d)

            super().run(model, [seed], judges, evaluator, announce_seed=False)
            # del seed, h, judges
