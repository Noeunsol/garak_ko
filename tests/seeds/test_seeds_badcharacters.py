import pytest

from garak import _config, _plugins
from garak._plugins import PluginProvider
import garak.seeds.badchars as badchars
from garak.seeds.badchars import DEFAULT_INVISIBLE, BIDI_CONTROLS


PLUGIN_NAME = "seeds.badchars.BadCharacters"


@pytest.fixture(autouse=True)
def restore_target_lang():
    original_target_lang = getattr(_config.run, "target_lang", "en")
    try:
        yield
    finally:
        _config.run.target_lang = original_target_lang
        PluginProvider.clear_cache()


def _load_badcharacters(custom_config: dict | None = None):
    PluginProvider.clear_cache()
    cfg = {"seeds": {"badchars": {"BadCharacters": custom_config or {}}}}
    return _plugins.load_plugin(PLUGIN_NAME, config_root=cfg)


def test_badcharacters_generates_all_categories():
    original_cap = _config.run.soft_seed_prompt_cap
    _config.run.soft_seed_prompt_cap = None
    try:
        seed = _load_badcharacters(
            {
                "perturbation_budget": 1,
                "max_position_candidates": 2,
                "max_reorder_candidates": 2,
                "max_ascii_variants": 4,
                "follow_prompt_cap": False,
            }
        )
    finally:
        _config.run.soft_seed_prompt_cap = original_cap

    categories = {conv.notes.get("bad_character_category") for conv in seed.prompts}
    assert {"invisible", "homoglyph", "reordering", "deletion"}.issubset(categories)

    for conv in seed.prompts:
        assert isinstance(conv.notes.get("operations"), dict)
        assert conv.notes.get("source_payload_index") is not None
        assert conv.notes.get("source_payload_excerpt")


def test_badcharacters_respects_prompt_cap():
    original_cap = _config.run.soft_seed_prompt_cap
    _config.run.soft_seed_prompt_cap = 5
    try:
        seed = _load_badcharacters(
            {
                "perturbation_budget": 1,
                "max_position_candidates": 2,
                "max_reorder_candidates": 2,
                "max_ascii_variants": 3,
            }
        )
    finally:
        _config.run.soft_seed_prompt_cap = original_cap

    assert len(seed.prompts) <= 5

    categories = {conv.notes.get("bad_character_category") for conv in seed.prompts}
    assert categories  # non-empty after downsampling


def test_badcharacters_inserts_expected_characters():
    seed = _load_badcharacters(
        {
            "perturbation_budget": 1,
            "max_position_candidates": 2,
            "max_reorder_candidates": 2,
            "max_ascii_variants": 2,
            "follow_prompt_cap": False,
        }
    )

    samples = {}
    for conv in seed.prompts:
        category = conv.notes.get("bad_character_category")
        samples.setdefault(category, conv)

    assert {"invisible", "homoglyph", "reordering", "deletion"}.issubset(samples.keys())

    invisible_text = samples["invisible"].turns[0].content.text
    assert any(ch in DEFAULT_INVISIBLE for ch in invisible_text)

    homoglyph_conv = samples["homoglyph"]
    homoglyph_text = homoglyph_conv.turns[0].content.text
    replacements = homoglyph_conv.notes["operations"]["replacements"]
    for replacement in replacements:
        assert replacement in homoglyph_text

    reorder_text = samples["reordering"].turns[0].content.text
    assert any(ctrl in reorder_text for ctrl in BIDI_CONTROLS.values())

    deletion_conv = samples["deletion"]
    deletion_text = deletion_conv.turns[0].content.text
    ascii_codes = deletion_conv.notes["operations"]["ascii_codes"]
    for code in ascii_codes:
        seq = f"{chr(code)}\b"
        assert seq in deletion_text


def test_badcharacters_localized_lang_and_payload_ko():
    _config.run.target_lang = "ko"
    seed = _load_badcharacters(
        {
            "perturbation_budget": 1,
            "max_position_candidates": 2,
            "max_reorder_candidates": 2,
            "max_ascii_variants": 2,
            "follow_prompt_cap": False,
        }
    )

    assert seed.lang == "ko"
    assert seed._source_payloads[0].startswith("파라티온")
    assert seed.prompts[0].turns[0].content.lang == "ko"


def test_badcharacters_localized_lang_and_payload_en():
    _config.run.target_lang = "en"
    seed = _load_badcharacters(
        {
            "perturbation_budget": 1,
            "max_position_candidates": 2,
            "max_reorder_candidates": 2,
            "max_ascii_variants": 2,
            "follow_prompt_cap": False,
        }
    )

    assert seed.lang == "en"
    assert seed._source_payloads[0].startswith("Give detailed")
    assert seed.prompts[0].turns[0].content.lang == "en"


def test_homoglyph_candidates_prefers_intentional_ko():
    ko_candidates = badchars._homoglyph_file_candidates("ko")
    assert ko_candidates[0].name == "intentional_ko.txt"
    assert ko_candidates[-1].name == "intentional.txt"

    en_candidates = badchars._homoglyph_file_candidates("en")
    assert [path.name for path in en_candidates] == ["intentional.txt"]
