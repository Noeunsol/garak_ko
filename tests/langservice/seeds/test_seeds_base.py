# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest
import pathlib
import tempfile
import os

from garak import _config, _plugins
from garak.attempt import Message, Attempt, Conversation


NON_PROMPT_SEEDS = [
    "seeds.dan.AutoDAN",
    "seeds.tap.TAP",
    "seeds.suffix.BEAST",
    "seeds.suffix.GCG",
    "seeds.fitd.FITD",
]
ATKGEN_PROMPT_SEEDS = ["seeds.atkgen.Tox"]
VISUAL_SEEDS = [
    "seeds.visual_jailbreak.FigStep",
    "seeds.visual_jailbreak.FigStepFull",
]
AUDIO_SEEDS = [
    "seeds.audio.AudioAchillesHeel",
]
SEEDS = [
    classname
    for (classname, _) in _plugins.enumerate_plugins("seeds")
    if classname not in NON_PROMPT_SEEDS
    and classname not in VISUAL_SEEDS
    and classname not in ATKGEN_PROMPT_SEEDS
    and classname not in AUDIO_SEEDS
]
openai_api_key_missing = not os.getenv("OPENAI_API_KEY")


@pytest.fixture(autouse=True)
def seed_pre_req(classname):
    # this sets up config for seeds that access _config still
    _config.run.seed = 42
    local_config_path = str(
        pathlib.Path(__file__).parents[1] / "test_config" / "translation_local_low.yaml"
    )
    if os.path.exists(local_config_path) is False:
        pytest.skip("Local config file does not exist, skipping test.")
    _config.load_config(run_config_filename=local_config_path)
    # judges run by seeds write to the report file
    temp_report_file = tempfile.NamedTemporaryFile(
        mode="w+", delete=False, encoding="utf-8"
    )
    _config.transient.reportfile = temp_report_file
    _config.transient.report_filename = temp_report_file.name

    # since this does not go through cli generations must be set
    _, module, klass = classname.split(".")
    _config.plugins.seeds[module][klass]["generations"] = 1


RESPONSE_SAMPLES = [
    (
        [
            Message("text to translate", lang="fr"),
            Message("text to translate", lang="fr"),
            Message("text to translate", lang="fr"),
        ],
        "seeds.base.Seed",
    ),
    (
        [
            Message("text to translate", lang="fr"),
            None,
            None,
        ],
        "seeds.base.Seed",
    ),
    (
        [
            None,
            Message("text to translate", lang="fr"),
            None,
        ],
        "seeds.base.Seed",
    ),
    (
        [
            None,
            None,
            Message("text to translate", lang="fr"),
            None,
        ],
        "seeds.base.Seed",
    ),
]


@pytest.mark.parametrize("responses, classname", RESPONSE_SAMPLES)
def test_base_postprocess_attempt(responses, mocker):
    """Validate processing of reverse translation for various response cases"""
    import garak.langservice
    import garak.seeds.base
    from garak.langproviders.local import Passthru

    null_provider = Passthru(
        {
            "langproviders": {
                "local": {
                    "language": "en,en",
                }
            }
        }
    )

    mocker.patch.object(
        garak.langservice, "get_langprovider", return_value=null_provider
    )

    prompt_mock = mocker.patch.object(
        null_provider,
        "get_text",
        wraps=null_provider.get_text,
    )

    a = Attempt(prompt=Message("just a test attempt", lang="fr"))
    a.outputs = responses
    p = garak.seeds.base.Seed()
    p.lang = "en"
    r = p._postprocess_attempt(a)
    assert prompt_mock.called
    assert len(r.reverse_translation_outputs) == len(responses)
    for response, output in zip(r.reverse_translation_outputs, r.outputs):
        assert type(response) == type(
            output
        ), "translation index outputs should align with output types"


"""
Skip seeds.tap.PAIR because it needs openai api key and large gpu resource
"""


@pytest.mark.parametrize("classname", ATKGEN_PROMPT_SEEDS)
def test_atkgen_seed_translation(classname, mocker):
    # how can tests for atkgen seeds be expanded to ensure translation is called?
    import garak.langservice
    from garak.langproviders.local import Passthru

    null_provider = Passthru(
        {
            "langproviders": {
                "local": {
                    "language": "en,en",
                }
            }
        }
    )

    mocker.patch.object(
        garak.langservice, "get_langprovider", return_value=null_provider
    )

    prompt_mock = mocker.patch.object(
        null_provider,
        "get_text",
        wraps=null_provider.get_text,
    )

    seed_instance = _plugins.load_plugin(classname)
    # cut down test time
    seed_instance.max_calls_per_conv = 2
    seed_instance.convs_per_generation = 2
    seed_instance.allow_repetition = True  # we're counting responses, don't quit early

    if seed_instance.lang != "en" or classname == "seeds.tap.PAIR":
        return

    target_instance = _plugins.load_plugin("targets.test.Repeat")

    seed_instance.seed(target_instance)

    expected_langprovision_calls = (
        2 * seed_instance.max_calls_per_conv * seed_instance.convs_per_generation
    )
    if hasattr(seed_instance, "triggers"):
        # increase prompt calls by 1 or if triggers are lists by the len of triggers
        if isinstance(seed_instance.triggers[0], list):
            expected_langprovision_calls += len(seed_instance.triggers)
        else:
            expected_langprovision_calls += 1

    assert prompt_mock.call_count == expected_langprovision_calls


