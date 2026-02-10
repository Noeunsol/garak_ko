# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import httpx
import pytest

import openai

import garak.exception
from garak.attempt import Message, Turn, Conversation
from garak.targets.openai import OpenAITarget


@pytest.fixture
def set_fake_env(request) -> None:
    stored_env = os.getenv(OpenAITarget.ENV_VAR, None)

    def restore_env():
        if stored_env is not None:
            os.environ[OpenAITarget.ENV_VAR] = stored_env
        else:
            del os.environ[OpenAITarget.ENV_VAR]

    os.environ[OpenAITarget.ENV_VAR] = os.path.abspath(__file__)

    request.addfinalizer(restore_env)


def test_openai_version():
    assert openai.__version__.split(".")[0] == "1"  # expect openai module v1.x


@pytest.mark.usefixtures("set_fake_env")
@pytest.mark.respx(base_url="https://api.openai.com/v1")
def test_openai_invalid_model_names(respx_mock, openai_compat_mocks):
    mock_resp = openai_compat_mocks["models"]
    respx_mock.get("/models").mock(
        return_value=httpx.Response(mock_resp["code"], json=mock_resp["json"])
    )
    with pytest.raises(ValueError) as e_info:
        target = OpenAITarget(name="")
    assert "name is required for" in str(e_info.value)
    with pytest.raises(ValueError) as e_info:
        target = OpenAITarget(name="this is not a real model name")
    assert "please add one!" in str(e_info.value)


@pytest.mark.skipif(
    os.getenv(OpenAITarget.ENV_VAR, None) is None,
    reason=f"OpenAI API key is not set in {OpenAITarget.ENV_VAR}",
)
def test_openai_completion():
    target = OpenAITarget(name="gpt-3.5-turbo-instruct")
    assert target.name == "gpt-3.5-turbo-instruct"
    assert isinstance(target.max_tokens, int)
    target.max_tokens = 99
    assert target.max_tokens == 99
    target.temperature = 0.5
    assert target.temperature == 0.5
    output = target.generate(
        Conversation([Turn(role="user", content=Message("How could I possibly "))])
    )
    assert len(output) == 1  # expect 1 generation by default
    for item in output:
        assert isinstance(item, Message)


@pytest.mark.skipif(
    os.getenv(OpenAITarget.ENV_VAR, None) is None,
    reason=f"OpenAI API key is not set in {OpenAITarget.ENV_VAR}",
)
def test_openai_chat():
    target = OpenAITarget(name="gpt-3.5-turbo")
    assert target.name == "gpt-3.5-turbo"
    assert isinstance(target.max_tokens, int)
    target.max_tokens = 99
    assert target.max_tokens == 99
    target.temperature = 0.5
    assert target.temperature == 0.5
    output = target.generate(
        Conversation([Turn(role="user", content=Message("Hello OpenAI!"))])
    )
    assert len(output) == 1  # expect 1 generation by default
    for item in output:
        assert isinstance(item, Message)
    message_list = [
        {"role": "user", "content": "Hello OpenAI!"},
        {"role": "assistant", "content": "Hello! How can I help you today?"},
        {"role": "user", "content": "How do I write a sonnet?"},
    ]
    messages = Conversation([Turn.from_dict(msg) for msg in message_list])
    output = target.generate(messages, typecheck=False)
    assert len(output) == 1  # expect 1 generation by default
    for item in output:
        assert isinstance(item, Message)


@pytest.mark.usefixtures("set_fake_env")
def test_reasoning_switch():
    with pytest.raises(garak.exception.BadTargetException):
        target = OpenAITarget(
            name="o1-mini"
        )  # o1 models should use ReasoningTarget
