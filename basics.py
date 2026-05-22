from pyniryo import *

robot = NiryoRobot('172.16.190.27')
sensor1 = "DI5"
sensor2 = "DI1"

robot.calibrate_auto()
#robot.wait(10) si la calibración no se ha hecho
robot.update_tool()
conveyor_id = robot.set_conveyor()
print(conveyor_id)

#robot.update_tool()
#Inicialización de posiciones
inicio = PoseObject(x=0.140, y=0.000, z=0.203, roll=0.003, pitch=0.757, yaw=-0.001)
subir_abierto = PoseObject(x=0.155, y=-0.009, z=0.327, roll=0.460, pitch=1.505, yaw=0.547)
bajar1 = PoseObject(x=0.226, y=-0.194, z=0.221, roll=-3.037, pitch=1.344, yaw=-2.859)
bajar1_2 = PoseObject(x=0.221, y=-0.197, z=0.169, roll=3.087, pitch=1.312, yaw=3.131)
#bajar1_2 = PoseObject(x=0.205598, y=-193.400, z=96.275, roll=3.047, pitch=1.255, yaw=-3.141)
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

#Movimientos
for i in range (4):

    # 1. Robot toma la pieza y la pone en la cinta
    robot.release_with_tool()
    robot.move_pose(inicio)
    robot.move_pose(subir_abierto)
    robot.move_pose(bajar1)
    robot.move_pose(bajar1_2)
    robot.grasp_with_tool()
    robot.move_pose(subir_cerrado1)
    robot.move_pose(bajar1_3)
    robot.release_with_tool()
    robot.move_pose(subir_poquito)
    robot.run_conveyor(conveyor_id, speed=50, direction=ConveyorDirection.FORWARD)
    
    while True:
        s1 = robot.digital_read(sensor1)
        s2 = robot.digital_read(sensor2)
    
        #d5 abajo d1 arriba s1 abajo s2 arriba
        if s1 == PinState.LOW and s2 == PinState.HIGH:
            robot.stop_conveyor(conveyor_id)
            robot.wait(0.1)
            robot.move_pose (atacar1)
            robot.move_pose (atacar_abajo1)
            robot.grasp_with_tool()
            robot.move_pose (subir_ataque)
            robot.move_pose (bajar_ataque1)
            robot.move_pose (subir_final_ataque1)
            robot.release_with_tool()
            break

        if s2 == PinState.LOW and s1 == PinState.LOW:
            robot.stop_conveyor(conveyor_id)
            robot.run_conveyor(conveyor_id, speed=50, direction=ConveyorDirection.BACKWARD)
            robot.wait(15)
            robot.stop_conveyor(conveyor_id)
            break
        robot.wait(0.02)
        
##fin bucle
robot.close_connection()