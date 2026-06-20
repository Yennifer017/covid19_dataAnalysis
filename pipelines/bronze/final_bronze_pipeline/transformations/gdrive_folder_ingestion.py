import dlt
from pyspark.sql import functions as F
import pandas as pd
import requests
import io
import re

def download_public_gdrive_file(file_id: str, file_format: str = "csv", skiprows: int = 0) -> pd.DataFrame:
    """
    Descarga un archivo público de Google Drive y lo convierte a Pandas DataFrame.
    """
    download_url = f"https://docs.google.com/uc?export=download&id={file_id}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(download_url, headers=headers)
    response.raise_for_status()
    
    if file_format.lower() == "csv":
        file_stream = io.BytesIO(response.content)
        pdf = pd.read_csv(
            file_stream, 
            skiprows=skiprows, 
            on_bad_lines='skip', 
            engine='python',
            encoding_errors='ignore'
        )
    elif file_format.lower() in ["excel", "xlsx", "xls"]:
        file_stream = io.BytesIO(response.content)
        pdf = pd.read_excel(file_stream, engine='openpyxl', skiprows=skiprows)
    else:
        raise ValueError(f"Formato no soportado: {file_format}")
    
    pdf.columns = [
        re.sub(r'[^\w\s]', '_', str(c).lower().strip()).replace(' ', '_')
        for c in pdf.columns
    ]
    
    return pdf


gdrive_files = [
    {"file_id": "1AiDs4hV0Cw_GtVL-oHeoq_vRIqHZ82Ta", "table_name": "desagregados_por_evento_2015", "format": "csv", "skiprows": 0},
    {"file_id": "1vK_BpO7_Dtr-7hVJJe6bavo3Jzmy6a1j", "table_name": "desagregados_por_departamemto_2015", "format": "csv", "skiprows": 0},
    {"file_id": "1DMXBeCSlvGkRUWdmgs1t1zcDLialIjcc", "table_name": "desagregados_por_departamemto_2016", "format": "csv", "skiprows": 0},
    {"file_id": "1pzVqrFe3I2un9Gd1O1J_NLn-_jlpdIOQ", "table_name": "desagregados_por_evento_2016", "format": "csv", "skiprows": 0},
    {"file_id": "1NkGVskshIw4xeHVSh37arlo_bacvvnW_", "table_name": "desagregados_por_departamemto_2017", "format": "csv", "skiprows": 0},
    {"file_id": "1vVwrRjvNlUo0ZoJzT4qmW7vmuObgRhja", "table_name": "desagregados_por_evento_2017", "format": "csv", "skiprows": 0},
    {"file_id": "1AeVKWLYskwGL-n8FPEuo06S08Woxb-j0", "table_name": "desagregados_por_departamemto_2018", "format": "csv", "skiprows": 0},
    {"file_id": "1gNdRDkXUs1eB1VpIMQftxceEXtRnxf3g", "table_name": "desagregados_por_evento_2018", "format": "csv", "skiprows": 0},
    {"file_id": "1GwTIsin6ft_-CYk3hAX4eSRSHK0NmzX-", "table_name": "desagregados_por_departamemto_2019", "format": "csv", "skiprows": 0},
    {"file_id": "1wWWWtiPS_a2yIqesjR12OB4sLp3Z4reh", "table_name": "desagregados_por_evento_2019", "format": "csv", "skiprows": 0},
    {"file_id": "1A5nB4CcM_TZWdTyLaTNykHUG4e93i0xR", "table_name": "desagregados_por_departamemto_2020", "format": "csv", "skiprows": 0},
    {"file_id": "1lsHS9YGa-hukuM3FNNDoI_343QLNlnWS", "table_name": "desagregados_por_evento_2020", "format": "csv", "skiprows": 0},
    {"file_id": "15ZH3SyYN-3JrMYoLBq9nCeqzxr58RWJU", "table_name": "desagregados_por_departamemto_2021", "format": "csv", "skiprows": 0},
    {"file_id": "14LxbByQ6Fi1Qx0sq4krH-IO7At5atrXI", "table_name": "desagregados_por_evento_2021", "format": "csv", "skiprows": 0},
    {"file_id": "1eu4tb_QEm938YQjNpHBuTuFiBbbN5c0r", "table_name": "desagregados_por_evento_2022", "format": "csv", "skiprows": 0},
    {"file_id": "17gHoGvIe6szkm1JxdBPpBP0dc7_CaAHB", "table_name": "desagregados_por_departamemto_2022", "format": "csv", "skiprows": 0},
    {"file_id": "1G9wpazeELwss_ZhTpm-BXJxhxvOgFmfd", "table_name": "desagregados_por_evento_2023", "format": "csv", "skiprows": 0},
    {"file_id": "1mtfqtZRrkT0fKXXWYDC_wJO66RqMm6Ef", "table_name": "desagregados_por_departamemto_2023", "format": "csv", "skiprows": 0},
    {"file_id": "1JdeGQiN5LjoOdQQUNl9MSF-dIt1CsfLq", "table_name": "desagregados_por_evento_2024", "format": "csv", "skiprows": 0},
    {"file_id": "1vBFnssvbpObmefI6lw0-BBTCLQcJpFre", "table_name": "desagregados_por_departamemto_2024", "format": "csv", "skiprows": 0},
    {"file_id": "11h6RokcdqSDzPBSLT-6U2JOx-o2KeOZ5", "table_name": "desagregados_por_departamemto_2025", "format": "csv", "skiprows": 0},
    {"file_id": "1fTpil6-VM5kuGtC7w6uiNomhOAVVNzZo", "table_name": "desagregados_por_evento_2025", "format": "csv", "skiprows": 0},
    {"file_id": "1qPGTLA1OnCgzEVkwjhq5zejXpfOBtBqE", "table_name": "desagregados_por_departamemto_2026", "format": "csv", "skiprows": 0},
    {"file_id": "1mfA2ETgn8jtzZXKcoaaKfGuE8VpX9F4k", "table_name": "desagregados_por_evento_2026", "format": "csv", "skiprows": 0},
]


for file_config in gdrive_files:
    def factory(config=file_config):
        @dlt.table(
            name=config["table_name"],
            comment=f"Datos {config['table_name']} - Origen: Google Drive"
        )
        def load_gdrive_table():
            pdf_data = download_public_gdrive_file(
                file_id=config["file_id"],
                file_format=config["format"],
                skiprows=config["skiprows"]
            )
            return spark.createDataFrame(pdf_data)
        return load_gdrive_table
    factory()
