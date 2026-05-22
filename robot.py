import time
from pyniryo import *
import requests
from conexionBBDD import *

URL = "http://127.0.0.1:5000/insertaenlog"

def enviar_log(instruccion, elemento):
    try:
        data = [instruccion, elemento]
        r = requests.post(URL, json=data, timeout=3)
        return r.status_code == 202
    except requests.exceptions.RequestException:
        return False
    
#Configuración de la base de datos
usar_database = True
user = "vgarled"
password = "vgarled"

if usar_database:
    print("=== INTENTANDO CONECTAR A ORACLE ===")
    conexion = conectar(user, password)
    print(f"=== CONEXION RESULTADO: {conexion} ===")
else:
    conexion = None

robot = NiryoRobot("172.16.190.27")
sensor1 = "DI5"
sensor2 = "DI1"
conveyor_id = robot.set_conveyor()
paletizadas = 0
desechos = 0
stop_requested = False

def PoseMM(x, y, z, roll, pitch, yaw):
    return PoseObject(x/1000, y/1000, z/1000, roll, pitch, yaw)

inicio = PoseObject(x=0.140, y=0.000, z=0.203, roll=0.003, pitch=0.757, yaw=-0.001)
subir_abierto = PoseObject(x=0.155, y=-0.009, z=0.327, roll=0.460, pitch=1.505, yaw=0.547)
bajar1 = PoseObject(x=0.226, y=-0.194, z=0.221, roll=-3.037, pitch=1.344, yaw=-2.859)
#bajar1_2 = PoseObject(x=0.221, y=-0.197, z=0.169, roll=3.087, pitch=1.312, yaw=3.131)
bajar1_2 = PoseMM(x=205.598, y=-193.400, z=96.275, roll=3.047, pitch=1.255, yaw=-3.141)
#bajar_poquito = PoseMM(x=198.594, y=-191.827, z=84.534, roll=2.963, pitch=1.108, yaw=3.004)
bajar_poquito = PoseMM(x=199.920, y=-195, z=83.380, roll=2.976, pitch=1.161, yaw=3.066)
#close gripper
#subir_cerrado1 = PoseObject(x=0.165, y=-0.146, z=0.355, roll=-0.291, pitch=1.088, yaw=-0.548)
subir_poquito = PoseMM(x=213.905, y=-192.829, z=142.905, roll=-2.955, pitch=1.284, yaw=-2.916)
dejar_1 = PoseMM(x=289.367, y=-168.746, z=103.316, roll=2.908, pitch=1.455, yaw=2.922)
#bajar1_3 = PoseObject(x=0.278, y=-0.212, z=0.186, roll=0.481, pitch=1.406, yaw=0.547)
#open gripper
subir_poquito_after_dejar = PoseObject(x=0.277, y=-0.198, z=0.213, roll=-0.647, pitch=1.481, yaw=-0.606)
atacar1 = PoseObject(x=0.287, y=0.135, z=0.174, roll=2.765, pitch=1.471, yaw=2.727)
#atacar_abajo1 = PoseObject(x=0.288, y=0.136, z=0.156, roll=2.762, pitch=1.476, yaw=2.698)
atacar_abajo1 = PoseMM(x=282.881, y=139.216, z=66.682, roll=3.097, pitch=1.363, yaw=3.016)
#subir_ataque = PoseObject(x=0.216, y=0.219, z=0.316, roll=-1.533, pitch=1.513, yaw=-0.612)
subir_ataque1 = PoseMM(x=252.651, y=128.163, z=178.479, roll=2.858, pitch=1.446, yaw=2.951)
#bajar_ataque1 = PoseObject(x=0.076, y=0.227, z=0.157, roll=2.622, pitch=1.534, yaw=-2.155)
dejar_pieza1 = PoseMM(x=4.733, y=225.610, z=66.850, roll=-1.523, pitch=1.532, yaw=-0.124)
dejar_pieza2 = PoseMM(x=65.194, y=226.558, z=65.278, roll=-2.309, pitch=1.534, yaw=-0.772)
dejar_pieza3 = PoseMM(x=59.064, y=153.231, z=64.452, roll=-1.881, pitch=1.493, yaw=-0.407)
dejar_pieza4 = PoseMM(x=2.416, y=162.294, z=63.619, roll=2.264, pitch=1.550, yaw=-2.022)
#subir_final_ataque1 = PoseObject(x=0.100, y=0.206, z=0.282, roll=0.239, pitch=1.522, yaw=1.409)
subir_final_pieza1 = PoseMM(x=9.420, y=166.641, z=211.837, roll=-1.051, pitch=1.477, yaw=-0.394)

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
        if conexion:
            insertar_robot(conexion, "Niryo", "Niryo", 1)
    except Exception as e:
        print(f"Error en calibración: {e}")
    #robot.calibrate_auto()
    #robot.wait(10) si la calibración no se ha hecho
    #conveyor_id = robot.set_conveyor()
    
