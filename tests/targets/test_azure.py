import os
import pytest
import httpx

from garak.attempt import Message, Turn, Conversation
from garak.targets.azure import AzureOpenAITarget

DEFAULT_DEPLOYMENT_NAME = "gpt-4o-deployment-test"


@pytest.fixture
def set_fake_env(request) -> None:
    stored_env = {
        AzureOpenAITarget.ENV_VAR: os.getenv(AzureOpenAITarget.ENV_VAR, None),
        AzureOpenAITarget.MODEL_NAME_ENV_VAR: os.getenv(
            AzureOpenAITarget.MODEL_NAME_ENV_VAR, None
        ),
        AzureOpenAITarget.ENDPOINT_ENV_VAR: os.getenv(
            AzureOpenAITarget.ENDPOINT_ENV_VAR, None
        ),
    }

    def restore_env():
        for k, v in stored_env.items():
            if v is not None:
                os.environ[k] = v
            else:
                del os.environ[k]

    os.environ[AzureOpenAITarget.ENV_VAR] = "test_value"
    os.environ[AzureOpenAITarget.MODEL_NAME_ENV_VAR] = "gpt-4o"
    os.environ[AzureOpenAITarget.ENDPOINT_ENV_VAR] = "https://garak.example.com/"
    request.addfinalizer(restore_env)


@pytest.mark.usefixtures("set_fake_env")
def test_azureopenai_invalid_model_names():
    with pytest.raises(ValueError) as e_info:
        del os.environ[AzureOpenAITarget.MODEL_NAME_ENV_VAR]
        _ = AzureOpenAITarget(name="this is the deployment name")
    assert "environment variable is required" in str(e_info.value)
    with pytest.raises(ValueError) as e_info:
        os.environ[AzureOpenAITarget.MODEL_NAME_ENV_VAR] = "gpt-4o"
        _ = AzureOpenAITarget(name="")
    assert "name is required for" in str(e_info.value)
    with pytest.raises(ValueError) as e_info:
        os.environ[AzureOpenAITarget.MODEL_NAME_ENV_VAR] = "incorrect-model-name"
        _ = AzureOpenAITarget(name="this is the deployment name")
    assert "please add one!" in str(e_info.value)


@pytest.mark.usefixtures("set_fake_env")
@pytest.mark.respx(base_url="https://garak.example.com/")
def test_azureopenai_chat(respx_mock, openai_compat_mocks):
    mock_response = openai_compat_mocks["azure_chat_default_generations"]
    extended_request = "openai/deployments/"
    extended_request += DEFAULT_DEPLOYMENT_NAME
    extended_request += "/chat/completions?api-version="
    extended_request += AzureOpenAITarget.api_version
    respx_mock.post(extended_request).mock(
        return_value=httpx.Response(mock_response["code"], json=mock_response["json"])
    )
    target = AzureOpenAITarget(name=DEFAULT_DEPLOYMENT_NAME)
    assert target.name == DEFAULT_DEPLOYMENT_NAME
    assert target.target_name == os.environ[AzureOpenAITarget.MODEL_NAME_ENV_VAR]
    assert isinstance(target.max_tokens, int)
    target.max_tokens = 99
    assert target.max_tokens == 99
    target.temperature = 0.5
    assert target.temperature == 0.5
    conv = Conversation([Turn("user", Message("Hello OpenAI!"))])
    output = target.generate(conv, 1)
    assert len(output) == 1
    for item in output:
        assert isinstance(item, Message)
