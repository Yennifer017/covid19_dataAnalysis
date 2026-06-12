import dlt
from pyspark.sql import functions as F
import pandas as pd
import io
import re

S3_BUCKET_PATH = "s3://ine-data/"


def load_and_clean_excel(file_name: str):
    full_path = f"{S3_BUCKET_PATH}{file_name}"
    
    binary_df = spark.read.format("binaryFile").load(full_path)
    raw_binary_content = binary_df.select("content").collect()[0][0]
    
    pandas_df = pd.read_excel(io.BytesIO(raw_binary_content), engine="openpyxl")
    
    pandas_df.columns = [re.sub(r'[ ,;{}()\n\t=]', '_', str(col)) for col in pandas_df.columns]
    
    spark_df = spark.createDataFrame(pandas_df)
    return (spark_df
            .withColumn("bronze_processing_date", F.current_timestamp())
            .withColumn("source_file", F.lit(file_name)))


@dlt.table(name="ine_defunciones_2018", comment="Defunciones año 2018")
def ine_defunciones_2018():
    return load_and_clean_excel("defunciones-2018.xlsx")

@dlt.table(name="ine_defunciones_2019", comment="Defunciones año 2019")
def ine_defunciones_2019():
    return load_and_clean_excel("defunciones-2019.xlsx")

@dlt.table(name="ine_defunciones_2020", comment="Defunciones año 2020")
def ine_defunciones_2020():
    return load_and_clean_excel("defunciones-2020.xlsx")

@dlt.table(name="ine_defunciones_2021", comment="Defunciones año 2021")
def ine_defunciones_2021():
    return load_and_clean_excel("defunciones-2021.xlsx")

@dlt.table(name="ine_defunciones_2022", comment="Defunciones año 2022")
def ine_defunciones_2022():
    return load_and_clean_excel("defunciones-2022.xlsx")

@dlt.table(name="ine_defunciones_2023", comment="Defunciones año 2023")
def ine_defunciones_2023():
    return load_and_clean_excel("defunciones-2023.xlsx")

@dlt.table(name="ine_defunciones_2024", comment="Defunciones año 2024")
def ine_defunciones_2024():
    return load_and_clean_excel("defunciones-2024.xlsx")