import dlt
from pyspark.sql import functions as F
import pandas as pd
import requests
import io

def download_public_gdrive_csv(file_id: str, skiprows: int) -> pd.DataFrame:
    """
    Downloads a public Google Drive CSV file using its ID 
    and loads it into a Pandas DataFrame, skipping metadata headers.
    """
   
    download_url = f"https://docs.google.com/uc?export=download&id={file_id}"
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    response = requests.get(download_url, headers=headers)
    response.raise_for_status()  
    
    file_stream = io.BytesIO(response.content)
    pdf = pd.read_csv(
        file_stream, 
        skiprows=skiprows, 
        on_bad_lines='skip', 
        engine='python'
    )
    
    pdf.columns = [
        c.lower().strip().replace(' ', '_').replace('-', '_').replace('/', '_') 
        for c in pdf.columns
    ]
    
    return pdf


@dlt.table(
    name="who_mortality",
    comment="Raw WHO mortality data for Guatemala ingested directly from Google Drive."
)
def who_mortality_bronze():
    GOOGLE_DRIVE_FILE_ID = "1XC5fwdXo94bLmpTDB4JkN79cr8bGs5o8"
    METADATA_ROWS_TO_SKIP = 9
    
    pdf_data = download_public_gdrive_csv(
        file_id=GOOGLE_DRIVE_FILE_ID, 
        skiprows=METADATA_ROWS_TO_SKIP
    )
    return spark.createDataFrame(pdf_data)