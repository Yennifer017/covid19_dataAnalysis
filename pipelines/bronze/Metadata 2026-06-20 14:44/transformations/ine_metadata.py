import dlt
from pyspark.sql import functions as F

S3_METADATA_PATH = "s3://ine-data/metadata/"

def load_csv(file_path: str, file_name: str):
    return (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(file_path)
        .withColumn("source_file", F.lit(file_name))
        .withColumn("bronze_processing_date", F.current_timestamp())
    )

def create_metadata_table(file_path: str, file_name: str, table_name: str):

    @dlt.table(
        name=table_name,
        comment=f"Metadata table generated from {file_name}"
    )
    def _table():
        return load_csv(file_path, file_name)

    return _table

files_df = spark.read.format("binaryFile").load(f"{S3_METADATA_PATH}*.csv")

file_list = [
    (row.path, row.path.split("/")[-1].replace(".csv", ""))
    for row in files_df.select("path").collect()
]


for path, file_name in file_list:
    table_name = f"dim_{file_name}"
    create_metadata_table(path, file_name, table_name)

