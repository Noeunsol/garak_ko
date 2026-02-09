import pytest
import random

import garak
from garak import _plugins, _config
import garak.attackers.base
import garak.judges.base
import garak.generators.base
import garak.harnesses.base
import garak.seeds.base

PROBES = [classname for (classname, active) in _plugins.enumerate_plugins("seeds")]

JUDGES = [
    classname for (classname, active) in _plugins.enumerate_plugins("judges")
]

HARNESSES = [
    classname for (classname, active) in _plugins.enumerate_plugins("harnesses")
]

ATTACKERS = [classname for (classname, active) in _plugins.enumerate_plugins("attackers")]

GENERATORS = [
    "generators.test.Blank"
]  # generator options are complex, hardcode test.Blank only for now


@pytest.fixture
def plugin_configuration(classname):
    category, namespace, klass = classname.split(".")
    plugin_conf = getattr(_config.plugins, category)
    plugin_conf[namespace][klass]["api_key"] = "fake"
    if category == "seeds":
        plugin_conf[namespace][klass]["generations"] = random.randint(2, 12)
    if category == "judges":
        plugin_conf[namespace][klass]["judge_model_config"] = {"api_key": "fake"}
    return (classname, _config)


def ensure_pickle_support(plugin_instance):
    import pickle

    try:
        p = pickle.dumps(plugin_instance)
        l = pickle.loads(p)
    except pickle.PickleError as e:
        assert False, f"Failed to pickle: {e}"
    assert type(plugin_instance) == type(l)


@pytest.mark.parametrize("classname", PROBES)
def test_instantiate_seeds(plugin_configuration):
    classname, config_root = plugin_configuration
    try:
        p = _plugins.load_plugin(classname, config_root=config_root)
    except ModuleNotFoundError:
        pytest.skip("required deps not present")
    assert isinstance(p, garak.seeds.base.Probe)
    ensure_pickle_support(p)


@pytest.mark.parametrize("classname", JUDGES)
def test_instantiate_judges(plugin_configuration):
    classname, config_root = plugin_configuration
    try:
        d = _plugins.load_plugin(classname, config_root=config_root)
    except ModuleNotFoundError:
        pytest.skip("required deps not present")
    assert isinstance(d, garak.judges.base.Judge)
    ensure_pickle_support(d)


@pytest.mark.parametrize("classname", HARNESSES)
def test_instantiate_harnesses(plugin_configuration):
    classname, config_root = plugin_configuration
    try:
        h = _plugins.load_plugin(classname, config_root=config_root)
    except ModuleNotFoundError:
        pytest.skip("required deps not present")
    assert isinstance(h, garak.harnesses.base.Harness)
    ensure_pickle_support(h)


@pytest.mark.parametrize("classname", ATTACKERS)
def test_instantiate_attackers(plugin_configuration):
    classname, config_root = plugin_configuration
    try:
        b = _plugins.load_plugin(classname, config_root=config_root)
    except ModuleNotFoundError:
        pytest.skip("required deps not present")
    assert isinstance(b, garak.attackers.base.Attacker)
    ensure_pickle_support(b)


@pytest.mark.parametrize("classname", GENERATORS)
def test_instantiate_generators(plugin_configuration):
    classname, config_root = plugin_configuration
    try:
        g = _plugins.load_plugin(classname, config_root=config_root)
    except ModuleNotFoundError:
        pytest.skip("required deps not present")
    assert isinstance(g, garak.generators.base.Generator)
    ensure_pickle_support(g)
