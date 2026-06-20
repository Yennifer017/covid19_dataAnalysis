import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
import unicodedata
import importlib
from pyspark.sql.functions import col, sum, when, upper, trim
from pyspark.sql import functions as F
from pyspark import pipelines as dp

# Import functions from utilities (handling spaces in filename)
utilities_module = importlib.import_module("utilities.Functions 2026-06-20 16:20:49")
to_snake_case = utilities_module.to_snake_case
validate_codes = utilities_module.validate_codes

def basic_cleaning(df):
    df = df.toDF(*[to_snake_case(col) for col in df.columns])
    unique_rows = df.dropDuplicates().count()

    df = df.fillna({
        "Escodif": 99,
        "Ciuodif": 99
    })

    df = df.withColumn(
        "Caudef",
        upper(trim("Caudef"))
    )

    df = df.withColumn(
        "Edadif",
        when(col("Edadif") == 999, None)
        .otherwise(col("Edadif"))
    )

    return df


def remove_outliers_edad(df):

    q1, q3 = df.approxQuantile("Edadif", [0.25, 0.75], 0.01)
    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    return df.filter(
        (F.col("Edadif").isNull()) |
        ((F.col("Edadif") >= lower) & (F.col("Edadif") <= upper))
    )



def apply_validation(df, validation_config):

    for col_name, config in validation_config.items():

        df, _ = validate_codes(
            df,
            col_name,
            config["table"],
            critical=config["critical"]
        )

    return df


validation_config = {
    "Asist": {"table": "covid19.metadata.dim_asistencia_recibida", "critical": False},
    "Cerdef": {"table": "covid19.metadata.dim_certificador", "critical": True},
    "Ocur": {"table": "covid19.metadata.dim_citio_ocurrencia", "critical": True},

    "Depreg": {"table": "covid19.metadata.dim_departamentos", "critical": True},
    "Depocu": {"table": "covid19.metadata.dim_departamentos", "critical": True},
    "Dredif": {"table": "covid19.metadata.dim_departamentos", "critical": False},

    "Mupreg": {"table": "covid19.metadata.dim_municipios", "critical": True},
    "Mupocu": {"table": "covid19.metadata.dim_municipios", "critical": True},
    "Mredif": {"table": "covid19.metadata.dim_municipios", "critical": False},

    "Escodif": {"table": "covid19.metadata.dim_escolaridad", "critical": False},
    "Ecidif": {"table": "covid19.metadata.dim_estado_civil", "critical": False},
    "Ciuodif": {"table": "covid19.metadata.dim_ocupaciones", "critical": False},

    "Pnadif": {"table": "covid19.metadata.dim_paises", "critical": False},
    "Nacdif": {"table": "covid19.metadata.dim_paises", "critical": False},
    "Predif": {"table": "covid19.metadata.dim_paises", "critical": False},

    "Perdif": {"table": "covid19.metadata.dim_periodo_edad", "critical": False}
}


@dp.table(
    name="silver_ine_deaths",
    comment="Cleaned and validated death records"
)
def silver_ine_deaths():

    df = spark.table("covid19.bronze.ine_deaths")
    df = basic_cleaning(df)
    df = remove_outliers_edad(df)
    df = apply_validation(df, validation_config)
    df = df.withColumn(
        "silver_processing_date",
        F.current_timestamp()
    )

    return df
