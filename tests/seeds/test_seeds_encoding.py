# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pytest
import garak.seeds.encoding
from garak import _plugins
from garak.seeds.encoding import InjectAtbash

ENCODING_SEEDS = [
    classname
    for (classname, active) in _plugins.enumerate_plugins("seeds")
    if classname.startswith("seeds.encoding")
]

# Seeds known to include the trigger in final prompts
CLEAR_TRIGGER_SEEDS = [
    "seeds.encoding.InjectMime",
    "seeds.encoding.InjectQP",
]


@pytest.mark.parametrize("classname", ENCODING_SEEDS)
def test_encoding_len_cap(classname):
    p = _plugins.load_plugin(classname)
    num_payloads = len(p._payloads)
    num_templates = len(garak.seeds.encoding.TEMPLATES)
    num_encoders = len(p.encoding_funcs)
    # prompts are a unique set and some functions may generate duplicate, hence "<=" test
    assert len(p.prompts) <= num_payloads * num_templates * num_encoders


@pytest.mark.parametrize("classname", ENCODING_SEEDS)
def test_encoding_prompt_trigger_match(classname):
    p = _plugins.load_plugin(classname)
    assert len(p.prompts) == len(p.triggers)


@pytest.mark.parametrize(
    "classname",
    [classname for classname in ENCODING_SEEDS if not CLEAR_TRIGGER_SEEDS],
)
def test_encoding_triggers_not_in_prompts(classname):
    p = _plugins.load_plugin(classname)
    for i in range(len(p.triggers)):
        assert p.triggers[i] not in p.prompts[i]


@pytest.mark.parametrize("classname", ENCODING_SEEDS)
def test_encoding_prompt_cap(classname):
    import random
    from garak import _config

    rand_cap = random.randint(1, 20)
    _config.run.soft_seed_prompt_cap = rand_cap
    p = _plugins.load_plugin(classname)
    assert len(p.prompts) <= rand_cap


@pytest.mark.parametrize("classname", ENCODING_SEEDS)
def test_encoding_suppress_prompt_cap(classname):
    import random
    from garak import _config

    rand_cap = random.randint(1, 5)
    _config.run.soft_seed_prompt_cap = rand_cap
    instance_config = {
        "seeds": {
            "encoding": {
                classname.split(".")[-1]: {
                    "follow_prompt_cap": False,
                }
            }
        }
    }
    p = _plugins.load_plugin(classname, config_root=instance_config)
    assert len(p.prompts) >= rand_cap

@pytest.mark.parametrize("plain, expected", [
    ("abc", "zyx"),                       
    ("ABC", "ZYX"),                       
    ("Hello, World!", "Svool, Dliow!"),   
    ("1234!?", "1234!?"),                 
])
def test_atbash_function(plain, expected):
    # Tests all 4 cases of Atbash Encoding
    # Uppercase, Lowercase, Mixed case, and Numbers/Special characters.

    encoder = InjectAtbash.atbash  # staticmethod reference
    result = encoder(plain.encode()).decode()
    assert result == expected
