import re
import unicodedata
from pyspark.sql import functions as F
from pyspark.sql import SparkSession

# Get the active Spark session
spark = SparkSession.getActiveSession()

def to_snake_case(column_name):
    column_name = unicodedata.normalize("NFKD", column_name)
    column_name = column_name.encode("ascii", "ignore").decode("utf-8")
    column_name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", column_name)
    column_name = re.sub(r"[^a-zA-Z0-9]+", "_", column_name)
    column_name = re.sub(r"_+", "_", column_name)
    column_name = column_name.strip("_")

    return column_name.lower()


def validate_codes(df, col_name, dim_table, dim_code="code", critical=False):

    dim = spark.table(dim_table)

    total_count = df.count()

    # Detect invalid values
    invalid = df.join(
        dim,
        df[col_name] == dim[dim_code],
        "left_anti"
    )

    invalid_count = invalid.count()

    # porcentaje
    invalid_pct = (invalid_count / total_count) * 100 if total_count > 0 else 0

    print(f"{col_name}: {invalid_count} invalid values ({invalid_pct:.2f}%)")

    # If critical → remove invalid rows
    if critical:
        original_columns = df.columns
        df = df.join(
            dim,
            df[col_name] == dim[dim_code],
            "inner"
        ).select([df[c] for c in original_columns])
        return df, invalid

    # If not critical → set invalids to NULL
    valid_values = [row[dim_code] for row in dim.collect()]

    df = df.withColumn(
        col_name,
        F.when(
            F.col(col_name).isin(valid_values),
            F.col(col_name)
        ).otherwise(F.lit(None))
    )

    return df, invalid
