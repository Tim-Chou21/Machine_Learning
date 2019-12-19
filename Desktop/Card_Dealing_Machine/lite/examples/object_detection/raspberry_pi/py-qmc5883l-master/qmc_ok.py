#sudo pip install qmc5883l
import py_qmc5883l
sensor = py_qmc5883l.QMC5883L()
while True:
    m = sensor.get_magnet()
    print(m)
    #x = sensor.get_bearing()
    #print(x)
    #y = sensor.get_calibration()
    #print(y)