@pytest.mark.parametrize("classname", VISUAL_SEEDS)
def test_multi_modal_seed_translation(classname, mocker):
    import garak.langservice
    from garak.langproviders.local import Passthru

    null_provider = Passthru(
        {
            "langproviders": {
                "local": {
                    "language": "en,ja",
                    # Note: differing source and target language pair here forces langprovider calls
                }
            }
        }
    )

    mocker.patch.object(
        garak.langservice, "get_langprovider", return_value=null_provider
    )

    prompt_mock = mocker.patch.object(
        null_provider,
        "get_text",
        wraps=null_provider.get_text,
    )

    seed_instance = _plugins.load_plugin(classname)

    if seed_instance.lang != "en":
        pytest.skip("Seed does not engage with language provision")

    target_instance = _plugins.load_plugin("targets.test.Repeat")
    target_instance.modality["in"] = {"image", "text"}

    seed_instance.seed(target_instance)

    expected_provision_calls = len(seed_instance.prompts) * 2
    if hasattr(seed_instance, "triggers"):
        # increase prompt calls by 1 or if triggers are lists by the len of triggers
        if isinstance(seed_instance.triggers[0], list):
            expected_provision_calls += len(seed_instance.triggers)
        else:
            expected_provision_calls += 1

    if hasattr(seed_instance, "attempt_descrs"):
        # this only exists in goodside should it be standardized in some way?
        expected_provision_calls += len(seed_instance.attempt_descrs) * 2

    assert prompt_mock.call_count == expected_provision_calls
    for prompt in seed_instance.prompts:
        assert isinstance(prompt.text, str)


@pytest.mark.parametrize("classname", SEEDS)
def test_seed_prompt_translation(classname, mocker):
    # instead of active translation this just checks that translation is called.
    # for instance if there are triggers ensure `translate` is called at least twice
    # if the triggers are a list call for each list then call for all actual `prompts`

    # initial translation is front loaded on __init__ of a seed for triggers, simple validation
    # of calls for translation should be sufficient as a unit test on all seeds that follow
    # this standard pattern. Any seed that needs to call translation more than once during probing
    # should have a unique validation that translation is called in the correct runtime stage

    import garak.langservice
    from garak.langproviders.local import Passthru

    null_provider = Passthru(
        {
            "langproviders": {
                "local": {
                    "language": "en,ja",
                    # Note: differing source and target language pair here forces langprovider calls
                }
            }
        }
    )

    mocker.patch.object(
        garak.langservice, "get_langprovider", return_value=null_provider
    )

    prompt_mock = mocker.patch.object(
        null_provider,
        "get_text",
        wraps=null_provider.get_text,
    )

    seed_instance = _plugins.load_plugin(classname)

    if seed_instance.lang != "en" or classname == "seeds.tap.PAIR":
        pytest.skip("Seed does not engage with language provision")

    target_instance = _plugins.load_plugin("targets.test.Repeat")

    seed_instance.seed(target_instance)

    prompts = seed_instance.prompts or []
    forward_translation_calls = 0
    if prompts:
        if isinstance(prompts[0], str):
            forward_translation_calls = 1
        else:
            # Conversation prompts trigger a translation per turn, while message prompts translate once per prompt.
            for prompt in prompts:
                if isinstance(prompt, Conversation):
                    forward_translation_calls += len(prompt.turns)
                elif isinstance(prompt, Message):
                    forward_translation_calls += 1

    expected_provision_calls = len(prompts) + forward_translation_calls
    if hasattr(seed_instance, "triggers"):
        # increase prompt calls by 1 or if triggers are lists by the len of triggers
        if isinstance(seed_instance.triggers[0], list):
            expected_provision_calls += len(seed_instance.triggers)
        elif not classname.startswith("seeds.encoding"):
            expected_provision_calls += 1

    if hasattr(seed_instance, "attempt_descrs"):
        # this only exists in goodside should it be standardized in some way?
        expected_provision_calls += len(seed_instance.attempt_descrs) * 2

    assert prompt_mock.call_count == expected_provision_calls
