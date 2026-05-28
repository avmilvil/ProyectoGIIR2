import threading
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from pyniryo import PinState
import robot 
from queue import Queue
import time
from conexionBBDD import *

app = Flask(__name__)
CORS(app)
robot_lock = threading.Lock()
cola = Queue()

def worker():
    while True:
        data = cola.get()
        instruccion, elemento = data

        try:
            conn = conectar()
            insertar_log(conn, instruccion, elemento)
            conn.close()

            print("Insertado: ", instruccion, elemento)
        except Exception as e:
            print("Error insertando, reintentando...", e)
            time.sleep(5)
            cola.put(data)
        finally:
            cola.task_done()

@app.route("/")
def home():
    return render_template("web_principal.html")

@app.route("/configurar_robot", methods=["POST"])
def configurar_robot():
    datos = request.get_json()
    nueva_ip = datos.get("robot_ip")
    def task():
        with robot_lock:
            try:
                print(f"Iniciando conexión hacia {nueva_ip}...")
                robot.inicializar_conexion(nueva_ip)
            except Exception as e:
                print(f"Error en el servidor al conectar: {str(e)}")
    threading.Thread(target=task).start()
    return jsonify({"status": f"Conectando a {nueva_ip}"})

@app.route("/run_main", methods=["POST"])
def run_main():
    def task():
        with robot_lock:
            robot.main()
    threading.Thread(target=task).start()
    return jsonify({"status": "Moviendo robot"})

# @app.route("/runconv", methods=["POST"])
# def runconv():
#     def task():
#            with robot_lock: 
#                 robot.run_conv()
#     threading.Thread(target=task).start()        
#     return jsonify({"status":"Cinta funcionando"})

@app.route("/stopconv", methods=["POST"])
def stopconv():
    def task():
        with robot_lock: 
            print("Deteniendo cinta...")
            robot.stop_conv()
    threading.Thread(target=task).start()
    return jsonify({"status":"Cinta parada"})

@app.route("/runconv_speed", methods=["POST"])
def runconv_speed():
    data = request.json
    velocidad = int(data.get("velocidad", 50))
    def task():
        with robot_lock:    
            robot.run_conv(velocidad)
    threading.Thread(target=task, daemon=True).start()
    return jsonify({"status": f"Cinta corriendo al {velocidad}%"})

@app.route("/home", methods=["POST"])
def movehome():
    def task():
        #print("Moviendo a home")
        adquirido = robot_lock.acquire(timeout=5)
        if not adquirido:
            print("El robot está bloqueado por otra tarea.")
            return
        try:
            print("Moviendo a home...")
            robot.move_home()
        except Exception as e:
            print(f"Error al mover a home: {e}")
        finally:
            robot_lock.release()
            print("--- Lock liberado ---")
            
    threading.Thread(target=task, daemon=True).start()
    return jsonify({"status":"Moviendo a home"})

@app.route("/stop", methods=["POST"])
def stop():

    threading.Thread(target=robot.stop_all).start()

    return jsonify({"status":"Parando robot"})

