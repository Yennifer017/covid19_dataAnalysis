from pyspark import pipelines as dp

# Configuración de conexión MySQL RDS
MYSQL_HOST = "ds-transaccional-rds.cx0w640wuzud.us-east-2.rds.amazonaws.com"
MYSQL_PORT = "3306"
MYSQL_DATABASE = "proyecto_necropsias"
MYSQL_USER = "admin_ss2"
MYSQL_PASSWORD = "TU_CONTRASEÑA_AQUI"  # ⚠️ REEMPLAZAR con la contraseña real
MYSQL_TABLE = "NOMBRE_DE_TU_TABLA"  # ⚠️ REEMPLAZAR con el nombre de la tabla (ej: necropsias, casos, etc.)
SSL_CERT_PATH = "/path/to/global-bundle.pem"  # ⚠️ REEMPLAZAR con la ruta al certificado SSL

# JDBC URL para MySQL con SSL
JDBC_URL = f"jdbc:mysql://{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?useSSL=true&requireSSL=true&enabledTLSProtocols=TLSv1.2&trustCertificateKeyStoreUrl=file:{SSL_CERT_PATH}"

@dp.materialized_view(
    name="bronze_inacif_necropsias",
    comment="Datos de necropsias desde MySQL RDS - Carga completa"
)
def bronze_inacif_necropsias():
    """
    Lee datos de la tabla de MySQL RDS usando JDBC.
    Realiza una carga completa en cada ejecución del pipeline.
    """
    return (
        spark.read
        .format("jdbc")
        .option("url", JDBC_URL)
        .option("dbtable", MYSQL_TABLE)
        .option("user", MYSQL_USER)
        .option("password", MYSQL_PASSWORD)
        .option("driver", "com.mysql.cj.jdbc.Driver")
        .load()
    )
