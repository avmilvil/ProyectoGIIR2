import oracledb

def conectar(usuario, password):
    try:
        conexion = oracledb.connect(
            user = usuario,
            password = password,
            dsn = "oralabos.dsic.upv.es/labora.dsic.upv.es"
        )
        print("Conectado con éxito")
        return conexion
    except Exception as e:
        print("Error al conectar: ", e)
        return None
    
def insertar_log(conexion, instruccion, tipo="Info"):
    try:
        cursor = conexion.cursor()
        sql = "INSERT INTO log(instruccion, tipo) VALUES (:1, :2)"

        cursor.execute(sql, [instruccion, tipo])

        conexion.commit()
        cursor.close()

    except Exception as e:
        print("Error al insertar:", e)

def obtener_logs(conexion, tipo_filtro=None):
    try:
        cursor = conexion.cursor()
        sql = "SELECT id, fecha, tipo, instruccion FROM log"
        params = []
        
        if tipo_filtro and tipo_filtro != "Todos":
            sql += " WHERE tipo = :1"
            params.append(tipo_filtro)
            
        sql += " ORDER BY id DESC"
        
        print(f"SQL a ejecutar: {sql} con parametros: {params}")
        
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)

        resultados = cursor.fetchall()
        cursor.close()
        return resultados
    except Exception as e:
        print("Error al consultar logs:", e)
        return []

def desconectar(conexion):
    if conexion:
        conexion.close()
        print("Desconectado con éxito")