@app.route("/posicion", methods=["POST"])
def get_posicion():
    print(f"DEBUG enviando posicion actual -> {robot.posicion}")
    p = robot.posicion
    try:
        return jsonify({
            "status": "ok",
            "x": p["x"]*1000.0,
            "y": p["y"]*1000.0,
            "z": p["z"]*1000.0,
            "roll": p["roll"],
            "pitch": p["pitch"],
            "yaw": p["yaw"]
        })
    except Exception as e:
        print(f"Error en posicion: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route("/paletizadas", methods=["POST"])
def piezaspaletizadas():
    try:
        return jsonify({"status":"ok", "piezas_paletizadas": robot.paletizadas})
    except Exception as e:
        return jsonify({"error": str(e)}), 500    
    
@app.route("/desechadas", methods=["POST"])
def piezas_desechadas():
    try:
        return jsonify({"status":"ok", "piezas_desechadas": robot.desechos})
    except Exception as e:
        return jsonify({"error": str(e)}), 500    

@app.route("/mover_posicion", methods=["POST"])
def moverposicion():
    data = request.json
    def task():
        adquirido = robot_lock.acquire(timeout=5)
        if not adquirido:
            print("El robot está bloqueado por otra tarea.")
            return
        try:
            print(f"Moviendo a posición: {data}")
            robot.mover(data["x"], data["y"], data["z"],
                        data["roll"], data["pitch"], data["yaw"])
        except Exception as e:
            print(f"Error al mover posición: {e}")
        finally:
            robot_lock.release()
    threading.Thread(target=task, daemon=True).start()
    return jsonify({"status": "Moviendo posición"})

@app.route("/disconnect_DB", methods=["POST"])
def desconectarDB():
    def task():
        with robot_lock:
            robot.close_DB()
    threading.Thread(target=task).start()        
    return jsonify({"status":"Desconectando de la DB"})

@app.route("/logs", methods=["GET"])
def ver_logs():
    conexion = robot.conexion
    if conexion is None:
        return jsonify({"status": "error", "logs": [],
                        "mensaje": "Sin conexión a BD"})
    tipo_filtro = request.args.get("tipo")
    print(f"--- NUEVA PETICION DE LOGS ---")
    print(f"Filtro recibido desde la web: '{tipo_filtro}'")
    logs = robot.obtener_logs(conexion, tipo_filtro)
    print(f"Enviando {len(logs)} logs al navegador")
    return jsonify({"status": "ok", "logs": logs})
    
@app.route("/sensores", methods=["GET"])
def leer_sensores():
    try:
        adquirido = robot_lock.acquire(timeout=3)
        if not adquirido:
            return jsonify({"status": "error",
                            "mensaje": "Robot ocupado, reintenta en un momento"}), 503
        try:
            s1 = robot.robot.digital_read(robot.sensor1)
            s2 = robot.robot.digital_read(robot.sensor2)
        finally:
            robot_lock.release()
 
        return jsonify({
            "status":  "ok",
            "sensor1": "HIGH" if s1 == PinState.HIGH else "LOW",
            "sensor2": "HIGH" if s2 == PinState.HIGH else "LOW",
        })
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

@app.route("/open_gripper", methods=["POST"])
def open_gripper():
    def task():
        adquirido = robot_lock.acquire(timeout=5)
        if not adquirido:
            print("El robot está bloqueado, no se pudo abrir gripper.")
            return
        try:
            robot.robot.open_gripper()
            if robot.conexion:
                robot.insertar_log(robot.conexion, "Pinza abierta (manual)", "Pinza")
        except Exception as e:
            print(f"Error al abrir gripper: {e}")
        finally:
            robot_lock.release()
    threading.Thread(target=task, daemon=True).start()
    return jsonify({"status": "Pinza abriendo"})
 
@app.route("/close_gripper", methods=["POST"])
def close_gripper():
    def task():
        adquirido = robot_lock.acquire(timeout=5)
        if not adquirido:
            print("El robot está bloqueado, no se pudo cerrar gripper.")
            return
        try:
            robot.robot.close_gripper()
            if robot.conexion:
                robot.insertar_log(robot.conexion, "Pinza cerrada (manual)", "Pinza")
        except Exception as e:
            print(f"Error al cerrar gripper: {e}")
        finally:
            robot_lock.release()
    threading.Thread(target=task, daemon=True).start()
    return jsonify({"status": "Pinza cerrando"})

@app.route('/insertaenlog', methods=["POST"])
def recibir_log():
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON vacío"}), 400
    
    cola.put(data)
    return jsonify({"status": "encolado"}), 202

@app.route("/movimientos", methods=["GET"])
def ver_movimientos():
    conexion = robot.conexion
    try:
        movimientos = robot.obtener_movimientos(conexion)
        return jsonify({"status": "ok", "movimientos": movimientos})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/robots", methods=["GET"])
def ver_robots():
    conexion = robot.conexion
    try:
        robots = robot.obtener_robots(conexion)
        return jsonify({"status": "ok", "robots": robots})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/cintas", methods=["GET"])
def ver_cintas():
    conexion = robot.conexion
    try:
        cintas = robot.obtener_cintas(conexion)
        return jsonify({"status": "ok", "cintas": cintas})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/sensores_db", methods=["GET"])
def ver_sensores_db():
    conexion = robot.conexion
    try:
        sensores = robot.obtener_sensores(conexion)
        return jsonify({"status": "ok", "sensores": sensores})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    threading.Thread(target=worker, daemon=True).start()
    app.run(host="127.0.0.1", port=5000, debug=False)