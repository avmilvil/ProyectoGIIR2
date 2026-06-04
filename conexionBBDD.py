import oracledb
import csv
import os
import threading
import time
from datetime import datetime

_DIR = os.path.dirname(os.path.abspath(__file__))
# Ruta del archivo CSV exclusivo de logins
CSV_LOGS_PATH = os.path.join(_DIR, "logs_robot.csv")
# Estructuras para el hilo de login asíncrono
logins_pendientes = []
lock_logins = threading.Lock()
evento_login = threading.Event()

def trabajo_guardar_logins(evento):
    """
    Hilo daemon que espera a que haya logins pendientes mediante un Evento
    y los añade al archivo CSV único 'logins.csv'.
    """
    while True:
        evento.wait()  # Espera a que el evento sea activado (evento.set())
        
        while evento.is_set():
            logins_a_escribir = []
            with lock_logins:
                if logins_pendientes:
                    logins_a_escribir = list(logins_pendientes)
                    logins_pendientes.clear()
                else:
                    evento.clear()  # No quedan elementos, desactivamos el interruptor
            
            if logins_a_escribir:
                try:
                    archivo_nuevo = not os.path.exists(CSV_LOGS_PATH)
                    with open(CSV_LOGS_PATH, "a", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f, delimiter=";")
                        if archivo_nuevo:
                            # Cabecera descriptiva para el CSV de logins
                            writer.writerow(["fecha", "instruccion", "tipo", "robot_id"])
                        for log in logins_a_escribir:
                            writer.writerow([log["fecha"], log["instruccion"], log["tipo"], log["robot_id"]])
                except Exception as e:
                    print("Error al escribir logs en CSV:", e)
            
            time.sleep(0.5)  # Breve pausa para control de recursos

# Iniciamos el hilo de escritura al importar el módulo
hilo_escritor = threading.Thread(target=trabajo_guardar_logins, args=(evento_login,), daemon=True)
hilo_escritor.start()

def encolar_log(instruccion, tipo, robot_id):
    """Añade un log a la cola y activa el evento para despertar al hilo."""
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with lock_logins:
        logins_pendientes.append({
            "fecha": fecha_actual,
            "instruccion": instruccion,
            "tipo": tipo,
            "robot_id": robot_id
        })
    evento_login.set()

# =====================================================================
#  CONEXIÓN / DESCONEXIÓN
# =====================================================================

def conectar(usuario="vgarled", password="vgarled"):
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

def desconectar(conexion):
    if conexion:
        conexion.close()
        print("Desconectado con éxito")

# =====================================================================
#  TABLA: log
# =====================================================================

def insertar_log(conexion, instruccion, tipo="Info", robot_id=16):
    try:
        cursor = conexion.cursor()
        sql = "INSERT INTO log(instruccion, tipo, robot_id) VALUES (:1, :2, :3)"
        cursor.execute(sql, [instruccion, tipo, robot_id])
        conexion.commit()
        cursor.close()

    except Exception as e:
        print("Error al insertar log:", e)

    encolar_log(instruccion, tipo, robot_id)

def obtener_logs(conexion, tipo_filtro=None):
    try:
        cursor = conexion.cursor()
        sql = "SELECT id, fecha, tipo, instruccion FROM log"
        params = []
        
        if tipo_filtro and tipo_filtro != "Todos":
            sql += " WHERE tipo = :1"
            params.append(tipo_filtro)
            
        sql += " ORDER BY id DESC"
        
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

def eliminar_logs(conexion):
    """Elimina todos los registros de la tabla log."""
    try:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM log")
        conexion.commit()
        cursor.close()
        print("Todos los logs eliminados")
    except Exception as e:
        print("Error al eliminar logs:", e)

# =====================================================================
#  TABLA: Movimiento
# =====================================================================

def insertar_movimiento(conexion, x, y, z, pitch, roll, yaw, log_id):
    """Inserta un registro de movimiento con las coordenadas y rotaciones."""
    try:
        cursor = conexion.cursor()
        sql = """INSERT INTO Movimiento(x, y, z, pitch, roll, yaw, log_id)
                 VALUES (:1, :2, :3, :4, :5, :6, :7)"""
        cursor.execute(sql, [x, y, z, pitch, roll, yaw, log_id])
        conexion.commit()
        cursor.close()
    except Exception as e:
        print("Error al insertar movimiento:", e)

