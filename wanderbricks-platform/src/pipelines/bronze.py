"""WanderBricks Platform — Bronze layer.

Raw streaming ingestion from samples.wanderbricks into bronze_* streaming tables.
Each table is a near-verbatim copy of the source with an added _ingested_at
timestamp. Primary key expectations catch obviously malformed rows early.

Metadata-driven: the BRONZE_TABLES dict below is the single source of truth
for which source tables are ingested and their natural key(s). Adding a new
table to bronze is a one-line config addition, not a new function.
"""

from pyspark import pipelines as dp
from pyspark.sql.functions import current_timestamp

SOURCE_CATALOG = "samples"
SOURCE_SCHEMA = "wanderbricks"

# source_table -> list of primary key column(s); composite keys use multiple columns.
BRONZE_TABLES = {
    "properties": ["property_id"],
    "bookings": ["booking_id"],
    "reviews": ["review_id"],
    "users": ["user_id"],
    "hosts": ["host_id"],
    "destinations": ["destination_id"],
    "payments": ["payment_id"],
    "countries": ["country"],
    "amenities": ["amenity_id"],
    "property_amenities": ["property_id", "amenity_id"],
    "property_images": ["image_id"],
}


def _create_bronze_table(table_name: str, pk_columns: list[str]) -> None:
    """Register a bronze streaming table for a single source table.

    table_name / pk_columns are captured as default arguments so each
    invocation of this function binds its own values (avoids the classic
    Python for-loop late-binding-closure bug with decorated functions).
    """
    source_fqn = f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.{table_name}"
    target_name = f"bronze_{table_name}"
    expectations = {f"{table_name}_{pk}_not_null": f"{pk} IS NOT NULL" for pk in pk_columns}

    @dp.table(
        name=target_name,
        comment=(
            f"Bronze: raw streaming ingestion from {source_fqn}. "
            "Preserves all source columns; adds _ingested_at only."
        ),
    )
    @dp.expect_all(expectations)
    def _bronze_flow(source_fqn=source_fqn):
        return spark.readStream.table(source_fqn).withColumn(
            "_ingested_at", current_timestamp()
        )


for _table_name, _pk_columns in BRONZE_TABLES.items():
    _create_bronze_table(_table_name, _pk_columns)
