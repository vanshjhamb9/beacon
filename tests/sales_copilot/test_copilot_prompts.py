from sales_copilot.prompting.versions import CURRENT_PROMPT_VERSION, PROMPT_REGISTRY, get_prompt_version


def test_prompt_versions_are_registered() -> None:
    assert CURRENT_PROMPT_VERSION in PROMPT_REGISTRY
    prompt = get_prompt_version(CURRENT_PROMPT_VERSION)
    assert prompt.temperature == 0.2
    assert "Never invent" in prompt.system_prompt or "never invent" in prompt.system_prompt.lower()
    assert "{evidence_block}" in prompt.user_prompt_template


def test_unknown_prompt_falls_back_to_current() -> None:
    prompt = get_prompt_version("does-not-exist")
    assert prompt.version == CURRENT_PROMPT_VERSION
