from discord_appkit.secrets import SecretStr, redact, redact_assignments


def test_secret_never_stringifies():
    secret = SecretStr("super-secret-user-token-value")
    assert str(secret) == "***"
    assert "super-secret" not in repr(secret)
    assert bool(secret) is True


def test_redact_strips_token_and_assignments():
    token = "super-secret-user-token-value"
    assert redact(f"failed with {token}", token) == "failed with ***"
    assert redact(f"failed with {token}", SecretStr(token)) == "failed with ***"
    assert redact_assignments("DISCORD_USER_TOKEN=abc.def.ghi") == "DISCORD_USER_TOKEN=***"
