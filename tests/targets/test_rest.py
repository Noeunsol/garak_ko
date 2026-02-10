import json
import pytest

from garak import _config, _plugins
from garak.attempt import Message, Turn, Conversation
from garak.exception import BadTargetException
from garak.targets.rest import RestTarget

DEFAULT_NAME = "REST Test"
DEFAULT_URI = "https://www.wikidata.org/wiki/Q22971"
DEFAULT_TEXT_RESPONSE = "Here's your model response"


@pytest.fixture
def set_rest_config():
    _config.run.user_agent = "test user agent, garak.ai"
    _config.plugins.targets["rest"] = {}
    _config.plugins.targets["rest"]["RestTarget"] = {
        "name": DEFAULT_NAME,
        "uri": DEFAULT_URI,
        "api_key": "testing",
    }
    # excluded: req_template_json_object, response_json_field


@pytest.mark.usefixtures("set_rest_config")
def test_rest_target_initialization():
    target = RestTarget()
    assert target.name == DEFAULT_NAME
    assert target.uri == DEFAULT_URI


# plain text test
@pytest.mark.usefixtures("set_rest_config")
def test_plaintext_rest(requests_mock):
    requests_mock.post(
        "https://www.wikidata.org/wiki/Q22971",
        text=DEFAULT_TEXT_RESPONSE,
    )
    target = RestTarget()
    conv = Conversation([Turn("user", Message("sup REST"))])
    output = target._call_model(conv)
    assert output == [Message(DEFAULT_TEXT_RESPONSE)]


@pytest.mark.usefixtures("set_rest_config")
def test_json_rest_top_level(requests_mock):
    requests_mock.post(
        "https://www.wikidata.org/wiki/Q22971",
        text=json.dumps({"text": DEFAULT_TEXT_RESPONSE}),
    )
    _config.plugins.targets["rest"]["RestTarget"]["response_json"] = True
    _config.plugins.targets["rest"]["RestTarget"]["response_json_field"] = "text"
    target = RestTarget()
    print(target.response_json)
    print(target.response_json_field)
    conv = Conversation([Turn("user", Message("Who is Enabran Tain's son?"))])
    output = target._call_model(conv)
    assert output == [Message(DEFAULT_TEXT_RESPONSE)]


@pytest.mark.usefixtures("set_rest_config")
def test_json_rest_list(requests_mock):
    requests_mock.post(
        "https://www.wikidata.org/wiki/Q22971",
        text=json.dumps([DEFAULT_TEXT_RESPONSE]),
    )
    _config.plugins.targets["rest"]["RestTarget"]["response_json"] = True
    _config.plugins.targets["rest"]["RestTarget"]["response_json_field"] = "$"
    target = RestTarget()
    conv = Conversation([Turn("user", Message("Who is Enabran Tain's son?"))])
    output = target._call_model(conv)
    assert output == [Message(DEFAULT_TEXT_RESPONSE)]


@pytest.mark.usefixtures("set_rest_config")
def test_json_rest_deeper(requests_mock):
    requests_mock.post(
        "https://www.wikidata.org/wiki/Q22971",
        text=json.dumps(
            {
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": DEFAULT_TEXT_RESPONSE,
                        },
                    }
                ]
            }
        ),
    )
    _config.plugins.targets["rest"]["RestTarget"]["response_json"] = True
    _config.plugins.targets["rest"]["RestTarget"][
        "response_json_field"
    ] = "$.choices[*].message.content"
    target = RestTarget()
    conv = Conversation([Turn("user", Message("Who is Enabran Tain's son?"))])
    output = target._call_model(conv)
    assert output == [Message(DEFAULT_TEXT_RESPONSE)]


@pytest.mark.usefixtures("set_rest_config")
def test_rest_skip_code(requests_mock):
    target = _plugins.load_plugin(
        "targets.rest.RestTarget", config_root=_config
    )
    target.skip_codes = [200]
    requests_mock.post(
        DEFAULT_URI,
        text=json.dumps(
            {
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": DEFAULT_TEXT_RESPONSE,
                        },
                    }
                ]
            }
        ),
    )
    conv = Conversation([Turn("user", Message("Who is Enabran Tain's son?"))])
    output = target._call_model(conv)
    assert output == [None]


@pytest.mark.usefixtures("set_rest_config")
def test_rest_valid_proxy(mocker, requests_mock):
    test_proxies = {
        "http": "http://localhost:8080",
        "https": "https://localhost:8443",
    }
    _config.plugins.targets["rest"]["RestTarget"]["proxies"] = test_proxies
    target = _plugins.load_plugin(
        "targets.rest.RestTarget", config_root=_config
    )
    requests_mock.post(
        DEFAULT_URI,
        text=json.dumps(
            {
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": DEFAULT_TEXT_RESPONSE,
                        },
                    }
                ]
            }
        ),
    )
    mock_http_function = mocker.patch.object(
        target, "http_function", wraps=target.http_function
    )
    conv = Conversation([Turn("user", Message("Who is Enabran Tain's son?"))])
    target._call_model(conv)
    mock_http_function.assert_called_once()
    assert mock_http_function.call_args_list[0].kwargs["proxies"] == test_proxies


@pytest.mark.usefixtures("set_rest_config")
def test_rest_invalid_proxy(requests_mock):
    from garak.exception import GarakException

    test_proxies = [
        "http://localhost:8080",
        "https://localhost:8443",
    ]
    _config.plugins.targets["rest"]["RestTarget"]["proxies"] = test_proxies
    with pytest.raises(GarakException) as exc_info:
        _plugins.load_plugin("targets.rest.RestTarget", config_root=_config)
    assert "not in the required format" in str(exc_info.value)


@pytest.mark.usefixtures("set_rest_config")
@pytest.mark.parametrize("verify_ssl", (True, False, None))
def test_rest_ssl_suppression(mocker, requests_mock, verify_ssl):
    if verify_ssl is not None:
        _config.plugins.targets["rest"]["RestTarget"]["verify_ssl"] = verify_ssl
    else:
        verify_ssl = RestTarget.DEFAULT_PARAMS["verify_ssl"]
    target = _plugins.load_plugin(
        "targets.rest.RestTarget", config_root=_config
    )
    requests_mock.post(
        DEFAULT_URI,
        text=json.dumps(
            {
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": DEFAULT_TEXT_RESPONSE,
                        },
                    }
                ]
            }
        ),
    )
    mock_http_function = mocker.patch.object(
        target, "http_function", wraps=target.http_function
    )
    conv = Conversation([Turn("user", Message("Who is Enabran Tain's son?"))])
    target._call_model(conv)
    mock_http_function.assert_called_once()
    assert mock_http_function.call_args_list[0].kwargs["verify"] is verify_ssl


@pytest.mark.usefixtures("set_rest_config")
def test_rest_non_latin1():
    _config.plugins.targets["rest"]["RestTarget"][
        "uri"
    ] = "http://127.0.0.9"  # don't mock
    _config.plugins.targets["rest"]["RestTarget"]["headers"] = {
        "not_latin1": "😈😈😈"
    }
    target = _plugins.load_plugin(
        "targets.rest.RestTarget", config_root=_config
    )
    conv = Conversation([Turn("user", Message("summon a demon and bind it"))])
    with pytest.raises(BadTargetException):
        target._call_model(conv)
