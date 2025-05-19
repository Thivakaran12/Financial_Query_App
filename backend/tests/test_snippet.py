import pytest
from backend.src.utils import extract_qtr_snippet

def test_extract_qtr_snippet_found():
    text = (
        "Intro line\n"
        "03 months to 31/12/2021   03 months to 30/09/2021\n"
        "Revenue 1 2\n"
        "COGS -1 -2\n"
        "\n"
        "Follow-up text"
    )
    snippet, header = extract_qtr_snippet(text)

    assert header == "03 months to 31/12/2021   03 months to 30/09/2021"
    # snippet should contain exactly the lines up to the blank
    assert "Revenue 1 2" in snippet
    assert "COGS -1 -2" in snippet
    assert "\n\n" not in snippet  # stops before the blank

def test_extract_qtr_snippet_not_found():
    text = "No relevant header here\nJust random text"
    snippet, header = extract_qtr_snippet(text)
    assert snippet == text
    assert header == ""
