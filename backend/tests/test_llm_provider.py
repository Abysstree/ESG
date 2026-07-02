from app.llm.providers import get_llm_status


def test_default_llm_status_is_mock() -> None:
    status = get_llm_status()

    assert status["provider"] == "mock"
    assert status["configured"] is True
