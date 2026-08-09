"""
Run this from a Databricks notebook or the Databricks CLI-authenticated
environment to store your app secrets as Databricks secrets,
instead of hard-coding them anywhere in the app.

This script sets up:
- DATABASE_URL: Lakebase Postgres connection string
- MASSIVE_API_KEY: Massive.com API key

Usage (from a Databricks notebook cell):
    %run ./setup_secrets

Usage (from a local shell with the Databricks CLI configured):
    python setup_secrets.py
"""

from databricks.sdk import WorkspaceClient

SCOPE_NAME = "support_app_secrets"

w = WorkspaceClient()

# Create the scope if it doesn't already exist.
existing_scopes = [s.name for s in w.secrets.list_scopes()]
if SCOPE_NAME not in existing_scopes:
    w.secrets.create_scope(scope=SCOPE_NAME)
    print(f"✅ Created secret scope: {SCOPE_NAME}")
else:
    print(f"ℹ️  Secret scope '{SCOPE_NAME}' already exists, reusing it.")

print()

# Set up DATABASE_URL
print("=" * 60)
print("1️⃣  DATABASE_URL (Lakebase Postgres connection string)")
print("=" * 60)
database_url = input("Paste your Lakebase connection string: ").strip()

if database_url:
    w.secrets.put_secret(scope=SCOPE_NAME, key="DATABASE_URL", string_value=database_url)
    print("✅ Stored secret 'DATABASE_URL'")
else:
    print("⚠️  Skipped DATABASE_URL (empty input)")

print()

# Set up MASSIVE_API_KEY
print("=" * 60)
print("2️⃣  MASSIVE_API_KEY (Massive.com API key)")
print("=" * 60)
massive_api_key = input("Paste your Massive.com API key: ").strip()

if massive_api_key:
    w.secrets.put_secret(scope=SCOPE_NAME, key="MASSIVE_API_KEY", string_value=massive_api_key)
    print("✅ Stored secret 'MASSIVE_API_KEY'")
else:
    print("⚠️  Skipped MASSIVE_API_KEY (empty input)")

print()
print("=" * 60)
print("✅ Secret setup complete!")
print("=" * 60)

# List all secrets in the scope
secret_list = list(w.secrets.list_secrets(scope=SCOPE_NAME))
print(f"\nSecrets in scope '{SCOPE_NAME}':")
for s in secret_list:
    print(f"  • {s.key}")

print("\nℹ️  These secrets are already configured in app.yaml.")
print("   Redeploy your app to pick up the new secrets:")
print(f"   databricks apps deploy support-ticketing-app --source-code-path /Users/kottarathmuhsina@gmail.com/Ticketing_System")
