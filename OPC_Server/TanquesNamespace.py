from opcua import ua, Server
import time
import threading
from opcua.server.history_sql import HistorySQLite
import os
import random

'''
*********************************************** Servidor OPC-UA ***********************************************************

Implementación del servidor completo para la aplicación de los cuatro tanques. 
El servidor presenta las siguientes funcionalidades:
    - Data modeling -> Todas las variables están representadas como objetos y guardadas de manera ordenada
    - Suscripción a eventos -> El servidor está constantemente monitoreando los niveles de los estanques, en caso de que
                                estos alcancen un nivel crítico o temperatura elevada, manda alarmas a todos los clientes
                                suscritos a estos eventos
    - Buffer circular -> En un buffer circular se guarda el historial inmediato de las variables, útil para el preprocesamiento
                        edge y por batch, el cliente después solo debe leer estas variables.
'''
# Subscription Handler
class SubHandler(object):

    """
    Subscription Handler. To receive events from server for a subscription
    """
    def __init__(self, th, dir):
        self.th = th
        self.dir = dir

    def datachange_notification(self, node, val, data):
        thread_handler = threading.Thread(target=funcion_handler, args=(node, val, self.th, self.dir))
        thread_handler.start()
        #print("Python: New data change event", node, val)

    def event_notification(self, event):
        print("Python: New event", event)


mensaje_alarma = ''
alarma1 = False
alarma2 = False
alarma3 = False
alarma4 = False
valor_alarma = 0
def funcion_handler(node, val, th, dir):
    global mensaje_alarma, alarma1,alarma2, alarma3, alarma4, valor_alarma
    padre = node.get_parent().get_display_name().Text
    if (dir == 'menor' and val <= th) or (dir == 'mayor' and val >= th):
        if padre == 'Tanque1':
            alarma1 = True
        elif padre == 'Tanque2':
            alarma2 = True
        elif padre == 'Tanque3':
            alarma3 = True
        elif padre == 'Tanque4':
            alarma4 = True
        variable = node.get_display_name().Text
        mensaje_alarma = 'Alarma en: {}-{} valor: {}'.format(padre, variable, val)
        valor_alarma = int(val)
    else:
        if padre == 'Tanque1':
            alarma1 = False
        elif padre == 'Tanque2':
            alarma2 = False
        elif padre == 'Tanque3':
            alarma3 = False
        elif padre == 'Tanque4':
            alarma4 = False


class TanquesNamespace:
    def __init__(self, objects, idx, server):
        self.server = server
        self.objects = objects
        self.idx = idx
        ################################### Llenado del address space ##########################################################
        T_init = 22
        H_init = 50

        # Carpeta principal
        proceso_tanques = self.objects.add_folder(self.idx, 'Proceso_Tanques')

        # Tanques
        Tanques = proceso_tanques.add_folder(self.idx, 'Tanques')
        Tanque1 = Tanques.add_object(self.idx, 'Tanque1')
        Tanque2 = Tanques.add_object(self.idx, 'Tanque2')
        Tanque3 = Tanques.add_object(self.idx, 'Tanque3')
        Tanque4 = Tanques.add_object(self.idx, 'Tanque4')
        self.Tanques_list = [Tanque1, Tanque2, Tanque3, Tanque4]
        self.niveles = []
        self.temperaturas = []
        for Tanque in self.Tanques_list:
            var = Tanque.add_variable(self.idx, 'h', H_init)
            var2 = Tanque.add_variable(self.idx, 'T', T_init)
            var.set_writable()
            var2.set_writable()
            self.niveles.append(var)
            self.temperaturas.append(var2)

        # Pumps
        Valvulas = proceso_tanques.add_folder(self.idx, 'Valvulas')
        Valvula1 = Valvulas.add_object(self.idx, 'Valvula1')
        Valvula2 = Valvulas.add_object(self.idx, 'Valvula2')
        self.Valvulas_list = [Valvula1, Valvula2]
        self.u_Valvulas = []
        for Valvula in self.Valvulas_list:
            var = Valvula.add_variable(self.idx, 'u', 0.4)
            var.set_writable()
            self.u_Valvulas.append(var)

        # Razones
        Razones = proceso_tanques.add_folder(self.idx, 'Razones')
        Razon1 = Razones.add_object(self.idx, 'Razon1')
        Razon2 = Razones.add_object(self.idx, 'Razon2')
        self.Razones_list = [Razon1, Razon2]
        self.u_Razones = []
        for Razon in self.Razones_list:
            var = Razon.add_variable(self.idx, 'gamma', 0.35)
            var.set_writable()
            self.u_Razones.append(var)


        ############################################ Eventos y alarmas ########################################################
        '''
        Servidor se suscribe a cambios en el nivel de los tanques y temperaturas, 
         de manera que si el nivel es inferior a un threshold dispara una alarma
        '''
        # Creación de la alarma
        alarmas = proceso_tanques.add_folder(self.idx, 'Alarmas')
        obj = alarmas.add_object(self.idx, 'Alarma_nivel')
        alarm_type = self.server.create_custom_event_type(self.idx, 'Alarma_nivel', ua.ObjectIds.BaseEventType,
                                                [('Nivel', ua.VariantType.Float),
                                                 ('Mensaje', ua.VariantType.String)])


        self.alarma_nivel = self.server.get_event_generator(alarm_type, obj)


        # Se inicial el buffer para guardar datos recientes de cada una de las variables y poder hacer preprocesamiento por batch
        directorio = 'historial'
        if not os.path.exists(directorio):
            os.makedirs(directorio)

        db = HistorySQLite("{}/Tanques_historial.sql".format(directorio))
        self.server.iserver.history_manager.set_storage(db) # Se dice que en esta base de datos se guardará el historial



    def subscripciones(self):
        # Suscripción a los cambios de valor de los niveles y temperaturas simuladas
        th1 = 10
        th2 = 40
        handler_niveles = SubHandler(th1, 'menor') # Qué es lo que activa la alarma
        handler_temperaturas = SubHandler(th2, 'mayor')

        sub_niveles = self.server.create_subscription(100, handler_niveles) # Revisa cada 1000 milisegundos la variables
        sub_temperaturas = self.server.create_subscription(100, handler_temperaturas)


        for i in range(len(self.niveles)): # FInalmente se realizan las subscripciones
            sub_niveles.subscribe_data_change(self.niveles[i])
            sub_temperaturas.subscribe_data_change(self.temperaturas[i])

        # Subscripción de variables cuyo historial será monitorieado
        cantidad_guardada = 100
        for i in range(len(self.niveles)):
            self.server.historize_node_data_change(self.niveles[i], period=None, count=cantidad_guardada)
            self.server.historize_node_data_change(self.temperaturas[i], period=None, count=cantidad_guardada)

    def monitorea_alarma(self):
        global alarma, valor_alarma, mensaje_alarma
        if alarma1 or alarma2 or alarma3 or alarma4:
            self.alarma_nivel.event.Message = ua.LocalizedText("Alarma")
            self.alarma_nivel.event.Severity = valor_alarma
            self.alarma_nivel.event.Nivel = float(valor_alarma)
            self.alarma_nivel.event.Mensaje = mensaje_alarma
            self.alarma_nivel.trigger(message=mensaje_alarma)
            #print(self.alarma_nivel)
