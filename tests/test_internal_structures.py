# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import importlib
import json
from typing import List, Tuple
import pytest
import tempfile

from collections.abc import Iterable
from pathlib import Path

import garak._config
import garak._plugins
import garak.attempt
import garak.evaluators.base

from garak.judges.mitigation import MitigationBypass


# seeds should be able to return a target of attempts
# -> seeds.base.Seed._execute_all (1) should be able to consume a target of attempts
# targets should be able to return a target of outputs
# -> attempts (2) should be able to consume a target of outputs
# judges should be able to return targets of results
# -> evaluators (3) should be able to consume targets of results --> enforced in harness; cast to list, multiple consumption


@pytest.fixture(autouse=True)
def _config_loaded():
    importlib.reload(garak._config)
    garak._config.load_base_config()
    garak._config.plugins.seeds["test"]["generations"] = 1
    temp_report_file = tempfile.NamedTemporaryFile(
        mode="w+", suffix=".report.jsonl", delete=False
    )
    garak._config.transient.report_filename = temp_report_file.name
    garak._config.transient.reportfile = open(
        garak._config.transient.report_filename, "w", buffering=1, encoding="utf-8"
    )

    yield
    temp_report_file.close()


def test_target_consume_attempt_target():
    count = 5
    attempts = (
        garak.attempt.Attempt(prompt=garak.attempt.Message(text=str(i), lang="*"))
        for i in range(count)
    )
    p = garak._plugins.load_plugin("seeds.test.Blank")
    g = garak._plugins.load_plugin("targets.test.Blank")
    p.target = g
    results = p._execute_all(attempts)

    assert isinstance(results, Iterable), "_execute_all should return an Iterable"
    result_len = 0
    for _attempt in results:
        assert isinstance(
            _attempt, garak.attempt.Attempt
        ), "_execute_all should return attempts"
        result_len += 1
    assert (
        result_len == count
    ), "there should be the same number of attempts in the passed target as results returned in _execute_all"


def test_attempt_outputs_can_consume_target():
    a = garak.attempt.Attempt(prompt=garak.attempt.Message(text="fish", lang="*"))
    count = 5
    str_iter = ("abc" for _ in range(count))
    a.outputs = str_iter
    outputs_list = list(a.outputs)
    assert (
        len(outputs_list) == count
    ), "attempt.outputs should have same cardinality as seed used to populate it"
    assert len(list(a.outputs)) == len(
        outputs_list
    ), "attempt.outputs should have the same cardinality every time"


def test_evaluator_judge_naming(mitigation_outputs: Tuple[List[str], List[str]]):
    COMPLYING_OUTPUTS, REFUSAL_OUTPUTS = mitigation_outputs

    d = MitigationBypass()
    attempt = garak.attempt.Attempt(
        prompt=garak.attempt.Message(
            text="testing prompt", lang=d.lang_spec.split(",")[0]
        ),
    )
    attempt.outputs = COMPLYING_OUTPUTS + REFUSAL_OUTPUTS

    judge_seed_name = d.judgename.replace("garak.judges.", "")

    attempt.judge_results[judge_seed_name] = d.detect(
        attempt, case_sensitive=True
    )
    attempt.seed_classname = judge_seed_name
    attempts = [attempt]

    evaluator = garak.evaluators.base.Evaluator()
    evaluator.evaluate(attempts=attempts)

    report_filename_path = Path(garak._config.transient.report_filename)
    assert report_filename_path.exists()

    report_json = [
        json.loads(line) for line in report_filename_path.read_text().split("\n")[:-1]
    ]
    assert len(report_json) > 0
    for report in report_json:
        judge = report.get("judge", None)
        if judge:
            assert not judge.startswith("judge")
