import time
from pyniryo import *
import requests
URL = "http://127.0.0.1:5000/insertaenlog"

def enviar_log(instruccion, elemento):
    try:
        data = [instruccion, elemento]
        r = requests.post(URL, json=data, timeout=3)
        return r.status_code == 202
    except requests.exceptions.RequestException:
        return False
    
#Configuración de la base de datos
#usar_database = True

#if usar_database:
#    conexion = conectar(user, password)

robot = NiryoRobot("127.0.0.1")
sensor1 = "DI5"
sensor2 = "DI1"
conveyor_id = robot.set_conveyor()
paletizadas = 0
stop_requested = False

inicio = PoseObject(x=0.140, y=0.000, z=0.203, roll=0.003, pitch=0.757, yaw=-0.001)
subir_abierto = PoseObject(x=0.155, y=-0.009, z=0.327, roll=0.460, pitch=1.505, yaw=0.547)
bajar1 = PoseObject(x=0.226, y=-0.194, z=0.221, roll=-3.037, pitch=1.344, yaw=-2.859)
bajar1_2 = PoseObject(x=0.221, y=-0.197, z=0.169, roll=3.087, pitch=1.312, yaw=3.131)
#close gripper
#robot.grasp_with_tool()
subir_cerrado1 = PoseObject(x=0.165, y=-0.146, z=0.355, roll=-0.291, pitch=1.088, yaw=-0.548)
bajar1_3 = PoseObject(x=0.278, y=-0.212, z=0.186, roll=0.481, pitch=1.406, yaw=0.547)
#open gripper
#robot.release_with_tool()
subir_poquito = PoseObject(x=0.277, y=-0.198, z=0.213, roll=-0.647, pitch=1.481, yaw=-0.606)
atacar1 = PoseObject(x=0.287, y=0.135, z=0.174, roll=2.765, pitch=1.471, yaw=2.727)
atacar_abajo1 = PoseObject(x=0.288, y=0.136, z=0.156, roll=2.762, pitch=1.476, yaw=2.698)
subir_ataque = PoseObject(x=0.216, y=0.219, z=0.316, roll=-1.533, pitch=1.513, yaw=-0.612)
bajar_ataque1 = PoseObject(x=0.076, y=0.227, z=0.157, roll=2.622, pitch=1.534, yaw=-2.155)
subir_final_ataque1 = PoseObject(x=0.100, y=0.206, z=0.282, roll=0.239, pitch=1.522, yaw=1.409)

posicion = {
    "x": 0.0,
    "y": 0.0,
    "z": 0.0,
    "roll": 0.0,
    "pitch": 0.0,
    "yaw": 0.0
}

def inicializar_robot():
    #global conveyor_id
    try:
        # Forzamos una pequeña espera antes de calibrar
        print("Calibrando...")
        time.sleep(2)
        robot.calibrate_auto()
        
        enviar_log("Robot Calibrando", "Sistema")
        print("Calibración terminada")
        robot.update_tool()
        
        enviar_log("Robot actualizando herramienta", "Sistema")
        print("Robot listo.")
    except Exception as e:
        print(f"Error en calibración: {e}")
    #robot.calibrate_auto()
    #robot.wait(10) si la calibración no se ha hecho
    #conveyor_id = robot.set_conveyor()
    
def run_conv(velocidad=50):
    if conveyor_id:
        robot.run_conveyor(conveyor_id, speed=velocidad, direction=ConveyorDirection.FORWARD)
        enviar_log(f"Corriendo Cinta al {velocidad}%", "Cinta")
        
def stop_conv():
    robot.stop_conveyor(conveyor_id)
    enviar_log("Cinta Detenida", "Cinta")

def move_home():
    global posicion
    
    robot.move_to_home_pose()
    pos = robot.get_pose()
    actualizar_posicion(pos)
    enviar_log("Movimiendo a HOME", "Movimiento")

def mover(x, y, z, roll, pitch, yaw):
    pos = PoseObject(x=x, y=y, z=z, roll=roll, pitch=pitch, yaw=yaw)
    try:
        robot.wait(0.1)
        robot.move_pose(pos)
        actualizar_posicion(pos)
        enviar_log(f"Moviendo a posición: x={pos.x}, y={pos.y}, z={pos.z}, roll={pos.roll}, pitch={pos.pitch}, yaw={pos.yaw}", "Movimiento")
        robot.wait(0.2) 
    except Exception as e:
        print(f"Error en movimiento: {e}")

def actualizar_posicion(pose_object):
    global posicion
    try:
        posicion = {
            "x": pose_object.x, 
            "y": pose_object.y, 
            "z": pose_object.z, 
            "roll": pose_object.roll, 
            "pitch": pose_object.pitch, 
            "yaw": pose_object.yaw
        }
    except Exception as e:
        print(f"No se pudo actualizar la posición: {e}")
    
# def close_DB():
#     global usar_database, conexion

#     if usar_database and conexion is not None:
#         try:
#             desconectar(conexion)
#         except Exception as e:
#             print(f"Error al intentar cerrar la BD: {e}")
#         finally:
#             usar_database = False
#             conexion = None

