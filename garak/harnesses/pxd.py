# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""pxd harness

The pxd (seeds x judges) harness runs all specified seeds and analyses
results using all specified judges.

It's thorough, and might end up doing some comparisons that don't make so
much sense, because not all judges are designed to pick up failure modes
in all situations.
"""

import logging
from colorama import Fore, Style

from garak.harnesses.base import Harness

import garak._plugins as _plugins


class PxD(Harness):
    def run(self, model, seed_names, judge_names, evaluator, attacker_names=None):
        if attacker_names is None:
            attacker_names = []
        seed_names = sorted(seed_names)
        judge_names = sorted(judge_names)
        print(
            f"🕵️  queue of {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}seeds:{Style.RESET_ALL} "
            + ", ".join([name.replace("seeds.", "") for name in seed_names])
        )
        print(
            f"🔎 queue of {Style.RESET_ALL}{Fore.LIGHTBLUE_EX}judges:{Style.RESET_ALL} "
            + ", ".join([name.replace("judges.", "") for name in judge_names])
        )
        logging.info("seed queue: %s", " ".join(seed_names))
        self._load_attackers(attacker_names)
        for seedname in seed_names:
            try:
                seed = _plugins.load_plugin(seedname)
            except Exception as e:
                message = f"{seedname} load exception 🛑, skipping >>"
                print(message, str(e))
                logging.error("%s %s", message, str(e))
                continue
            if not seed:
                message = f"{seedname} load failed ⚠️, skipping >>"
                print(message)
                logging.warning(message)
                continue
            judges = []
            for judge_name in judge_names:
                judge = _plugins.load_plugin(judge_name, break_on_fail=False)
                if judge:
                    judges.append(judge)
                else:
                    msg = f" judge load failed: {judge_name}, skipping >>"
                    print(msg)
                    logging.error(msg)
            super().run(model, [seed], judges, evaluator, announce_seed=False)
            # del seed, h, judges
