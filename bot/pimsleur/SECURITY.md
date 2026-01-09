# Security Features in Pimsleur Module

This document describes the security enhancements implemented to protect against prompt injection when processing user input.

## Input Validation System

### Design Principles

1. **Context-aware detection**: Only blocks explicit injection attempts, not normal vocabulary
2. **Minimal false positives**: Words like "forget", "ignore", "assume" are allowed since they're common in language learning
3. **Single validation point**: Validation happens at public API entry points to avoid redundancy

### Components

- `InputValidator` class: Main validation class with contextual pattern matching
- `validate_user_input()`: Convenience function for validation
- `sanitize_user_input()`: Function to remove potentially harmful patterns

### Validation Checks

1. **Length validation**: Input must not exceed 10,000 characters
2. **Empty check**: Input cannot be empty or whitespace-only
3. **Contextual injection detection**: Looks for specific injection phrases (not single words)

### Injection Patterns Detected

The system detects these **contextual** patterns (not single words):

- "ignore all previous instructions"
- "disregard prior prompts"
- "forget earlier instructions"
- "you are now a new system/assistant"
- "your new role is"
- "reveal your system prompt"
- "show me your instructions"
- "respond only with the word/text/phrase"
- "output exactly/only/just"
- Delimiter injection: `</system>`, `<user>`, `[system]`, etc.

### What is NOT Blocked

Normal language learning content like:
- "I forget my keys" (normal vocabulary)
- "Please ignore the noise" (contextual usage)
- "Let's assume you understand" (normal phrase)
- "Pretend you are a tourist" (roleplay scenario)

## Integration Points

Validation is applied at public API entry points only:

1. `PimsleurLessonGenerator.generate_custom_lesson_script()` - Validates user text
2. `TextAnalyzer.analyze()` - Validates text before analysis

Internal functions (like `get_custom_lesson_prompt()`) do not validate - they trust that input was validated at the entry point.

## Usage Examples

### Basic Validation
```python
from bot.pimsleur import validate_user_input

text = "User provided text"
is_valid, error_msg = validate_user_input(text)

if not is_valid:
    raise ValueError(f"Invalid input: {error_msg}")
```

### Text Sanitization
```python
from bot.pimsleur import sanitize_user_input

# Removes system delimiters like </system>, <user>, etc.
sanitized_text = sanitize_user_input(user_input)
```

## Error Handling

When validation fails, functions raise `ValueError` with a generic message "Input contains potentially unsafe content" to avoid leaking detection patterns.

## Running Tests

```bash
# Unit tests
python -m pytest tests/pimsleur/test_input_validator.py -v

# Integration tests
python -m pytest tests/pimsleur/test_security_integration.py -v
```
