from databricks.sdk import WorkspaceClient 
w = WorkspaceClient() 
for s in w.secrets.list_scopes(): 
    print(s.name) 

for secret in w.secrets.list_secrets(scope="database"):
    print(secret.key)

for secret in w.secrets.list_secrets(scope="massive"):
    print(secret.key)