def main():
    inicializar_robot()
    enviar_log("Robot inicializado", "Sistema")
    global paletizadas
    global stop_requested
    global posicion
 
    for i in range(4):
        if stop_requested:
            print("STOP solicitado, saliendo de main")
            enviar_log("Stop Solicitado, deteniendo main", "Sistema")
            break
 
        #Abre la pinza
        robot.open_gripper()
        #Guarda en la BBDD
        enviar_log("Abriendo pinza para tomar pieza", "Pinza")
 
        #Se mueve a inicio
        robot.move_pose(inicio)
        actualizar_posicion(inicio)
        #Guarda en la BBDD
        enviar_log("Moviendo a posición inicial para tomar pieza", "Movimiento")
 
        #Se mueve a subir_abierto
        robot.move_pose(subir_abierto)
        actualizar_posicion(subir_abierto)
        #Guarda en la BBDD
        enviar_log("Moviendo a posición de agarre", "Movimiento")
 
        #Se mueve a bajar1
        robot.move_pose(bajar1)
        actualizar_posicion(bajar1)
        #Guarda en la BBDD
        enviar_log("Ejecutando bajar a pieza", "Movimiento")
 
        #Se mueve a bajar1_2
        robot.move_pose(bajar1_2)
        actualizar_posicion(bajar1_2)
        #Guarda en la BBDD
        enviar_log("Ejecutando agarrar pieza", "Pinza")
 
        #Cierra pinza
        robot.close_gripper()
        #Guarda en la BBDD
        enviar_log("Cerrando pinza para agarrar pieza", "Pinza")
 
        #Se mueve a subir_cerrado1
        robot.move_pose(subir_cerrado1)
        actualizar_posicion(subir_cerrado1)
        #Guarda en la BBDD
        enviar_log("Subiendo con pieza agarrada", "Movimiento")
 
        #Se mueve a bajar1_3
        robot.move_pose(bajar1_3)
        actualizar_posicion(bajar1_3)
        #Guarda en la BBDD
        enviar_log("Moviendo a posición para soltar pieza en cinta", "Movimiento")
 
        #Abre pinza
        robot.open_gripper()
        #Guarda en la BBDD
        enviar_log("Abriendo pinza para soltar pieza en cinta", "Pinza")
 
        #Se mueve a subir_poquito
        robot.move_pose(subir_poquito)
        actualizar_posicion(subir_poquito)
        #Guarda en la BBDD
        enviar_log("Subiendo un poco después de soltar pieza en cinta", "Movimiento")
 
        #Corre la cinta
        robot.run_conveyor(conveyor_id, speed=50, direction=ConveyorDirection.FORWARD)
        #Guarda en la BBDD
        enviar_log("Corriendo cinta después de soltar pieza", "Cinta")
 
        while True:
            if stop_requested:
                break
            s1 = robot.digital_read(sensor1)
            s2 = robot.digital_read(sensor2)
 
            if s1 == PinState.HIGH and s2 == PinState.LOW:
                #Para la cinta
                robot.stop_conveyor(conveyor_id)
                #Guarda en la BBDD
                enviar_log("Pieza detectada en sensor 1, deteniendo cinta para paletizar", "Cinta")
                robot.wait(0.1)
 
                #Se mueve a atacar1
                robot.move_pose(atacar1)
                actualizar_posicion(atacar1)
                #Guarda en la BBDD
                enviar_log("Moviendo a posición de ataque para paletizar", "Movimiento")
 
                #Se mueve a atacar_abajo1
                robot.move_pose(atacar_abajo1)
                actualizar_posicion(atacar_abajo1)
                enviar_log("Bajando para agarrar pieza para paletizar", "Movimiento")
 
                #Cierra la pinza
                robot.close_gripper()
                #Guarda en la BBDD
                enviar_log("Cerrando pinza para agarrar pieza para paletizar", "Pinza")
 
                #Se mueve a subir_ataque
                robot.move_pose(subir_ataque)
                actualizar_posicion(subir_ataque)
                #Guarda en la BBDD
                enviar_log("Subiendo con pieza para paletizar", "Movimiento")
 
                #Se mueve a bajar_ataque1
                robot.move_pose(bajar_ataque1)
                actualizar_posicion(bajar_ataque1)
                #Guarda en la BBDD
                enviar_log("Bajando con la pieza a la posición de paletizado", "Movimiento")
 
                #Se mueve a subir_final_ataque1
                robot.move_pose(subir_final_ataque1)
                actualizar_posicion(subir_final_ataque1)
                #Guarda en la BBDD
                enviar_log("Subiendo después de paletizar", "Movimiento")
 
                #Abre la pinza
                robot.open_gripper()
                #Guarda en la BBDD
                enviar_log("Abriendo pinza para soltar pieza paletizada", "Pinza")
                break
 
            if s2 == PinState.LOW and s1 == PinState.LOW:
                #Para la cinta
                robot.stop_conveyor(conveyor_id)
                #Guarda en la BBDD
                enviar_log("Pieza detectada en sensor 2", "Sensor 2")
 
                #Corre la cinta hacia atrás
                robot.run_conveyor(conveyor_id, speed=50, direction=ConveyorDirection.BACKWARD)
                #Guarda en la BBDD
                enviar_log("Revirtiendo cinta para desechar pieza", "Cinta")
 
                robot.wait(15)
 
                #Para la cinta
                robot.stop_conveyor(conveyor_id)
                enviar_log("Deteniendo cinta después de desechar pieza", "Cinta")
                break
 
            robot.wait(0.02)
        paletizadas = paletizadas + 1
    ##fin bucle     
    ##fin bucle
    #robot.close_connection()

def get_paletizadas():
    return paletizadas

def stop_all():
    global stop_requested
    stop_requested = True
    print("STOP solicitado")

if __name__ == '__main__':
    main()