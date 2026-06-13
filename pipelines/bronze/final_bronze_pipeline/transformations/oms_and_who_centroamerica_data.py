import dlt
from pyspark.sql import functions as F
import pandas as pd
import requests
import io

def download_public_sharepoint_csv(sharepoint_url: str, skiprows: int) -> pd.DataFrame:
    if "?" in sharepoint_url:
        base_url = sharepoint_url.split("?")[0]
        download_url = f"{base_url}?download=1"
    else:
        download_url = f"{sharepoint_url}?download=1"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(download_url, headers=headers)
    response.raise_for_status() 
    clean_text = response.content.decode('utf-8-sig', errors='ignore')
    file_stream = io.StringIO(clean_text)
    pdf = pd.read_csv(
        file_stream, 
        skiprows=skiprows, 
        sep=",",                    
        header=0,
        engine='python',            
        encoding_errors='ignore',   
        on_bad_lines='skip',        
        keep_default_na=True        
    )
    pdf = pdf.loc[:, ~pdf.columns.str.contains('^<!___copyright_', case=False)]
    pdf.columns = [
        str(c).lower().strip().replace(' ', '_').replace('-', '_').replace('/', '_') 
        for c in pdf.columns
    ]
    return pdf

sharepoint_sources = [
    (
        "who_covid_19_global_daily_data", 
        "https://1drv.ms/x/c/9b3df75ac5d97177/IQA952j9q_4-RoJeMFhCG5CqAQ79T6BcFqHtAI5SfbpsnHg?e=zDrJgq", 
        0
    ),
    (
        "mortalidad_por_edades_costa_rica", 
        "https://1drv.ms/x/c/9b3df75ac5d97177/IQDLvWOtzCNFSpo_Nj6IoP4iAd_egWqve7_kb-3vTNCRCrY?e=UMJhhx", 
        8
    ),
    (
        "mortalidad_indicadores_costa_rica", 
        "https://1drv.ms/x/c/9b3df75ac5d97177/IQDZFPcLVZJGSIG-tkWrFlSlAYlX-MwSG8iNa6hBUuX47L4?e=v0P7fX", 
        8
    ),
    (
        "mortalidad_categorias_costa_rica_2022", 
        "https://1drv.ms/x/c/9b3df75ac5d97177/IQCZgdufUPXySohL08_uc3cpAelrtRmzH_0lYvb5haQVCGU?e=YWIMQ9", 
        8
    ),
    (
        "mortalidad_categorias_costa_rica_2021", 
        "https://1drv.ms/x/c/9b3df75ac5d97177/IQA-resb3FP9RphCtunYyH_vAfD2axPRtwBoonO1m1X22nE?e=KeDxhX", 
        8
    ),
    (
        "mortalidad_categorias_costa_rica_2020(1)", 
        "https://1drv.ms/x/c/9b3df75ac5d97177/IQDZZUKSZbzIR5igaZ3f9CzHAbVWmwADCqD4wWUP4-l-bR0?e=WWwKGa", 
        8
    ),
    
]

for table_name, url, rows_to_skip in sharepoint_sources:
    def factory(target_url=url, skip_count=rows_to_skip):
        @dlt.table(
            name=table_name,
            comment=f"Table generated from SharePoint source: {table_name}"
        )
        def load_table():
            pdf_data = download_public_sharepoint_csv(
                sharepoint_url=target_url, 
                skiprows=skip_count
            )
            return spark.createDataFrame(pdf_data)
    factory()