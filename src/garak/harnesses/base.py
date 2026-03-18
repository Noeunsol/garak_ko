# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Base harness

A harness coordinates running seeds on a target, running judges on the
outputs, and evaluating the results.

This module includes the class Harness, which all `garak` harnesses must
inherit from.
"""

import importlib
import json
import logging
from collections.abc import Iterator
from typing import List

import tqdm

import garak.attempt
from garak import _config
from garak import _plugins
from garak.configurable import Configurable


def _initialize_runtime_services():
    """Initialize and validate runtime services required for a successful test"""

    from garak.exception import GarakException

    # TODO: this block may be gated in the future to ensure it is only run once. At this time
    # only one harness will execute per run so the output here is reasonable.
    service_names = ["garak.langservice"]
    for service_name in service_names:
        logging.info("service import: " + service_name)
        service = importlib.import_module(service_name)
        try:
            if service.enabled():
                symbol, msg = service.start_msg()
                if len(msg):
                    logging.info(msg)
                    print(f"{symbol} {msg}")
                service.load()
        except GarakException as e:
            logging.critical(f"❌ {service_name} setup failed! ❌", exc_info=e)
            raise e


class Harness(Configurable):
    """Class to manage the whole process of probing, detecting and evaluating"""

    active = True
    # list of strings naming modules required but not explicitly in garak by default
    extra_dependency_names = []

    DEFAULT_PARAMS = {
        "strict_modality_match": False,
    }

    def __init__(self, config_root=_config):
        self._load_config(config_root)

        _initialize_runtime_services()

        logging.info("harness init: %s", self)

    def _load_attackers(self, attacker_names: List) -> None:
        """Instantiate specified attackers into global config

        Inheriting classes call _load_attackers in their run() methods. They then call
        garak.harness.base.Harness.run themselves, and so if _load_attackers() is called
        from this base class, we'll end up w/ inefficient reinstantiation of attacker
        objects. If one wants to use attackers directly with this harness without
        subclassing, then call this method instance directly.

        Don't use this in the base class's run method, garak.harness.base.Harness.run;
        harnesses should be explicit about how they expect to deal with attackers.
        """

        _config.attackermanager.attackers = []
        for attacker_name in attacker_names:
            err_msg = None
            try:
                name = (str(attacker_name) or "").strip()
                if name.startswith("garak."):
                    name = name[len("garak.") :]
                # Allow legacy "attackers.*" specs, but load as attackers.
                if name.startswith("attackers."):
                    name = "attackers." + name[len("attackers.") :]
                if not name.startswith("attackers."):
                    name = "attackers." + name
                _config.attackermanager.attackers.append(_plugins.load_plugin(name))
                logging.debug("loaded %s", name)
            except ValueError as ve:
                err_msg = f"❌🦾 attacker load error:❌ {ve}"
            except Exception as e:
                err_msg = f"❌🦾 failed to load attacker {attacker_name}:❌ {e}"
            finally:
                if err_msg is not None:
                    print(err_msg)
                    logging.warning(err_msg)
                    continue

    # Back-compat alias while other harnesses migrate.
    def load_attackers(self, attacker_names: List) -> None:
        self._load_attackers(attacker_names)

    def _start_run_hook(self):
        self._http_lib_user_agents = _config.get_http_lib_agents()
        _config.set_all_http_lib_agents(_config.run.user_agent)

    def _end_run_hook(self):
        _config.set_http_lib_agents(self._http_lib_user_agents)

    def run(self, model, seeds, judges, evaluator, announce_seed=True) -> None:
        """Core harness method

        :param model: an instantiated target providing an interface to the model to be examined
        :type model: garak.targets.Target
        :param seeds: a list of seed instances to be run
        :type seeds: List[garak.seeds.base.Seed]
        :param judges: a list of judges to use on the results of the seeds
        :type judges: List[garak.judges.base.Judge]
        :param evaluator: an instantiated evaluator for judging judge results
        :type evaluator: garak.evaluators.base.Evaluator
        :param announce_seed: Should we print seed loading messages?
        :type announce_seed: bool, optional
        """
        if not judges:
            msg = "No judges, nothing to do"
            logging.warning(msg)
            if hasattr(_config.system, "verbose") and _config.system.verbose >= 2:
                print(msg)
            raise ValueError(msg)

        if not seeds:
            msg = "No seeds, nothing to do"
            logging.warning(msg)
            if hasattr(_config.system, "verbose") and _config.system.verbose >= 2:
                print(msg)
            raise ValueError(msg)

        self._start_run_hook()

        for seed in seeds:
            logging.debug("harness: seed start for %s", seed.seedname)
            if not seed:
                continue

            modality_match = _modality_match(
                seed.modality["in"], model.modality["in"], self.strict_modality_match
            )

            if not modality_match:
                logging.warning(
                    "seed skipped due to modality mismatch: %s - model expects %s",
                    seed.seedname,
                    model.modality["in"],
                )
                continue

            attempt_results = seed.seed(model)
            assert isinstance(
                attempt_results, (list, Iterator)
            ), "probing should always return an ordered iterable"

            for d in judges:
                logging.debug("harness: run judge %s", d.judgename)
                attempt_iterator = tqdm.tqdm(attempt_results, leave=False)
                judge_seed_name = d.judgename.replace("garak.judges.", "")
                attempt_iterator.set_description("judges." + judge_seed_name)
                for attempt in attempt_iterator:
                    if d.skip:
                        continue
                    attempt.judge_results[judge_seed_name] = list(
                        d.detect(attempt)
                    )

            for attempt in attempt_results:
                attempt.status = garak.attempt.ATTEMPT_COMPLETE
                _config.transient.reportfile.write(json.dumps(attempt.as_dict(), ensure_ascii=False) + "\n")

            if len(attempt_results) == 0:
                logging.warning(
                    "zero attempt results: seed %s, judge %s",
                    seed.seedname,
                    judge_seed_name,
                )
            else:
                evaluator.evaluate(attempt_results)

        self._end_run_hook()

        logging.debug("harness: seed list iteration completed")


def _modality_match(seed_modality, target_modality, strict):
    if strict:
        # must be perfect match
        return seed_modality == target_modality
    else:
        # everything seed wants must be accepted by model
        return set(seed_modality).intersection(target_modality) == set(
            seed_modality
        )
