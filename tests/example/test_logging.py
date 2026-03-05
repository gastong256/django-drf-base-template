from config.logging import _redact_value


def test_redacts_sensitive_fields_in_dict() -> None:
    payload = {
        "username": "alice",
        "password": "secret",
        "nested": {"api_key": "xyz", "value": 123},
    }

    redacted = _redact_value(payload)

    assert redacted["username"] == "alice"
    assert redacted["password"] == "[REDACTED]"
    assert redacted["nested"]["api_key"] == "[REDACTED]"
    assert redacted["nested"]["value"] == 123


def test_redacts_bearer_tokens_in_strings() -> None:
    raw = "Authorization: Bearer abc.def.ghi"
    redacted = _redact_value(raw, key_hint="message")
    assert "abc.def.ghi" not in redacted
    assert "Bearer [REDACTED]" in redacted
