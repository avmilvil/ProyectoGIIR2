import threading
from flask import Flask, jsonify, request
from flask_cors import CORS
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
    tipo_filtro = request.args.get("tipo")
    print(f"--- NUEVA PETICION DE LOGS ---")
    print(f"Filtro recibido desde la web: '{tipo_filtro}'")
    logs = robot.obtener_logs(conexion, tipo_filtro)
    print(f"Enviando {len(logs)} logs al navegador")
    return jsonify({"status": "ok", "logs": logs})
    



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)