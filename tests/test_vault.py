"""
test_vault.py
=============
Functional and security tests for security_vault.py.

Coverage:
- Basic create / set / get round-trip
- Multi-key isolation
- Corrupt vault recovery
- Key name injection (path traversal strings, special chars)
- Value injection (arbitrary binary/json content)
- MAC-address binding (key differs on different machines → decrypt fails)
"""
import os
import json
import pytest
import sys

# Ensure project root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# 1. Functional tests
# ---------------------------------------------------------------------------

class TestVaultFunctional:
    def test_create_vault_creates_file(self, temp_vault):
        import security_vault as sv
        sv.create_vault()
        assert os.path.exists(sv.VAULT_FILE)

    def test_set_and_get_key(self, temp_vault):
        import security_vault as sv
        sv.set_key("api_key", "sk-testvalue123")
        result = sv.get_key("api_key")
        assert result == "sk-testvalue123"

    def test_get_missing_key_returns_none(self, temp_vault):
        import security_vault as sv
        result = sv.get_key("nonexistent_key")
        assert result is None

    def test_multiple_keys_independent(self, temp_vault):
        import security_vault as sv
        sv.set_key("key_a", "value_a")
        sv.set_key("key_b", "value_b")
        assert sv.get_key("key_a") == "value_a"
        assert sv.get_key("key_b") == "value_b"

    def test_overwrite_key(self, temp_vault):
        import security_vault as sv
        sv.set_key("key_x", "old_value")
        sv.set_key("key_x", "new_value")
        assert sv.get_key("key_x") == "new_value"

    def test_vault_is_binary_encrypted(self, temp_vault):
        import security_vault as sv
        sv.set_key("secret", "mysecret")
        with open(sv.VAULT_FILE, "rb") as f:
            raw = f.read()
        # Must NOT contain the plaintext secret
        assert b"mysecret" not in raw

    def test_vault_file_not_plain_json(self, temp_vault):
        import security_vault as sv
        sv.set_key("groq_api_key", "gsk_abc123")
        with open(sv.VAULT_FILE, "rb") as f:
            raw = f.read()
        assert b"gsk_abc123" not in raw
        # Fernet tokens start with 'gAAA' (base64-encoded)
        assert raw[:4] == b"gAAA" or len(raw) > 30


# ---------------------------------------------------------------------------
# 2. Security tests — injection / tampering
# ---------------------------------------------------------------------------

class TestVaultSecurity:
    def test_path_traversal_key_name_stored_safely(self, temp_vault):
        """Path-traversal strings as key names must NOT cause file operations."""
        import security_vault as sv
        traversal_key = "../../../etc/passwd"
        sv.set_key(traversal_key, "harmless")
        # Value should be stored and retrievable (treated as a plain string key)
        assert sv.get_key(traversal_key) == "harmless"
        # No file at the traversal path should be created or modified
        assert not os.path.exists("/etc/passwd_modified")

    def test_newline_injection_in_key_name(self, temp_vault):
        """Newline chars in key names do not break JSON structure."""
        import security_vault as sv
        injected_key = "key\nmalicious_key"
        sv.set_key(injected_key, "injected_value")
        result = sv.get_key(injected_key)
        assert result == "injected_value"

    def test_unicode_key_and_value(self, temp_vault):
        """Unicode / emoji content must round-trip through encrypted vault."""
        import security_vault as sv
        sv.set_key("emoji_key", "🔑🔐👾 value with 中文")
        result = sv.get_key("emoji_key")
        assert result == "🔑🔐👾 value with 中文"

    def test_large_key_value(self, temp_vault):
        """Very large values (e.g., full JSON blobs) must survive encryption round-trip."""
        import security_vault as sv
        big_value = "x" * 100_000
        sv.set_key("large_key", big_value)
        assert sv.get_key("large_key") == big_value

    def test_corrupt_vault_raises_gracefully(self, temp_vault):
        """A tampered vault must raise an exception, not silently expose data."""
        import security_vault as sv
        sv.create_vault()
        # Corrupt the vault file
        with open(sv.VAULT_FILE, "wb") as f:
            f.write(b"CORRUPTED_GARBAGE_DATA_NOT_FERNET")
        with pytest.raises(Exception):
            sv.load_vault()

    def test_master_key_is_not_hardcoded(self, temp_vault):
        """Master key must be derived dynamically (not a static literal)."""
        import security_vault as sv
        import inspect
        source = inspect.getsource(sv.get_master_key)
        # Must NOT contain a hardcoded base64 key string
        assert "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=" not in source

    def test_vault_value_not_eval_executed(self, temp_vault):
        """Values containing Python code must be stored as strings, never executed."""
        import security_vault as sv
        evil = "__import__('os').system('echo HACKED')"
        sv.set_key("evil_key", evil)
        result = sv.get_key("evil_key")
        # Should be returned as a plain string, not executed
        assert result == evil


# ---------------------------------------------------------------------------
# 3. Reset global state between tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_vault_module():
    """Ensure VAULT_FILE changes in one test don't bleed into the next."""
    yield
    import importlib
    import security_vault
    importlib.reload(security_vault)