def obtener_movimientos(conexion):
    """Devuelve todos los registros de movimiento ordenados por id descendente."""
    try:
        cursor = conexion.cursor()
        sql = "SELECT id, x, y, z, pitch, roll, yaw, log_id FROM Movimiento ORDER BY id DESC"
        cursor.execute(sql)
        resultados = cursor.fetchall()
        cursor.close()
        return resultados
    except Exception as e:
        print("Error al consultar movimientos:", e)
        return []

def obtener_ultimo_movimiento(conexion):
    """Devuelve el último registro de movimiento."""
    try:
        cursor = conexion.cursor()
        sql = """SELECT id, x, y, z, pitch, roll, yaw, log_id FROM Movimiento
                 ORDER BY id DESC FETCH FIRST 1 ROWS ONLY"""
        cursor.execute(sql)
        resultado = cursor.fetchone()
        cursor.close()
        return resultado
    except Exception as e:
        print("Error al consultar último movimiento:", e)
        return None

def eliminar_movimientos(conexion):
    """Elimina todos los registros de movimiento."""
    try:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM Movimiento")
        conexion.commit()
        cursor.close()
        print("Todos los movimientos eliminados")
    except Exception as e:
        print("Error al eliminar movimientos:", e)

# =====================================================================
#  TABLA: Robot
# =====================================================================

def insertar_robot(conexion, nombre, tipo, estado):
    """Inserta un nuevo robot. estado: 1 = activo, 0 = inactivo."""
    try:
        cursor = conexion.cursor()
        sql = """INSERT INTO Robot(Nombre, tipo, estado)
                 VALUES (:1, :2, :3)"""
        cursor.execute(sql, [nombre, tipo, int(estado)])
        conexion.commit()
        cursor.close()
    except Exception as e:
        print("Error al insertar robot:", e)

def obtener_robots(conexion):
    """Devuelve todos los robots registrados."""
    try:
        cursor = conexion.cursor()
        sql = "SELECT id, Nombre, tipo, estado FROM Robot ORDER BY id"
        cursor.execute(sql)
        resultados = cursor.fetchall()
        cursor.close()
        return resultados
    except Exception as e:
        print("Error al consultar robots:", e)
        return []

def obtener_robot_por_id(conexion, robot_id):
    """Devuelve un robot por su id."""
    try:
        cursor = conexion.cursor()
        sql = "SELECT id, Nombre, tipo, estado FROM Robot WHERE id = :1"
        cursor.execute(sql, [robot_id])
        resultado = cursor.fetchone()
        cursor.close()
        return resultado
    except Exception as e:
        print("Error al consultar robot:", e)
        return None

def actualizar_estado_robot(conexion, robot_id, estado):
    """Actualiza el estado de un robot. estado: 1 = activo, 0 = inactivo."""
    try:
        cursor = conexion.cursor()
        sql = "UPDATE Robot SET estado = :1 WHERE id = :2"
        cursor.execute(sql, [int(estado), robot_id])
        conexion.commit()
        cursor.close()
    except Exception as e:
        print("Error al actualizar estado del robot:", e)

def eliminar_robot(conexion, robot_id):
    """Elimina un robot por su id."""
    try:
        cursor = conexion.cursor()
        sql = "DELETE FROM Robot WHERE id = :1"
        cursor.execute(sql, [robot_id])
        conexion.commit()
        cursor.close()
    except Exception as e:
        print("Error al eliminar robot:", e)

# =====================================================================
#  TABLA: Cinta
# =====================================================================

def insertar_cinta(conexion, direccion, velocidad, estado, robot_id):
    """Inserta un registro de cinta. estado: 1 = activa, 0 = parada."""
    try:
        cursor = conexion.cursor()
        sql = """INSERT INTO Cinta(direccion, velocidad, estado, robot_id)
                 VALUES (:1, :2, :3, :4)"""
        cursor.execute(sql, [direccion, velocidad, int(estado), robot_id])
        conexion.commit()
        cursor.close()
    except Exception as e:
        print("Error al insertar cinta:", e)

