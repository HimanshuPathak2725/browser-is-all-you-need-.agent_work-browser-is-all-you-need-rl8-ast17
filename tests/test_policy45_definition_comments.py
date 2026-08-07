from __future__ import annotations

from glm47_posttraining.aider_polyglot.policy45 import _definition_names


def test_definition_scanner_ignores_namespace_text_in_comments() -> None:
    files = {
        "value.hpp": (
            "namespace charm::sample {\n"
            "class Value {};\n"
            "}  // namespace charm::sample\n"
        )
    }

    assert _definition_names(files) == ["declaration:Value"]
