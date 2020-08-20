#-*- encoding: utf-8 -*-

from opcua import ua, Server
import time
import threading
from threading import Thread
from opcua.server.history_sql import HistorySQLite
import os
import random
from TanquesNamespace import TanquesNamespace
#from Espesador.EspesadorNamesPace import EspesadorNamespace

'''
En este script se maneja el Servidor OPC, el cual va a contener los distintos Namespaces de la apliación
'''


class Servidor_OPCUA:
    def __init__(self):
        self.server = Server()
        self.server.set_endpoint("opc.tcp://localhost:4840/freeopcua/server/")
        self.server.set_server_name("Stack IIoT")
        self.namespaces = {}
        self.objects = self.server.get_objects_node()

    # Para agregar un nuevo namespace
    def new_namespace(self, uri, namespace, nombre):
        idx = self.server.register_namespace(uri)
        print('New namespace: {}'.format(idx))
        Namespace = namespace(self.objects, idx, self.server) # Se declaran todas las variables del nuevo namespace
        self.namespaces[nombre] = Namespace


    def start(self):
        global alarma, valor_alarma, mensaje_alarma
        self.server.start()
        print("Server started")
        for nombre, namespace in self.namespaces.items():
            namespace.subscripciones()
        # Se incia el loop del servidor
        try:
            while True:
                time.sleep(0.1)
                for nombre, namespace in self.namespaces.items():
                    namespace.monitorea_alarma()
        finally:
            self.server.stop()



server = Servidor_OPCUA()
server.new_namespace(uri='Tanques', namespace=TanquesNamespace, nombre='Tanques')
#server.new_namespace(uri='Espesador', namespace=EspesadorNamespace, nombre='Espesador')
#server_thread = Thread(target=server.start)
#server_thread.start()
server.start()

