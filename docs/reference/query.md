# API Reference: Query Construction

## NewsQuery

Immutable query constructor for Google News search expressions.

```python
class NewsQuery:
    def __init__(
        self,
        text: str = "",
        *,
        exact_phrase: Optional[str] = None,
        any_words: Optional[List[str]] = None,
        exclude_words: Optional[List[str]] = None,
        in_title: Optional[str] = None,
    ): ...

    def build(self) -> str: ...
```

### Parameters

- `text` (`str`): Base search term or query prefix.
- `exact_phrase` (`Optional[str]`): Phrase enclosed in quotes (`"..."`).
- `any_words` (`Optional[List[str]]`): List of terms joined with Boolean `OR` (`(term1 OR term2)`).
- `exclude_words` (`Optional[List[str]]`): List of negative terms prefixed with `-` (`-term`).
- `in_title` (`Optional[str]`): Term targeted specifically to article titles (`intitle:"..."`).

### Validation

At least one positive search constraint (`text`, `exact_phrase`, `any_words`, or `in_title`)
must be supplied, otherwise a `ValidationError(field="query")` is raised.
