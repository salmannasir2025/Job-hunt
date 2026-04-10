import sys
from security_vault import set_key

def main():
    """
    Usage:
    python vault_cli.py set <key_name> <value>
    
    Example:
    python vault_cli.py set openai_api_key sk-12345...
    python vault_cli.py set groq_api_key gsk_abc123...
    """
    if len(sys.argv) < 4:
        print("Usage: python vault_cli.py set <key_name> <value>")
        sys.exit(1)

    cmd = sys.argv[1]
    key_name = sys.argv[2]
    value = sys.argv[3]

    if cmd == "set":
        set_key(key_name, value)
        print(f"✅ Successfully saved '{key_name}' to the secure vault.")
    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()