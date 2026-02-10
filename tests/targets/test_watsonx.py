from garak.targets.watsonx import WatsonXTarget
import os
import pytest
import requests_mock


DEFAULT_DEPLOYMENT_NAME = "ibm/granite-3-8b-instruct"


@pytest.fixture
def set_fake_env(request) -> None:
    stored_env = {
        WatsonXTarget.ENV_VAR: os.getenv(WatsonXTarget.ENV_VAR, None),
        WatsonXTarget.PID_ENV_VAR: os.getenv(WatsonXTarget.PID_ENV_VAR, None),
        WatsonXTarget.URI_ENV_VAR: os.getenv(WatsonXTarget.URI_ENV_VAR, None),
        WatsonXTarget.DID_ENV_VAR: os.getenv(WatsonXTarget.DID_ENV_VAR, None),
    }

    def restore_env():
        for k, v in stored_env.items():
            if v is not None:
                os.environ[k] = v
            else:
                del os.environ[k]

    os.environ[WatsonXTarget.ENV_VAR] = "XXXXXXXXXXXXX"
    os.environ[WatsonXTarget.PID_ENV_VAR] = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
    os.environ[WatsonXTarget.DID_ENV_VAR] = "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
    os.environ[WatsonXTarget.URI_ENV_VAR] = "https://garak.example.com/"
    request.addfinalizer(restore_env)


@pytest.mark.usefixtures("set_fake_env")
def test_bearer_token(watsonx_compat_mocks):
    with requests_mock.Mocker() as m:
        mock_response = watsonx_compat_mocks["watsonx_bearer_token"]

        extended_request = "identity/token"

        m.post(
            "https://garak.example.com/" + extended_request, json=mock_response["json"]
        )

        granite_llm = WatsonXTarget(DEFAULT_DEPLOYMENT_NAME)
        token = granite_llm._set_bearer_token(
            iam_url="https://garak.example.com/identity/token"
        )

        assert granite_llm.bearer_token == (
            "Bearer " + mock_response["json"]["access_token"]
        )


@pytest.mark.usefixtures("set_fake_env")
def test_project(watsonx_compat_mocks):
    with requests_mock.Mocker() as m:
        mock_response = watsonx_compat_mocks["watsonx_generation"]
        extended_request = "/ml/v1/text/generation?version=2023-05-29"

        m.post(
            "https://garak.example.com/" + extended_request, json=mock_response["json"]
        )

        granite_llm = WatsonXTarget(DEFAULT_DEPLOYMENT_NAME)
        response = granite_llm._generate_with_project("What is this?")

        assert granite_llm.name == response["model_id"]


@pytest.mark.usefixtures("set_fake_env")
def test_deployment(watsonx_compat_mocks):
    with requests_mock.Mocker() as m:
        mock_response = watsonx_compat_mocks["watsonx_generation"]
        extended_request = "/ml/v1/deployments/"
        extended_request += "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
        extended_request += "/text/generation?version=2023-05-29"

        m.post(
            "https://garak.example.com/" + extended_request, json=mock_response["json"]
        )

        granite_llm = WatsonXTarget(DEFAULT_DEPLOYMENT_NAME)
        response = granite_llm._generate_with_deployment("What is this?")

        assert granite_llm.name == response["model_id"]
