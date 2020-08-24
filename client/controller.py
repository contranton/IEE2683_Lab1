from opcua import Client
from opcua import ua

from threading import Thread, Event

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
        self.client = Client(url)
        self.client.connect()
        self.root_node = self.client.get_objects_node().get_child("2:Proceso_Tanques")

        self.pid_on = False
        self.pid_semaphore = Event()
        self.pid_v1 = PID()
        self.pid_v2 = PID()
        self.pid_thread = Thread(target=self.pid_thread, args=(self.pid_semaphore,))

    def close(self):
        self.client.disconnect()

    #######################
    # PID Interface

    def set_reference(self, h1=None, h2=None):
        if h1 is not None:
            self.pid_v1.set_reference(h1)
        if h2 is not None:
            self.pid_v2.set_reference(h1)

    def activate_pid(self):
        self.pid_on = True
    
    def set_Ki(self, value):
        self.pid_v1.set_Ki(value)
        self.pid_v2.set_Ki(value)

    def set_Kd(self, value):
        self.pid_v1.set_Kd(value)
        self.pid_v2.set_Kd(value)

    def set_Kp(self, value):
        self.pid_v1.set_Kp(value)
        self.pid_v2.set_Kp(value)

    def activate_windup(self, value):
        self.pid_v1.activate_windup(value)
        self.pid_v2.activate_windup(value)

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
    # PID worker (attention: threaded!)

    def pid_thread(self, event):
        while True:
            if not self.pid_on:
                event.wait()
                continue
            v1 = self.pid_v1.output
            v2 = self.pid_v2.output
            self.set_voltages(v1=v1, v2=v2)

    #######################
    # Miscellaneous

    @property
    def gammas(self):
        return self.root_node.get_child("2:Razones")

    @property
    def time(self):
        return self.client.get_objects_node().get_child(["0:Server", "0:ServerStatus", "0:CurrentTime"]).get_value()

    @property
    def timestamp(self):
        return self.time.timestamp()

    ######################
    # I/O

    def write_data(self):
        pass

    def calculate_control(self):
        pass


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