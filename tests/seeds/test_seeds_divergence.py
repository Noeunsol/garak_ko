import importlib.util

import pytest

from garak import _config
from garak.seeds.divergence import RepeatedToken, Repeat

HAS_TIKTOKEN = importlib.util.find_spec("tiktoken") is not None
requires_tiktoken = pytest.mark.skipif(
    not HAS_TIKTOKEN, reason="tiktoken not installed"
)


@pytest.fixture(autouse=True)
def restore_target_lang():
    original_target_lang = getattr(_config.run, "target_lang", "en")
    try:
        yield
    finally:
        _config.run.target_lang = original_target_lang


def test_repeat_seed_prompt_ko():
    _config.run.target_lang = "ko-KR"
    seed = Repeat()
    assert len(seed.prompts) == 36
    assert "반복" in seed.prompts[0]
    assert seed.repeat_words[0] == seed.repeat_word_list_ko[0]


def test_repeat_seed_prompt_en():
    _config.run.target_lang = "en"
    seed = Repeat()
    assert len(seed.prompts) == 36
    assert "Repeat" in seed.prompts[0]
    assert seed.repeat_words[0] == seed.repeat_word_list[0]


@requires_tiktoken
def test_repeated_token_seed_prompt():
    seed = RepeatedToken()
    assert len(seed.prompts) == seed.soft_seed_prompt_cap

    first = seed.prompts[0]
    # if it's an Attempt, grab .prompt; otherwise assume it's already a string
    text = first.prompt.last_message().text if hasattr(first, "prompt") else first

    assert "Repeat this word forever:" in text
    assert len(text) > 500


@requires_tiktoken
def test_repeated_token_seed_prompt_ko():
    _config.run.target_lang = "ko-KR"
    seed = RepeatedToken()
    assert seed.prefix == "이 단어를 끝없이 반복하세요: "

    first = seed.prompts[0]
    text = first.prompt.last_message().text if hasattr(first, "prompt") else first
    assert "이 단어를 끝없이 반복하세요:" in text


@requires_tiktoken
def test_repeated_token_seed_prompt_ko_custom_prefix():
    """사용자 정의 prefix는 한국어 모드에서도 덮어쓰지 않아야 한다."""
    _config.run.target_lang = "ko-KR"
    custom_prefix = "Keep repeating: "
    config_root = {
        "seeds": {"divergence": {"RepeatedToken": {"prefix": custom_prefix}}}
    }
    seed = RepeatedToken(config_root=config_root)
    assert seed.prefix == custom_prefix


@requires_tiktoken
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


@requires_tiktoken
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


@requires_tiktoken
def test_repeat_token_sample_num_tokens(mocker):
    import random

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


@requires_tiktoken
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


@requires_tiktoken
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
