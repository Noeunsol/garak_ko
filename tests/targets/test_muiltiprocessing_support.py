# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import pytest
import importlib


# TODO: expand this when all `parallel_capable` targets can be evaluated
# TARGETS = [
#     classname
#     for (classname, active) in _plugins.enumerate_plugins("targets")
#     if _plugins.plugin_info(classname)["parallel_capable"]
# ]
TARGETS = [
    "targets.huggingface.InferenceAPI",
    "targets.huggingface.InferenceEndpoint",
    "targets.mistral.MistralTarget",
    "targets.nvcf.NvcfChat",
    "targets.nvcf.NvcfCompletion",
    "targets.replicate.InferenceEndpoint",
    "targets.replicate.ReplicateTarget",
]

MODEL_NAME = "gpt-3.5-turbo-instruct"
ENV_VAR = os.path.abspath(
    __file__
)  # use test path as hint encase env changes are missed


def build_test_instance(module_klass):
    if hasattr(module_klass, "ENV_VAR"):
        stored_env = os.getenv(module_klass.ENV_VAR, None)
        os.environ[module_klass.ENV_VAR] = ENV_VAR
    try:
        class_instance = module_klass(name=MODEL_NAME)
    except ModuleNotFoundError as mnfe:
        pytest.skip(mnfe.args[0])
    if stored_env is not None:
        os.environ[module_klass.ENV_VAR] = stored_env
    else:
        del os.environ[module_klass.ENV_VAR]
    return class_instance


# helper method to pass mock config
def generate_in_subprocess(*args):
    target = args[0]
    return target.name


@pytest.mark.parametrize("classname", TARGETS)
def test_multiprocessing(classname):
    parallel_attempts = 4
    iterations = 2
    namespace = classname[: classname.rindex(".")]
    full_namespace = f"garak.{namespace}"
    klass_name = classname[classname.rindex(".") + 1 :]
    mod = importlib.import_module(full_namespace)
    klass = getattr(mod, klass_name)
    target = build_test_instance(klass)
    params = [
        target,
        target,
        target,
    ]

    for _ in range(iterations):
        from multiprocessing import Pool

        with Pool(parallel_attempts) as attempt_pool:
            for result in attempt_pool.imap_unordered(generate_in_subprocess, params):
                assert result is not None
