# import threading
# import time
#
# a = 0
#
# def Interfaz():
#     global a
#     while True:
#         print('Interfaz')
#         print(a)
#         time.sleep(0.5)
#
# def Controlador(b):
#     # recibir las variables de OPC
#     #Calcula las acciones de control
#     # Envìa las acciones por pid
#     global a
#     while True:
#         print('PID')
#         time.sleep(0.2)
#         a += 1
#
#
# PID_thread = threading.Thread(target=PID)
#
# PID_thread.start()
# PID_thread.daemon
#
# Interfaz()

import pandas as pd
import numpy as np

a = {'h1': [1,2,3,4], 'h2': [11,2,4,5]}
a = pd.DataFrame(a)
print(a)

pd.to_pickle(a, 'dhosadi.pkl')
a.to_csv('kjdsfhk.csv')
a.to_csv(r'pandas.txt', header=True, index=None, sep=' ', mode='a')
