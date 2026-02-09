import pytest
from garak.seeds.divergence import RepeatedToken, Repeat, RepeatExtended


def test_repeated_token_seed_prompt():
    seed = RepeatedToken()
    assert len(seed.prompts) == seed.soft_seed_prompt_cap

    first = seed.prompts[0]
    # if it's an Attempt, grab .prompt; otherwise assume it's already a string
    text = first.prompt.last_message().text if hasattr(first, "prompt") else first

    assert "Repeat this word forever:" in text
    assert len(text) > 500


def test_repeated_token_seed_invalid_encoding():
    config_root = {
        "seeds": {
            "divergence": {
                "RepeatedToken": {
                    "encoding": "fake",
                }
            }
        }
    }
    with pytest.raises(ValueError) as exc_info:
        RepeatedToken(config_root=config_root)
    assert "Unknown encoding" in str(exc_info.value)
    assert config_root["seeds"]["divergence"]["RepeatedToken"]["encoding"] in str(
        exc_info.value
    )


def test_repeat_token_sample():
    config_root = {
        "seeds": {
            "divergence": {
                "RepeatedToken": {
                    "mode": "sample",
                }
            }
        }
    }
    seed = RepeatedToken(config_root=config_root)
    assert len(seed.prompts) == seed.soft_seed_prompt_cap


def test_repeat_token_sample_num_tokens(mocker):
    import random
    from garak.judges.divergence import RepeatedToken as judge

    mock_sample = mocker.patch.object(random, "sample", wraps=random.sample)

    config_root = {
        "seeds": {
            "divergence": {
                "RepeatedToken": {
                    "mode": "sample",
                    "num_tokens": 5,
                    "num_repeats": 1024,
                }
            }
        }
    }
    seed = RepeatedToken(config_root=config_root)
    assert len(seed.prompts) == seed.soft_seed_prompt_cap
    assert mock_sample.call_args[0][1] == 5


def test_repeat_token_sample_all():
    config_root = {
        "seeds": {
            "divergence": {
                "RepeatedToken": {
                    "mode": "sample",
                    "follow_prompt_cap": False,
                }
            }
        }
    }
    seed = RepeatedToken(config_root=config_root)
    assert (
        len(seed.prompts) > seed.soft_seed_prompt_cap
    ), "prompts should be well over the testing cap as there are at least 99482 tokens in the dataset"


@pytest.mark.parametrize(
    "encoding, test_token_string",
    [
        ("cl100k_base", " cubicocaust"),
        ("r50k_base", "mills Aram"),
    ],
)
def test_repeat_token_single(encoding, test_token_string):
    single_tokens = [41999, 39026]
    config_root = {
        "seeds": {
            "divergence": {
                "RepeatedToken": {
                    "mode": "single",
                    "encoding": encoding,
                    "max_repeats": 8000,
                    "num_tests": 8,
                    "single_tokens": single_tokens,
                }
            }
        }
    }
    seed = RepeatedToken(config_root=config_root)
    assert len(seed.prompts) == 9
    for prompt in seed.prompts:
        assert prompt.count(test_token_string) > 1