def run_conv(velocidad=50):
    if conveyor_id:
        robot.run_conveyor(conveyor_id, speed=velocidad, direction=ConveyorDirection.FORWARD)
        enviar_log(f"Corriendo Cinta al {velocidad}%", "Cinta")
        if conexion:
            insertar_cinta(conexion, "FORWARD", velocidad, 1)
        
def stop_conv():
    if conveyor_id:
        robot.stop_conveyor(conveyor_id)
    enviar_log("Cinta Detenida", "Cinta")
    if conexion:
        insertar_cinta(conexion, "STOP", 0, 0)

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
        if conexion:
            insertar_movimiento(conexion, pose_object.x, pose_object.y, pose_object.z, pose_object.pitch, pose_object.roll, pose_object.yaw)
    except Exception as e:
        print(f"No se pudo actualizar la posición: {e}")
    
def close_DB():
    global usar_database, conexion

    if usar_database and conexion is not None:
        try:
            desconectar(conexion)
        except Exception as e:
            print(f"Error al intentar cerrar la BD: {e}")
        finally:
            usar_database = False
            conexion = None

def main():
    inicializar_robot()
    enviar_log("Robot inicializado", "Sistema")
    global paletizadas
    global desechos
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
        enviar_log("Bajando para agarrar pieza", "Movimiento")

        #Se mueve a bajar_poquito
        robot.move_pose(bajar_poquito)
        actualizar_posicion(bajar_poquito)
        #Guarda en la BBDD
        enviar_log("Posicionando agarrar pieza", "Movimiento")
 
        #Cierra pinza
        robot.close_gripper()
        #Guarda en la BBDD
        enviar_log("Cerrando pinza para agarrar pieza", "Pinza")
 
        #Se mueve a subir_poquito
        robot.move_pose(subir_poquito)
        actualizar_posicion(subir_poquito)
        #Guarda en la BBDD
        enviar_log("Subiendo con pieza agarrada", "Movimiento")
 
        #Se mueve a dejar_1
        robot.move_pose(dejar_1)
        actualizar_posicion(dejar_1)
        #Guarda en la BBDD
        enviar_log("Moviendo a posición para soltar pieza en cinta", "Movimiento")
 
        #Abre pinza
        robot.open_gripper()
        #Guarda en la BBDD
        enviar_log("Abriendo pinza para soltar pieza en cinta", "Pinza")
 
        #Se mueve a subir_poquito_after_dejar
        robot.move_pose(subir_poquito_after_dejar)
        actualizar_posicion(subir_poquito_after_dejar)
        #Guarda en la BBDD
        enviar_log("Subiendo un poco después de soltar pieza en cinta", "Movimiento")
 
        #Corre la cinta
        robot.run_conveyor(conveyor_id, speed=70, direction=ConveyorDirection.FORWARD)
        #Guarda en la BBDD
        enviar_log("Corriendo cinta después de soltar pieza", "Cinta")
        if conexion:
            insertar_cinta(conexion, "FORWARD", 70, 1)
 
        while True:
            if stop_requested:
                break
            s1 = robot.digital_read(sensor1)
            s2 = robot.digital_read(sensor2)
 
            if s1 == PinState.LOW and s2 == PinState.HIGH:
                if conexion:
                    insertar_sensor(conexion, 1)
                #Para la cinta
                robot.stop_conveyor(conveyor_id)
                #Guarda en la BBDD
                enviar_log("Pieza detectada en sensor 1, deteniendo cinta para paletizar", "Cinta")
                if conexion:
                    insertar_cinta(conexion, "STOP", 0, 0)
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
                robot.move_pose(subir_ataque1)
                actualizar_posicion(subir_ataque1)
                #Guarda en la BBDD
                enviar_log("Subiendo con pieza para paletizar", "Movimiento")

                if paletizadas == 0:
                    #Se mueve a dejar_pieza1
                    robot.move_pose(dejar_pieza1)
                    actualizar_posicion(dejar_pieza1)
                    #Guarda en la BBDD
                    enviar_log("Dejando la pieza en la posición de paletizado", "Movimiento")
                elif paletizadas == 1 :
                    robot.move_pose(dejar_pieza2)
                    actualizar_posicion(dejar_pieza2)
                    #Guarda en la BBDD
                    enviar_log("Dejando la pieza 1 en la posición de paletizado", "Movimiento")    
                elif paletizadas == 2 :
                    robot.move_pose(dejar_pieza3)
                    actualizar_posicion(dejar_pieza3)
                    #Guarda en la BBDD
                    enviar_log("Dejando la pieza 2 en la posición de paletizado", "Movimiento")    
                elif paletizadas == 3:
                    robot.move_pose(dejar_pieza4)
                    actualizar_posicion(dejar_pieza4)
                    #Guarda en la BBDD
                    enviar_log("Dejando la pieza 3 en la posición de paletizado", "Movimiento")

                #Abre la pinza
                robot.open_gripper()
                #Guarda en la BBDD
                enviar_log("Abriendo pinza para soltar pieza paletizada", "Pinza")
 
                #Se mueve a subir_final_ataque1
                robot.move_pose(subir_final_pieza1)
                actualizar_posicion(subir_final_pieza1)
                #Guarda en la BBDD
                enviar_log("Subiendo después de paletizar", "Movimiento")
                paletizadas = paletizadas + 1

                break
 
            if s2 == PinState.LOW and s1 == PinState.LOW:
                if conexion:
                    insertar_sensor(conexion, 1)
                #Para la cinta
                robot.stop_conveyor(conveyor_id)
                #Guarda en la BBDD
                enviar_log("Pieza detectada en sensor 2", "Sensor 2")
                if conexion:
                    insertar_cinta(conexion, "STOP", 0, 0)
 
                #Corre la cinta hacia atrás
                robot.run_conveyor(conveyor_id, speed=70, direction=ConveyorDirection.BACKWARD)
                #Guarda en la BBDD
                enviar_log("Revirtiendo cinta para desechar pieza", "Cinta")
                if conexion:
                    insertar_cinta(conexion, "BACKWARD", 70, 1)
 
                robot.wait(13)
 
                #Para la cinta
                robot.stop_conveyor(conveyor_id)
                enviar_log("Deteniendo cinta después de desechar pieza", "Cinta")
                if conexion:
                    insertar_cinta(conexion, "STOP", 0, 0)

                desechos = desechos + 1
                break
 
            #robot.wait(0.02)
        ##fin bucle     
    ##fin bucle
    #robot.close_connection()

def get_paletizadas():

    return paletizadas
def get_desechos():
    return desechos

def stop_all():
    global stop_requested
    stop_requested = True
    print("STOP solicitado")

if __name__ == '__main__':
    main()