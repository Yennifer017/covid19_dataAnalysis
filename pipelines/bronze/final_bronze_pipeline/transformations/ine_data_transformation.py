import dlt
from pyspark.sql import functions as F
import pandas as pd
import io
import re

S3_BUCKET_PATH = "s3://ine-data/"

def load_and_clean_single_excel(file_path: str, file_name: str):
    """
    Reads a binary file from S3, processes it with Pandas to clean 
    column names, and returns it as a Spark DataFrame.
    """
    binary_df = spark.read.format("binaryFile").load(file_path)
    raw_binary_content = binary_df.select("content").collect()[0][0]
    
    pandas_df = pd.read_excel(io.BytesIO(raw_binary_content), engine="openpyxl")
    pandas_df.columns = [re.sub(r'[ ,;{}()\n\t=]', '_', str(col)) for col in pandas_df.columns]
    
    spark_df = spark.createDataFrame(pandas_df)
    return spark_df.withColumn("source_file", F.lit(file_name))


@dlt.table(
    name="ine_deaths",
    comment="Unified table of death records extracted from S3",
    partition_cols=["source_file"] 
)
def bronze_ine_deaths():
    file_pattern = f"{S3_BUCKET_PATH}defunciones-*.xlsx"
    
    try:
        found_files = spark.read.format("binaryFile").load(file_pattern)
        path_list = [row.path for row in found_files.select("path").collect()]
    except Exception as e:
        raise Exception(f"No files matching the pattern were found in S3: {e}")
    
    if not path_list:
        raise ValueError("The list of files to process is empty.")

    processed_dfs = []
    
    for full_path in path_list:
        file_name = full_path.split("/")[-1]
        
        spark_df = load_and_clean_single_excel(full_path, file_name)
        processed_dfs.append(spark_df)

    consolidated_df = processed_dfs[0]
    for next_df in processed_dfs[1:]:
        consolidated_df = consolidated_df.unionByName(next_df, allowMissingColumns=True)
        
    return consolidated_df.withColumn("bronze_processing_date", F.current_timestamp())