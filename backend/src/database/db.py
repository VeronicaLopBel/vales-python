import pyodbc
from src.config import config

def get_connection():
    """Abre una conexión nueva a SQL Server. Recuerda cerrarla cuando termines."""
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={config.DB_SERVER},{config.DB_PORT};"
        f"DATABASE={config.DB_NAME};"
        f"UID={config.DB_USER};"
        f"PWD={config.DB_PASSWORD};"
        f"Encrypt=no;"
    )
    return pyodbc.connect(conn_str)


def vale_existe(conn, vale_id):
    """Revisa si un vale con ese ID ya existe en la tabla. Regresa True/False."""
    cursor = conn.cursor()
    cursor.execute("SELECT ID FROM vales WHERE ID = ?", str(vale_id))
    resultado = cursor.fetchone()
    cursor.close()
    return resultado is not None


def insertar_vale(conn, vale):
    """
    Inserta un vale nuevo. 'vale' es un diccionario con las llaves:
    id, sitestate, truckid, fecha, hora, galons, odometro, grate,
    cardno, sitecode, status, company, notes, pudate
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO vales
        (ID, SITESTATE, TRUCKID, FECHA, HORA, GALONS, ODOMETRO, GRATE,
         CARDNO, TRANSNO, SITECODE, STATUS, COMPANY, NOTES, PUDATE)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        vale["id"], vale["sitestate"], vale["truckid"], vale["fecha"],
        vale["hora"], vale["galons"], vale["odometro"], vale["grate"],
        vale["cardno"], vale["id"], vale["sitecode"], vale["status"],
        vale["company"], vale["notes"], vale["pudate"]
    )
    conn.commit()
    cursor.close()
    
def obtener_vales(desde, hasta):
    """Trae los vales de TruckNet y XIGA entre 2 fechas ('AAAA-MM-DD').
    Regresa una lista de diccionarios, uno por vale.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ID, TRUCKID, FECHA, HORA, GALONS, GRATE, COMPANY, SITESTATE
        FROM vales
        WHERE FECHA BETWEEN ? AND ?
          AND COMPANY IN ('TRUCK NET', 'XIGA')
        ORDER BY FECHA, HORA
        """,
        desde, hasta,
    )
    columnas = [c[0] for c in cursor.description]
    filas = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
    cursor.close()
    conn.close()
    return filas