from opcua import Client
from opcua import ua

from threading import Thread, Event, Timer
from time import sleep

from pid import PID

# client = Client()
# try:
#     client.connect()
#     objectsNode =  client.get_objects_node()
#     tanks = objectsNode.get_child(["2:Proceso_Tanques", "2:Tanques"])
#     print('Cliente OPCUA se ha conectado')
# except Exception as e:
#     print(e)
#     print('Cliente OPCUA no se ha conectado')
#     client.disconnect()

class AlarmHandler():
    def __init__(self, ctr):
        self.ctr = ctr

    def event_notification(self, event):
        # Event as defined in TanquesNamespace.py
        # Get event text
        _, name, val = event.Message.Text.split(":")
        
        # Get tank id (character following 'Tanque')
        id = name.split("Tanque")[-1][0]
        val = float(val)

        # Run callback
        self.ctr.blink_alarm(id, val)


class Controller():
    """
    Clase principal del controlador.
    
    Se manejan tres componentes principales:
        1. Conexión con el servidor OPC
            - Acceso a los nodos del proceso
            - Obtención de datos (tiempo, alturas, voltajes, etc.)
            - Publicación de datos
        2. Manejo del controlador PID definido en pid.py

    Esta clase NO maneja la interfaz con el usuario. Esta deberá
    acceder los metodos y atributos definidos aquí.

    TODO: Otro script de mas alta jerarquia que instancie tanto este
    controlador como el dashboard?

    """
    def __init__(self, url):
        # Client connection
        self.client = Client(url)
        self.client.connect()
        self.root_node = self.client.get_objects_node().get_child("2:Proceso_Tanques")

        # PIDs
        self.pid_on = False
        self.pid_starter = Event()
        self.pid_v1 = PID(1)
        self.pid_v2 = PID(2)
        self.pid_thread = Thread(target=self.run_pid, args=((lambda: self.pid_on), self.pid_starter))
        self.pid_thread.start()

        # Alarms state
        self.alarms = {"1": {"on": False, "val": 0},
                       "2": {"on": False, "val": 0},
                       "3": {"on": False, "val": 0},
                       "4": {"on": False, "val": 0}}
        self.alarm_timers = {"1": None, "2": None, "3": None, "4": None}

        # Alarm handler
        sub = self.client.create_subscription(10, AlarmHandler(self))
        sub.subscribe_events(self.root_node.get_child(["2:Alarmas", "2:Alarma_nivel"]))


    def close(self):
        self.client.disconnect()

    #######################
    # PID Interface

    @property
    def Kp(self):
        return self.pid_v1.Kp

    @property
    def Kd(self):
        return self.pid_v1.Kd

    @property
    def Ki(self):
        return self.pid_v1._Ki

    @property
    def antiwindup_on(self):
        return self.pid_v1.antiwindup_on

    @property
    def ref_h1(self):
        return self.pid_v1.reference

    @property
    def ref_h2(self):
        return self.pid_v2.reference

    def set_reference(self, h1=None, h2=None):
        if h1 is not None:
            self.pid_v1.set_reference(h1)
        if h2 is not None:
            self.pid_v2.set_reference(h2)

    def set_h1_ref(self, h1):
        if h1 is None:
            h1 = 0
        self.set_reference(h1=h1)

    def set_h2_ref(self, h2):
        if h2 is None:
            h2 = 0
        self.set_reference(h2=h2)

    def activate_pid(self, value):
        if value:
            print("PID Activated")
            self.pid_starter.set()
        else:
            print("PID deactivated")
        self.pid_on = value
    
    def set_Ki(self, value):
        if value is None:
            value = 0
        self.pid_v1.set_Ki(value)
        self.pid_v2.set_Ki(value)

    def set_Kd(self, value):
        if value is None:
            value = 0
        self.pid_v1.set_Kd(value)
        self.pid_v2.set_Kd(value)

    def set_Kp(self, value):
        if value is None:
            value = 0
        self.pid_v1.set_Kp(value)
        self.pid_v2.set_Kp(value)

    def activate_antiwindup(self, value):
        if value is None:
            value = False
        self.pid_v1.activate_antiwindup(value)
        self.pid_v2.activate_antiwindup(value)

    #######################
    # Ratios

    @property
    def gammas(self):
        return self.root_node.get_child("2:Razones")

    @property
    def gammas_vals(self):
        return {i: self.gammas.get_child([f"2:Razon{i}", "2:gamma"]).get_value() for i in (1, 2)}

    def set_gammas(self, g1=None, g2=None):
        if g1 is not None:
            self.gammas.get_child(["2:Razon1", "2:gamma"]).set_value(g1)
        if g2 is not None:
            self.gammas.get_child(["2:Razon2", "2:gamma"]).set_value(g2)

    def set_gamma1(self, g1):
        self.set_gammas(g1=g1)

    def set_gamma2(self, g2):
        self.set_gammas(g2=g2)    

    ########################
    # Heights

    @property
    def tanks(self):
        """Nodo que contiene a los tanques

        Returns:
            opcua.common.node.Node: Nodo '2:Tanques'
        """
        return self.root_node.get_child("2:Tanques")

    @property
    def heights(self):
        """Diccionario con el nodo correspondiente a la altura de cada tanque.
        El índice es el número del tanque, sea 1, 2, 3 o 4

        Returns:
            dict[i -> int] -> opcua.common.node.Node: Nodo '2:h' de cada tanque i
        """
        return {i: self.tanks.get_child([f"2:Tanque{i}", "2:h"]) for i in (1,2,3,4)}

    @property
    def heights_vals(self):
        """Diccionario con todas las alturas con sus tiempos asociados

            dict[i -> int] -> float
        """
        d = {}
        for i, h in self.heights.items():
            d[i] = h.get_value()
        return d

    @property
    def heights_timestamped(self):
        """Diccionario con todas las alturas con sus tiempos asociados

        Returns:
            dict[i -> int] -> dict['val': float, 't': time.timestamp]: Datos para cada tanque
        """
        d = {}
        for i, h in self.heights.items():
            d[i] = {"val": h.get_value(), "t": self.timestamp}
        return d

    ######################
    # Voltages

    @property
    def pumps(self):
        return self.root_node.get_child("2:Valvulas")

    @property
    def voltages(self):
        return {i: self.pumps.get_child([f"2:Valvula{i}", "2:u"]) for i in (1,2)}

    @property
    def voltages_vals(self):
        """Diccionario con todos los voltajes

        dict[i -> int] -> float
        """
        d = {}
        for i, v in self.voltages.items():
            d[i] = v.get_value()
        return d

    @property
    def voltages_timestamped(self):
        """Diccionario con todos los voltajes con sus tiempos asociados

        Returns:
            dict[i -> int] -> dict['val': float, 't': time.timestamp]: Datos para cada bomba
        """
        d = {}
        for i, v in self.voltages.items():
            d[i] = {"val": v.get_value(), "t": self.timestamp}
        return d

    def set_voltages(self, v1=None, v2=None):
        voltage_nodes = self.voltages
        if v1 is not None:
            voltage_nodes[1].set_value(v1)
        if v2 is not None:
            voltage_nodes[2].set_value(v2)

    def set_voltage1(self, v1):
        self.set_voltages(v1=v1)

    def set_voltage2(self, v2):
        self.set_voltages(v2=v2)

    ######################
    # Alarm

    def blink_alarm(self, id, val):

        # Cancel previous timers
        if self.alarm_timers[id]:
            self.alarm_timers[id].cancel()

        # Set state and start new timer to reset state
        self.alarms[id] = {"on": True, "val":val}
        timer = Timer(2, self.__reset_alarm, (id, ))
        self.alarm_timers[id] = timer
        timer.start()


    def __reset_alarm(self, id):
        self.alarms[id] = {"on": False, "val":0}

    ######################
    # PID worker (attention: threaded!)

    def run_pid(self, pid_on, event):
        while True:
            event.wait()
            event.clear()
            while pid_on():
                h1, h2, h3, h4 = self.heights_vals.values()

                self.pid_v1.add_sample(h1)
                self.pid_v2.add_sample(h2)

                v1 = self.pid_v1.output
                v2 = self.pid_v2.output

                self.set_voltages(v1=v1, v2=v2)

    #######################
    # Miscellaneous

    @property
    def time_node(self):
        return self.client.get_objects_node().get_child(["0:Server", "0:ServerStatus", "0:CurrentTime"])

    @property
    def time(self):
        return self.time_node.get_value()

    @property
    def timestamp(self):
        return self.time.timestamp()


######################
# Utilities

global depth # For pretty-printing
depth = 0

def explore(node):
    """Recorre nodo y sus hijos recursivamente e imprime sus nombres y valores

    Args:
        node (opcua.common.node.Node): Nodo raíz
    """
    global depth
    children = node.get_children()

    # If no children, then is leaf (recursive base case)
    if children:
        for child in children:
            # Print name and value if present
            try:
                print("\t"*depth + f"{child.get_browse_name()} : {child.get_value()}")
            except:
                print(child.get_browse_name())

            # Recursively explore children
            depth += 1
            explore(child)
            depth -= 1

def get_controller(url):
    return Controller(url)

if __name__ == "__main__":
    c = Controller("opc.tcp://localhost:4840/freeopcua/server/")
