"""Placeholder parser: extracts and validates ``{{namespace.key}}`` tokens."""
from __future__ import annotations

import re
from dataclasses import dataclass


class PlaceholderSyntaxError(ValueError):
    """Raised when a placeholder cannot be parsed."""


@dataclass(frozen=True)
class Placeholder:
    namespace: str
    key: str

    @property
    def full_key(self) -> str:
        return f"{self.namespace}.{self.key}"

    def __str__(self) -> str:
        return f"{{{{{self.full_key}}}}}"


# Matches valid double-brace placeholders: {{namespace.rest}}
_VALID_PATTERN = re.compile(r"\{\{([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z0-9_.]+)\}\}")

# Detects suspicious single-brace patterns that look like placeholders:
#   {word.word}  but NOT CSS property blocks like  { color: red; }
_MALFORMED_PATTERN = re.compile(
    r"(?<!\{)\{([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z0-9_.]+)\}(?!\})"
)


class PlaceholderParser:
    """Utility for extracting and validating ``{{namespace.key}}`` placeholders."""

    def extract(self, html: str) -> list[Placeholder]:
        """Return deduplicated list of valid placeholders found in *html*."""
        seen: set[Placeholder] = set()
        result: list[Placeholder] = []
        for m in _VALID_PATTERN.finditer(html):
            p = Placeholder(namespace=m.group(1), key=m.group(2))
            if p not in seen:
                seen.add(p)
                result.append(p)
        return result

    def detect_malformed(self, html: str) -> list[str]:
        """Return raw strings matching single-brace placeholder patterns."""
        return [m.group(0) for m in _MALFORMED_PATTERN.finditer(html)]

    def validate_namespaces(
        self, html: str, known_namespaces: set[str]
    ) -> list[Placeholder]:
        """Return placeholders whose namespace is not in *known_namespaces*."""
        return [
            p for p in self.extract(html) if p.namespace not in known_namespaces
        ]