def obtener_cintas(conexion):
    """Devuelve todos los registros de cinta."""
    try:
        cursor = conexion.cursor()
        sql = "SELECT id, direccion, velocidad, estado, robot_id FROM Cinta ORDER BY id"
        cursor.execute(sql)
        resultados = cursor.fetchall()
        cursor.close()
        return resultados
    except Exception as e:
        print("Error al consultar cintas:", e)
        return []

def obtener_cinta_por_id(conexion, cinta_id):
    """Devuelve una cinta por su id."""
    try:
        cursor = conexion.cursor()
        sql = "SELECT id, direccion, velocidad, estado, robot_id FROM Cinta WHERE id = :1"
        cursor.execute(sql, [cinta_id])
        resultado = cursor.fetchone()
        cursor.close()
        return resultado
    except Exception as e:
        print("Error al consultar cinta:", e)
        return None

def actualizar_cinta(conexion, cinta_id, direccion, velocidad, estado):
    """Actualiza dirección, velocidad y estado de una cinta."""
    try:
        cursor = conexion.cursor()
        sql = """UPDATE Cinta SET direccion = :1, velocidad = :2, estado = :3
                 WHERE id = :4"""
        cursor.execute(sql, [direccion, velocidad, int(estado), cinta_id])
        conexion.commit()
        cursor.close()
    except Exception as e:
        print("Error al actualizar cinta:", e)

def actualizar_estado_cinta(conexion, cinta_id, estado):
    """Actualiza solo el estado de una cinta. estado: 1 = activa, 0 = parada."""
    try:
        cursor = conexion.cursor()
        sql = "UPDATE Cinta SET estado = :1 WHERE id = :2"
        cursor.execute(sql, [int(estado), cinta_id])
        conexion.commit()
        cursor.close()
    except Exception as e:
        print("Error al actualizar estado de cinta:", e)

def eliminar_cinta(conexion, cinta_id):
    """Elimina una cinta por su id."""
    try:
        cursor = conexion.cursor()
        sql = "DELETE FROM Cinta WHERE id = :1"
        cursor.execute(sql, [cinta_id])
        conexion.commit()
        cursor.close()
    except Exception as e:
        print("Error al eliminar cinta:", e)

# =====================================================================
#  TABLA: Sensores
# =====================================================================

def insertar_sensor(conexion, estado, robot_id):
    """Inserta un nuevo sensor. estado: 1 = activo, 0 = inactivo."""
    try:
        cursor = conexion.cursor()
        sql = "INSERT INTO Sensores(estado, robot_id) VALUES (:1, :2)"
        cursor.execute(sql, [int(estado), robot_id])
        conexion.commit()
        cursor.close()
    except Exception as e:
        print("Error al insertar sensor:", e)

def obtener_sensores(conexion):
    """Devuelve todos los sensores registrados."""
    try:
        cursor = conexion.cursor()
        sql = "SELECT id, estado, robot_id FROM Sensores ORDER BY id"
        cursor.execute(sql)
        resultados = cursor.fetchall()
        cursor.close()
        return resultados
    except Exception as e:
        print("Error al consultar sensores:", e)
        return []

def obtener_sensor_por_id(conexion, sensor_id):
    """Devuelve un sensor por su id."""
    try:
        cursor = conexion.cursor()
        sql = "SELECT id, estado, robot_id FROM Sensores WHERE id = :1"
        cursor.execute(sql, [sensor_id])
        resultado = cursor.fetchone()
        cursor.close()
        return resultado
    except Exception as e:
        print("Error al consultar sensor:", e)
        return None

def actualizar_estado_sensor(conexion, sensor_id, estado):
    """Actualiza el estado de un sensor. estado: 1 = activo, 0 = inactivo."""
    try:
        cursor = conexion.cursor()
        sql = "UPDATE Sensores SET estado = :1 WHERE id = :2"
        cursor.execute(sql, [int(estado), sensor_id])
        conexion.commit()
        cursor.close()
    except Exception as e:
        print("Error al actualizar estado del sensor:", e)

def eliminar_sensor(conexion, sensor_id):
    """Elimina un sensor por su id."""
    try:
        cursor = conexion.cursor()
        sql = "DELETE FROM Sensores WHERE id = :1"
        cursor.execute(sql, [sensor_id])
        conexion.commit()
        cursor.close()
    except Exception as e:
        print("Error al eliminar sensor:", e)
