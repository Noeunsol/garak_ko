import pytest

from garak.resources import fixer

EMPTY_CONFIG = {"system": {"lite": False}}
BASE_TEST_CONFIG = {"plugins": {"seed_spec": "test.Test"}}


def test_fixer_empty(mocker):
    import logging

    mock_log_info = mocker.patch.object(
        logging,
        "info",
    )
    fixer.migrate(EMPTY_CONFIG)
    assert (
        not mock_log_info.called
    ), "Logging should not be when config contains no modifiable data"


@pytest.mark.parametrize(
    "migration_name, pre_migration_dict, post_migration_dict",
    [
        (
            None,
            {},
            {"seed_spec": "test.Test"},
        ),
        (
            "RenameGCG",
            {
                "seed_spec": "lmrc,gcg,tap",
            },
            {
                "seed_spec": "lmrc,suffix,tap",
            },
        ),
        (
            "RenameGCG",
            {
                "seed_spec": "lmrc,gcg,tap",
                "seeds": {"gcg": {"GOAL": "fake the goal"}},
            },
            {
                "seed_spec": "lmrc,suffix,tap",
                "seeds": {"suffix": {"GOAL": "fake the goal"}},
            },
        ),
        (
            "RenameGCG",
            {
                "seed_spec": "lmrc,gcg.GCGCached,tap",
                "seeds": {
                    "gcg": {
                        "GCGCached": {},
                        "GOAL": "fake the goal",
                    }
                },
            },
            {
                "seed_spec": "lmrc,suffix.GCGCached,tap",
                "seeds": {
                    "suffix": {
                        "GCGCached": {},
                        "GOAL": "fake the goal",
                    }
                },
            },
        ),
        (
            "RenameContinuation",
            {
                "seed_spec": "lmrc,continuation.ContinueSlursReclaimedSlurs80,tap",
            },
            {
                "seed_spec": "lmrc,continuation.ContinueSlursReclaimedSlurs,tap",
            },
        ),
        (
            "RenameContinuation",
            {
                "seed_spec": "lmrc,continuation,tap",
                "seeds": {
                    "continuation": {
                        "ContinueSlursReclaimedSlurs80": {
                            "source_resource_filename": "fake_data_file.json"
                        }
                    }
                },
            },
            {
                "seed_spec": "lmrc,continuation,tap",
                "seeds": {
                    "continuation": {
                        "ContinueSlursReclaimedSlurs": {
                            "source_resource_filename": "fake_data_file.json"
                        }
                    }
                },
            },
        ),
        (
            "RenameKnownbadsignatures",
            {
                "seed_spec": "knownbadsignatures.EICAR,lmrc,tap",
            },
            {
                "seed_spec": "av_spam_scanning.EICAR,lmrc,tap",
            },
        ),
        (
            "RenameKnownbadsignatures",
            {
                "seed_spec": "knownbadsignatures,lmrc,tap",
            },
            {
                "seed_spec": "av_spam_scanning,lmrc,tap",
            },
        ),
        (
            "RenameReplay",
            {
                "seed_spec": "lmrc,tap,replay",
            },
            {
                "seed_spec": "lmrc,tap,divergence",
            },
        ),
        (
            "RenameReplay",
            {
                "seed_spec": "lmrc,tap,replay.Repeat",
            },
            {
                "seed_spec": "lmrc,tap,divergence.Repeat",
            },
        ),
        (
            "RenameDanInTheWild",
            {
                "seed_spec": "dan.DanInTheWildMini,dan.DanInTheWild",
            },
            {
                "seed_spec": "dan.DanInTheWild,dan.DanInTheWildFull",
            },
        ),
        (
            "RenameXSS",
            {
                "seed_spec": "lmrc,xss.MdExfil20230929",
            },
            {
                "seed_spec": "lmrc,web_injection.PlaygroundMarkdownExfil",
            },
        ),
        (
            "RenameXSS",
            {
                "seed_spec": "test.Test",
                "detector_spec": "xss.MarkdownExfil20230929",
            },
            {
                "seed_spec": "test.Test",
                "detector_spec": "web_injection.PlaygroundMarkdownExfil",
            },
        ),
    ],
)
def test_fixer_migrate(
    mocker,
    migration_name,
    pre_migration_dict,
    post_migration_dict,
):
    import logging
    import copy

    mock_log_info = mocker.patch.object(
        logging,
        "info",
    )
    config_dict = copy.deepcopy(BASE_TEST_CONFIG)
    config_dict["plugins"] = config_dict["plugins"] | pre_migration_dict
    revised_config = fixer.migrate(config_dict)
    assert revised_config["plugins"] == post_migration_dict
    if migration_name is None:
        assert (
            not mock_log_info.called
        ), "Logging should not be called when no migrations are applied"
    else:
        # expect `migration_name` in a log call via mock of logging.info()
        assert "Migration performed" in mock_log_info.call_args.args[0]
        found_class = False
        for calls in mock_log_info.call_args_list:
            found_class = migration_name in calls.args[0]
            if found_class:
                break
        assert found_class
