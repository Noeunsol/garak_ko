import importlib
import os
import pytest

from garak.attempt import Message, Turn, Conversation
from garak.targets.langchain_serve import LangChainServeLLMTarget


@pytest.fixture
def set_env_vars():
    os.environ["LANGCHAIN_SERVE_URI"] = "http://127.0.0.1:8000"
    yield
    os.environ.pop("LANGCHAIN_SERVE_URI", None)


def test_validate_uri():
    assert LangChainServeLLMTarget._validate_uri("http://127.0.0.1:8000") == True
    assert LangChainServeLLMTarget._validate_uri("bad_uri") == False


@pytest.mark.usefixtures("set_env_vars")
def test_langchain_serve_target_initialization():
    target = LangChainServeLLMTarget()
    assert target.name == "127.0.0.1:8000"
    assert target.api_endpoint == "http://127.0.0.1:8000/invoke"


@pytest.mark.usefixtures("set_env_vars")
def test_langchain_serve_generation(requests_mock):
    requests_mock.post(
        "http://127.0.0.1:8000/invoke?config_hash=default",
        json={"output": ["Generated text"]},
    )
    target = LangChainServeLLMTarget()
    conv = Conversation([Turn("user", Message("Hello LangChain!"))])
    output = target._call_model(conv)
    assert len(output) == 1
    assert output[0] == Message("Generated text")


@pytest.mark.usefixtures("set_env_vars")
def test_error_handling(requests_mock):
    requests_mock.post(
        "http://127.0.0.1:8000/invoke?config_hash=default", status_code=500
    )
    target = LangChainServeLLMTarget()
    with pytest.raises(Exception):
        target._call_model(Message("This should raise an error"))


@pytest.mark.usefixtures("set_env_vars")
def test_bad_response_handling(requests_mock):
    requests_mock.post(
        "http://127.0.0.1:8000/invoke?config_hash=default", json={}, status_code=200
    )
    target = LangChainServeLLMTarget()
    conv = Conversation([Turn("user", Message("This should not find output"))])
    output = target._call_model(conv)
    assert output == [None]
