import threading
from flask import Flask, jsonify, request
from flask_cors import CORS
from pyniryo import ConveyorDirection,PinState
import robot

app = Flask(__name__)
CORS(app)
robot_lock = threading.Lock()
@app.route("/")

def home():
    return "API funcionando"

@app.route("/run_main", methods=["POST"])
def run_main():
    def task():
        with robot_lock:
            robot.main()
    threading.Thread(target=task).start()
    return jsonify({"status": "Moviendo robot"})

@app.route("/runconv", methods=["POST"])
def runconv():
    def task():
        with robot_lock:
            robot.run_conv()
    threading.Thread(target=task).start()        
    return jsonify({"status":"Cinta funcionando"})

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
            robot.robot.run_conveyor(
                robot.conveyor_id, 
                speed=velocidad, 
                direction=ConveyorDirection.FORWARD
            )
            if robot.conexion:
                robot.insertar_log(
                    robot.conexion, 
                    f"Corriendo cinta a velocidad {velocidad}%", 
                    "Cinta"
                )
    threading.Thread(target=task).start()
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
    global funcionando
    threading.Thread(target=robot.stop_all).start()
    funcionando = False
    return jsonify({"status":"Parando robot"})

@app.route("/posicion", methods=["POST"])
def get_posicion():
    print(f"DEBUG enviando poscioon actual -> {robot.posicion}")
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
        print(f"Error en /posicion: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route("/paletizadas", methods=["POST"])
def piezaspaletizadas():
    try:
        return jsonify({"status":"ok", "piezas": robot.paletizadas})
    except Exception as e:
        return jsonify({"error": str(e)}), 500    

@app.route("/mover_posicion", methods=["POST"])
def moverposicion():
    data = request.json
    def task():
        with robot_lock:
            print(f"Moviendo a posición: {data}")  
            robot.mover(data["x"], data["y"], data["z"], data["roll"], data["pitch"], data["yaw"])
    threading.Thread(target=task).start()
    return jsonify({"status":"Moviendo posición"})

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
        return jsonify({"status": "error", "logs": [], "mensaje": "Sin conexion a BD"})
    tipo_filtro = request.args.get("tipo")
    print(f"--- NUEVA PETICION DE LOGS ---")
    print(f"Filtro recibido desde la web: '{tipo_filtro}'")
    logs = robot.obtener_logs(conexion, tipo_filtro)
    print(f"Enviando {len(logs)} logs al navegador")
    return jsonify({"status": "ok", "logs": logs})
    
@app.route("/sensores", methods=["GET"])
def leer_sensores():
    try:
        s1 = robot.robot.digital_read(robot.sensor1)
        s2 = robot.robot.digital_read(robot.sensor2)
        estado_s1 = "HIGH" if s1 == PinState.HIGH else "LOW"
        estado_s2 = "HIGH" if s2 == PinState.HIGH else "LOW"
        if robot.conexion:
            robot.insertar_log(
                robot.conexion,
                f"Lectura sensores — DI5: {estado_s1} | DI1: {estado_s2}",
                "Sensor"
            )
        return jsonify({"status": "ok", "sensor1": estado_s1, "sensor2": estado_s2})
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

@app.route("/open_gripper", methods=["POST"])
def open_gripper():
    def task():
        with robot_lock:
            robot.robot.open_gripper()
            if robot.conexion:
                robot.insertar_log(robot.conexion, "Pinza abierta desde interfaz", "Pinza")
    threading.Thread(target=task).start()
    return jsonify({"status": "Pinza abriendo"})

@app.route("/close_gripper", methods=["POST"])
def close_gripper():
    def task():
        with robot_lock:
            robot.robot.close_gripper()
            if robot.conexion:
                robot.insertar_log(robot.conexion, "Pinza cerrada desde interfaz", "Pinza")
    threading.Thread(target=task).start()
    return jsonify({"status": "Pinza cerrando"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)