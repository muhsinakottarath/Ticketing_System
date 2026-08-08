"""
Run this from a Databricks notebook or the Databricks CLI-authenticated
environment to store your Lakebase connection string as a Databricks secret,
instead of hard-coding it anywhere in the app.

Usage (from a Databricks notebook cell):
    %run ./setup_secrets

Usage (from a local shell with the Databricks CLI configured):
    python setup_secrets.py
"""

from databricks.sdk import WorkspaceClient

SCOPE_NAME = "support_app_secrets"
SECRET_KEY = "DATABASE_URL"

w = WorkspaceClient()

# Create the scope if it doesn't already exist.
existing_scopes = [s.name for s in w.secrets.list_scopes()]
if SCOPE_NAME not in existing_scopes:
    w.secrets.create_scope(scope=SCOPE_NAME)
    print(f"Created secret scope: {SCOPE_NAME}")
else:
    print(f"Secret scope '{SCOPE_NAME}' already exists, reusing it.")

database_url = input("Paste your Lakebase Postgres connection string: ").strip()

w.secrets.put_secret(scope=SCOPE_NAME, key=SECRET_KEY, string_value=database_url)
print(f"Stored secret '{SECRET_KEY}' in scope '{SCOPE_NAME}'.")
print("Next: in your Databricks App -> Edit -> Add resource -> Secret,")
print(f"map scope='{SCOPE_NAME}', key='{SECRET_KEY}' to env var name 'DATABASE_URL'.")
