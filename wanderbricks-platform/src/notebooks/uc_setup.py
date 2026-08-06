# Databricks notebook source
# DBTITLE 1,Install latest Databricks SDK
# MAGIC %pip install --upgrade databricks-sdk
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Widgets
dbutils.widgets.text("catalog", "", "Catalog")
dbutils.widgets.text("schema", "", "Schema")
dbutils.widgets.text("lakebase_project_id", "", "Lakebase Project ID")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
lakebase_project_id = dbutils.widgets.get("lakebase_project_id")

# COMMAND ----------

# DBTITLE 1,Create UC secrets for Lakebase connection
# MAGIC %sql
# MAGIC -- UC secrets live at catalog.schema.secret_name
# MAGIC -- Governed by standard UC privileges (READ SECRET, WRITE SECRET, REFERENCE SECRET)
# MAGIC -- Placeholder secrets — values will be updated after Lakebase provisioning
# MAGIC
# MAGIC CREATE SECRET IF NOT EXISTS ${catalog}.${schema}.lakebase_host
# MAGIC   WITH VALUE 'placeholder'
# MAGIC   COMMENT 'Lakebase PostgreSQL endpoint hostname';
# MAGIC
# MAGIC CREATE SECRET IF NOT EXISTS ${catalog}.${schema}.lakebase_db
# MAGIC   WITH VALUE 'placeholder'
# MAGIC   COMMENT 'Lakebase PostgreSQL database name';

# COMMAND ----------

# DBTITLE 1,Store Lakebase connection info in UC secrets
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Retrieve the Lakebase endpoint and update UC secrets with real values
resource_path = f"projects/{lakebase_project_id}/branches/production"
endpoints = list(w.postgres.list_endpoints(parent=resource_path))

if endpoints:
    endpoint = endpoints[0]
    host = endpoint.spec.hostname
    db_name = endpoint.spec.database_name

    # Update UC secrets with actual Lakebase connection values
    spark.sql(f"""
        ALTER SECRET `{catalog}`.`{schema}`.lakebase_host
        SET VALUE = '{host}'
    """)
    spark.sql(f"""
        ALTER SECRET `{catalog}`.`{schema}`.lakebase_db
        SET VALUE = '{db_name}'
    """)
    print(f"Updated UC secrets in {catalog}.{schema}")
    print(f"  lakebase_host = {host}")
    print(f"  lakebase_db   = {db_name}")
else:
    print("No endpoints found yet - Lakebase may still be provisioning")
    print("Re-run this cell after the project finishes provisioning")

# COMMAND ----------

# DBTITLE 1,Summary
print("\n" + "="*60)
print("WanderBricks UC Setup Complete")
print("="*60)
print(f"  Catalog:          {catalog}")
print(f"  Schema:           {schema}")
print(f"  Lakebase Project: {lakebase_project_id}")
print(f"  UC Secrets:       {catalog}.{schema}.lakebase_host")
print(f"                    {catalog}.{schema}.lakebase_db")
print("="*60)