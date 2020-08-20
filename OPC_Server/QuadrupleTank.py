import numpy as np
from scipy.integrate import odeint
import scipy.integrate as integrator
import matplotlib.pyplot as plt
import pygame
import time
import sys
from cliente import Cliente # cliente OPCUA
import random
import threading

class QuadrupleTank():
    def __init__(self, x0, Hmax, voltmax):
        self.x0 = x0
        self.t = 0

        # Parámetros
        self.A = [28, 32, 28, 32] # cm^2
        self.a = [0.071, 0.057, 0.071, 0.057] # cm^2
        self.g = 981 # cm/s^2
        self.rho = 1 # g/cm^3
        self.kout = 0.5
        self.kin = 3.33
        
        self.time_scaling = 1
        self.gamma = [0.7, 0.6] # %
        self.volt = [0., 0.] # %
        self.voltmax = voltmax
        self.x = self.x0
        self.ti = 0
        self.Ts = 0
        self.Hmax = Hmax
        self.Hmin = 0.0

    # Restricciones físicas de los tanques
    def Limites(self):
        for i in range(len(self.x)):
            if self.x[i] > self.Hmax:
                self.x[i] = self.Hmax
            elif self.x[i] <1e-2:
                self.x[i] = 1e-2

        for i in range(2):
            if self.volt[i] > 1:
                self.volt[i] = 1
            elif self.volt[i] < -1:
                self.volt[i] = -1

    # Ecuaciones diferenciales de los tanques
    def xd_func(self, x, t):
        xd0 = -self.a[0]/self.A[0]*np.sqrt(2*self.g*x[0]) + self.a[2]/self.A[0]*np.sqrt(2*self.g*x[2]) + self.gamma[0]*self.kin*self.volt[0]*self.voltmax/self.A[0]
        xd1 = -self.a[1]/self.A[1]*np.sqrt(2*self.g*x[1]) + self.a[3]/self.A[1]*np.sqrt(2*self.g*x[3]) + self.gamma[1]*self.kin*self.volt[1]*self.voltmax/self.A[1]
        xd2 = -self.a[2]/self.A[2]*np.sqrt(2*self.g*x[2]) + (1 - self.gamma[1])*self.kin*self.volt[1]*self.voltmax/self.A[2]
        xd3 = -self.a[3]/self.A[3]*np.sqrt(2*self.g*x[3]) + (1 - self.gamma[0])*self.kin*self.volt[0]*self.voltmax/self.A[3]
        res = [xd0, xd1, xd2, xd3]
        for i in range(len(res)):

            if np.isnan(res[i]) or type(res[i]) != np.float64:
                res[i] = 0
        return np.multiply(self.time_scaling, res)

    # Integración en "tiempo real"
    def sim(self):
        self.x0 = np.array(self.x) # Estado actual se vuelve condición inicial para el nuevo estado
        self.Ts = time.time() - self.ti
        #self.Ts = 0.01
        t = np.linspace(0, self.Ts, 2)
        x = odeint(self.xd_func, self.x0, t)  # Perform integration using Fortran's LSODA (Adams & BDF methods)
        self.x = [x[-1, 0], x[-1,1], x[-1, 2], x[-1, 3]]
        self.Limites()
        #print(self.x)
        self.ti = time.time()
        return self.x



# series = []
# sistema = QuadrupleTank(x0=[50,50,50,50], Hmax=50, voltmax=50)
# sistema.time_scaling = 100 # Para el tiempo
#
# for i in range(2000):
#     series.append(sistema.sim())
# series = np.array(series)
# print(series.shape)
# plt.figure()
# plt.plot(series[:,0], label='Tanque1')
# plt.plot(series[:,1], label='Tanque2')
# plt.plot(series[:,2], label='Tanque3')
# plt.plot(series[:,3], label='Tanque4')
# plt.legend()
# plt.show()
#
# np.save('alturas.npy', series)

class Interfaz_grafica():

    def __init__(self, Hmax):
        self.width = 640
        self.height = 480
        pygame.init()
        # pygame.display.set_mode()
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.background = pygame.Surface(self.screen.get_size()).convert() # Surface para el background
        self.background.fill((255,255,255)) # fill background white
        self.textSurf = pygame.Surface(self.screen.get_size(),  pygame.SRCALPHA, 32).convert_alpha()
        pygame.display.set_caption('Watertank Sim')
        pygame.key.set_repeat(1, 50)
        self.altura_max_tanque = Hmax
        self.font = pygame.font.SysFont("comicsansms", 20)
        self.font.set_bold(True)
        self.font2 = pygame.font.SysFont("comicsansms", 15)
        self.font2.set_bold(True)

        self.colorBorde = (64,64,64)
        self.colorAgua = (0,0,255)
        self.colorPipe = (0, 0, 0)
        self.colorPump = (255,128,0)
        self.colorllave = (153,153,0)
        self.colorVacio = (255,255,255)

        self.pump1_ant = 0
        self.pump2_ant = 0
        self.switch1_ant = 0
        self.switch2_ant = 0

    # Se pinta y se posiciona cada una de las figuta en la interfaz
    def paint(self):
        """painting on the surface"""
        # Piscina
        self.posPiscina = (70, 400, 500, 50)
        self.Piscina = pygame.draw.rect(self.background, self.colorAgua, self.posPiscina)  # rect: (x1, y1, width, height)
        self.PiscinaB = pygame.draw.rect(self.background, self.colorBorde, self.posPiscina, 4)  # rect: (x1, y1, width, height)

        # Tank1
        self.posTank1 = (170, 250,70,120)
        self.Tank1B = pygame.draw.rect(self.background, self.colorBorde, self.posTank1 , 4)  # rect: (x1, y1, width, height)
        pygame.draw.rect(self.background, self.colorBorde, (170 + 30, 250 + 120, 10,20), 4)
        self.textSurf.blit(self.font.render('T1', True, (0, 0, 0)), (self.posTank1[0], self.posTank1[1]))


        # Tank2
        self.posTank2 = (400, 250, 70, 120)
        self.Tank2B = pygame.draw.rect(self.background, self.colorBorde, self.posTank2, 4)
        pygame.draw.rect(self.background, self.colorBorde, (400 + 30, 250 + 120, 10, 20), 4)
        self.textSurf.blit(self.font.render('T2', True, (0, 0, 0)), (self.posTank2[0], self.posTank2[1]))


        # Tank3
        self.posTank3 = (170, 70, 70, 120)
        self.Tank3B = pygame.draw.rect(self.background, self.colorBorde, self.posTank3, 4)
        pygame.draw.rect(self.background, self.colorBorde, (170 + 30, 70 + 120, 10, 20), 4)
        self.textSurf.blit(self.font.render('T3', True, (0, 0, 0)), (self.posTank3[0], self.posTank3[1]))


        # Tank4
        self.posTank4 = (400, 70, 70, 120)
        self.Tank4B = pygame.draw.rect(self.background, self.colorBorde, self.posTank4, 4)
        pygame.draw.rect(self.background, self.colorBorde, (400 + 30, 70 + 120, 10, 20), 4)
        self.textSurf.blit(self.font.render('T4', True, (0, 0, 0)), (self.posTank4[0], self.posTank4[1]))

        # Pipe1
        puntosPipe1 = [(120, 420), (120, 10), (435,10), (435, 70)]
        self.pipe1 = pygame.draw.lines(self.background, self.colorPipe, False, puntosPipe1, 10)

        # Pipe2
        puntosPipe2 = [(520, 420), (520, 30), (205, 30), (205, 70)]
        self.pipe2 = pygame.draw.lines(self.background, self.colorPipe, False, puntosPipe2, 10)

        # Pipe3
        puntosPipe3 = [(120, 220), (205, 220), (205, 250)]
        self.pipe3 = pygame.draw.lines(self.background, self.colorPipe, False, puntosPipe3, 10)

        # Pipe4
        puntosPipe4 = [(520, 220), (435, 220), (435, 250)]
        self.pipe4 = pygame.draw.lines(self.background, self.colorPipe, False, puntosPipe4, 10)

        # Pump1
        self.centroPump1 = (120, 320)
        self.Pump1 = pygame.draw.circle(self.background, self.colorPump, self.centroPump1, 20)
        self.Pump1p1 = (100,320)
        self.Pump1p2 = (140, 320)
        pygame.draw.line(self.background, self.colorPipe, self.Pump1p1, self.Pump1p2, 4)
        string = '{}'.format(round(0.000, 3))
        pygame.draw.rect(self.textSurf, self.colorVacio, (self.centroPump1[0] - 80, self.centroPump1[1], 60, 20))
        self.textSurf.blit(self.font2.render(string, True, (200, 0, 0)),
                           (self.centroPump1[0] - 80, self.centroPump1[1]))

        # Pump2
        self.centroPump2 = (520, 320)
        self.Pump2p1 = (500, 320)
        self.Pump2p2 = (540, 320)
        self.Pump2 = pygame.draw.circle(self.background, self.colorPump, self.centroPump2, 20)
        pygame.draw.line(self.background, self.colorPipe, self.Pump2p1, self.Pump2p2, 4)
        string = '{}'.format(round(0.00, 3))
        pygame.draw.rect(self.textSurf, self.colorVacio,
                         (self.centroPump2[0] + 30, self.centroPump2[1], 70, 20))
        self.textSurf.blit(self.font2.render(string, True, (200, 0, 0)),
                           (self.centroPump2[0] + 30, self.centroPump2[1]))

        # Llave1
        llave1pos = (105,210,30,20)
        self.centrollave1 = (105, 210)
        pygame.draw.ellipse(self.background, self.colorllave, llave1pos)

        # Llave2
        llave2pos = (505, 210, 30, 20)
        self.centrollave2 = (505, 210)
        pygame.draw.ellipse(self.background, self.colorllave, llave2pos)


    # De acuerdo a las ecuaciones diferenciales se van actualizando los dibujos de los tanques
    def Tank_update(self, altura, posicion):
        #posicion :(x,y,width, heigt)
        aux = list(posicion) # Se pasa a lista para poder cambiar los valores
        aux[3] = (aux[3]*altura)/self.altura_max_tanque #height de agua
        aux[1] = aux[1] + posicion[3] - aux[3] # Y + H-h
        aux = tuple(aux)
        pygame.draw.rect(self.background, self.colorVacio, posicion)  # rect vacio
        pygame.draw.rect(self.background, self.colorAgua, aux)
        if aux[3] <= 1:
            pygame.draw.rect(self.background, self.colorVacio, (posicion[0] + 30, posicion[1] + 120, 10,20))
        else:
            pygame.draw.rect(self.background, self.colorAgua, (posicion[0] + 30, posicion[1] + 120, 10,20))

        # Texto:
        string = 'H:{}'.format(round(altura, 3))
        pygame.draw.rect(self.textSurf, self.colorVacio,(posicion[0] + 80, posicion[1] + 20, 100,20))
        self.textSurf.blit(self.font2.render(string, True, (200, 0, 0)), (posicion[0] + 80, posicion[1] + 20))

    # Se muestra la rotación de la llave
    def rotate(self, centro, punto, theta):
        # tralación al origen
        x0 = punto[0] - centro[0]
        y0 = punto[1] - centro[1]
        #rotación
        xrot0 = x0*np.cos(np.deg2rad(theta)) - y0*np.sin(np.deg2rad(theta))
        yrot0 = y0*np.cos(np.deg2rad(theta)) + x0*np.sin(np.deg2rad(theta))
        #De vuelta
        return xrot0 + centro[0], yrot0 + centro[1]

    # Se actualiza con introducción del usuario
    def Automatico(self, pump1_act, pump2_act, switch1_act, switch2_act):
        if pump1_act != self.pump1_ant:
            pygame.draw.circle(self.background, self.colorPump, self.centroPump1, 20)  # se dibuja sobre
            Pump1p1 = self.rotate(self.centroPump1, self.Pump1p1, pump1_act* 90)
            Pump1p2 = self.rotate(self.centroPump1, self.Pump1p2, pump1_act* 90)
            pygame.draw.line(self.background, self.colorPipe, Pump1p1, Pump1p2, 4)
            string = '{}'.format(round(pump1_act, 3))
            pygame.draw.rect(self.textSurf, self.colorVacio,
                             (self.centroPump1[0] - 80, self.centroPump1[1], 60, 20))
            self.textSurf.blit(self.font2.render(string, True, (200, 0, 0)),
                               (self.centroPump1[0] - 80, self.centroPump1[1]))
            self.pump1_ant = pump1_act

        if pump2_act != self.pump2_ant:
            pygame.draw.circle(self.background, self.colorPump, self.centroPump2, 20)  # se dibuja sobre
            Pump2p1 = self.rotate(self.centroPump2, self.Pump2p1, pump2_act* 90)
            Pump2p2 = self.rotate(self.centroPump2, self.Pump2p2, pump2_act * 90)
            pygame.draw.line(self.background, self.colorPipe, Pump2p1, Pump2p2, 4)
            string = '{}'.format(round(pump2_act, 3))
            pygame.draw.rect(self.textSurf, self.colorVacio,
                             (self.centroPump2[0] + 30, self.centroPump2[1], 70, 20))
            self.textSurf.blit(self.font2.render(string, True, (200, 0, 0)),
                               (self.centroPump2[0] + 30, self.centroPump2[1]))
            self.pump2_ant = pump2_act

        if switch1_act != self.switch1_ant:
            string1 = 'up:{}'.format(round(1 - switch1_act, 3))
            string2 = 'down:{}'.format(round(switch1_act, 3))
            pygame.draw.rect(self.textSurf, self.colorVacio,
                             (self.centrollave1[0] - 100, self.centrollave1[1] - 20, 100, 80))
            self.textSurf.blit(self.font2.render(string1, True, (200, 0, 0)),
                               (self.centrollave1[0] - 100, self.centrollave1[1] - 20))
            self.textSurf.blit(self.font2.render(string2, True, (200, 0, 0)),
                               (self.centrollave1[0] - 100, self.centrollave1[1] + 20))

        if switch2_act != self.switch2_ant:
            string3 = 'up:{}'.format(round(1 - switch2_act, 3))
            string4 = 'down:{}'.format(round(switch2_act, 3))
            pygame.draw.rect(self.textSurf, self.colorVacio,
                             (self.centrollave2[0] + 30, self.centrollave2[1] - 20, 100, 80))
            self.textSurf.blit(self.font2.render(string3, True, (200, 0, 0)),
                               (self.centrollave2[0] + 30, self.centrollave2[1] - 20))
            self.textSurf.blit(self.font2.render(string4, True, (200, 0, 0)),
                               (self.centrollave2[0] + 30, self.centrollave2[1] + 20))


    def eventos(self, running, sensibilidad, pump1_act, pump2_act, switch1_act, switch2_act):
        # Diferenciales de cambio
        dpump1 = 0
        dpump2 = 0
        dswitch1 = 0
        dswitch2 = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

            # Control manual de las variables manipuladas
            if event.type == pygame.KEYDOWN:
                # Pumps
                if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    if event.key == pygame.K_UP:
                        dpump1 += sensibilidad

                    elif event.key == pygame.K_DOWN:
                        dpump1 -= sensibilidad

                    pump1_act += dpump1
                    if pump1_act >= 0 and pump1_act <= 1:
                        pygame.draw.circle(self.background, self.colorPump, self.centroPump1, 20)  # se dibuja sobre
                        self.Pump1p1 = self.rotate(self.centroPump1, self.Pump1p1, dpump1 * 90)
                        self.Pump1p2 = self.rotate(self.centroPump1, self.Pump1p2, dpump1 * 90)
                        pygame.draw.line(self.background, self.colorPipe, self.Pump1p1, self.Pump1p2, 4)
                        string = '{}'.format(round(pump1_act, 3))
                        pygame.draw.rect(self.textSurf, self.colorVacio,
                                         (self.centroPump1[0] - 80, self.centroPump1[1], 60, 20))
                        self.textSurf.blit(self.font2.render(string, True, (200, 0, 0)),
                                           (self.centroPump1[0] - 80, self.centroPump1[1]))
                    else:
                        pump1_act -= dpump1



                if event.key == pygame.K_RIGHT or event.key == pygame.K_LEFT:
                    if event.key == pygame.K_RIGHT:
                        dpump2 += sensibilidad

                    elif event.key == pygame.K_LEFT:
                        dpump2 -= sensibilidad

                    pump2_act += dpump2
                    if pump2_act >= 0 and pump2_act <= 1: # Restricciones
                        pygame.draw.circle(self.background, self.colorPump, self.centroPump2, 20)  # se dibuja sobre
                        self.Pump2p1 = self.rotate(self.centroPump2, self.Pump2p1, dpump2 * 90)
                        self.Pump2p2 = self.rotate(self.centroPump2, self.Pump2p2, dpump2 * 90)
                        pygame.draw.line(self.background, self.colorPipe, self.Pump2p1, self.Pump2p2, 4)
                        string = '{}'.format(round(pump2_act, 3))
                        pygame.draw.rect(self.textSurf, self.colorVacio,
                                         (self.centroPump2[0] + 30, self.centroPump2[1], 70, 20))
                        self.textSurf.blit(self.font2.render(string, True, (200, 0, 0)),
                                           (self.centroPump2[0] + 30, self.centroPump2[1]))
                    else:
                        pump2_act -= dpump2

                #Switches
                if event.key == pygame.K_q or event.key == pygame.K_a:
                    if event.key == pygame.K_a:
                        dswitch1 += sensibilidad
                    elif event.key == pygame.K_q:
                        dswitch1 -= sensibilidad

                    switch1_act += dswitch1
                    if switch1_act >= 0 and switch1_act <=1:
                        string1 = 'up:{}'.format(round(1 -switch1_act,3))
                        string2 = 'down:{}'.format(round(switch1_act,3))
                        pygame.draw.rect(self.textSurf, self.colorVacio,
                                         (self.centrollave1[0] - 100, self.centrollave1[1] - 20, 100, 80))
                        self.textSurf.blit(self.font2.render(string1, True, (200, 0, 0)),
                                           (self.centrollave1[0] - 100, self.centrollave1[1] - 20))
                        self.textSurf.blit(self.font2.render(string2, True, (200, 0, 0)),
                                           (self.centrollave1[0] - 100, self.centrollave1[1] + 20))
                    else:
                        switch1_act -= dswitch1


                if event.key == pygame.K_w or event.key == pygame.K_s:
                    if event.key == pygame.K_s:
                        dswitch2 += sensibilidad
                    elif event.key == pygame.K_w:
                        dswitch2 -= sensibilidad

                    switch2_act += dswitch2
                    if switch2_act >=0 and switch2_act <= 1:
                        string3 = 'up:{}'.format(round(1 -switch2_act, 3))
                        string4 = 'down:{}'.format(round(switch2_act, 3))
                        pygame.draw.rect(self.textSurf, self.colorVacio,
                                         (self.centrollave2[0] + 30, self.centrollave2[1] - 20, 100, 80))
                        self.textSurf.blit(self.font2.render(string3, True, (200, 0, 0)),
                                           (self.centrollave2[0] + 30, self.centrollave2[1] - 20))
                        self.textSurf.blit(self.font2.render(string4, True, (200, 0, 0)),
                                           (self.centrollave2[0] + 30, self.centrollave2[1] + 20))
                    else:
                        switch2_act -= dswitch2

        return running, {'valvula1': pump1_act, 'valvula2': pump2_act, 'razon1': switch1_act, 'razon2': switch2_act}


######################## Cliente opc ####################################

# Se declaran después cuando se haga el controlador
variables_manipuladas = {'Valvula1': 0, 'Valvula2':0 , 'Razon1':0, 'Razon2':0}

# Función que se suscribe
def funcion_handler(node, val):
    key = node.get_parent().get_display_name().Text
    variables_manipuladas[key] = val # Se cambia globalmente el valor de las variables manipuladas cada vez que estas cambian
    print('key: {} | val: {}'.format(key, val))


class SubHandler(object): # Clase debe estar en el script porque el thread que comienza debe mover variables globales
    def datachange_notification(self, node, val, data):
        thread_handler = threading.Thread(target=funcion_handler, args=(node, val))  # Se realiza la descarga por un thread
        thread_handler.start()

    def event_notification(self, event):
        #print("Python: New event", event)
        pass

cliente = Cliente("opc.tcp://localhost:4840/freeopcua/server/", suscribir_eventos=True, SubHandler=SubHandler)
cliente.conectar()
#cliente.subscribir_mv() # Se subscribe a las variables manipuladas

######################### Main loop #################################

# Setup
x0=[40, 40, 40, 40] #Condición inicial de los tanques
#x0=[33.915, 35.224, 4.485, 3.914] #Condición inicial de los tanques (eq para u_eq = (0.5,0.5)) y gamma = (0.7,0.6)
#x0=[28.029, 43.489, 10.091, 15.656] #Condic

#
# drh dfh dión inicial de los tanques (eq para u_eq = (0.5,0.5)) y gamma = (0.4,0.4)
Hmax = 50
voltmax = 10
fps = 20
sensibilidad = 0.01 # Cambio de las varibles manipuladas cada vez que se aprieta una tecla
clock = pygame.time.Clock() # Limita la cantidad de FPS
first_it = True

sistema = QuadrupleTank(x0=x0, Hmax=Hmax, voltmax=voltmax)
sistema.time_scaling = 1 # Para el tiempo
# interfaz = Interfaz_grafica(Hmax=Hmax)
# interfaz.paint()
running = True
manual = False # Control Manual o automático de las variables
t = 0
alturasMatrix = []
while running:
    # Actualización del sistema de forma manual
    if manual:
        running, u = interfaz.eventos(running, sensibilidad, sistema.volt[0], sistema.volt[1], sistema.gamma[0], sistema.gamma[1])
        sistema.volt[0] = u['valvula1']
        sistema.volt[1] = u['valvula2']
        sistema.gamma[0] = u['razon1']
        sistema.gamma[1] = u['razon2']

        # Envío de los valores por OPC cuando se está en forma manual
        # Obtención de los pumps
        cliente.valvulas['valvula1'].set_value(u['valvula1'])
        cliente.valvulas['valvula2'].set_value(u['valvula2'])

        # Obtención de los switches
        cliente.razones['razon1'].set_value(u['razon1'])
        cliente.razones['razon2'].set_value(u['razon2'])
    else:
        volt1 = cliente.valvulas['valvula1'].get_value()
        volt2 = cliente.valvulas['valvula2'].get_value()

        gamma1 = cliente.razones['razon1'].get_value()
        gamma2 = cliente.razones['razon2'].get_value()

        if volt1 > 1 or volt1 < -1 or volt2 > 1 or volt2 < -1 \
            or gamma1 > 1 or gamma1 < 0 or gamma2 > 1 or gamma2 < 0:
            raise ValueError('Valores fuera del rango específicado')

        # interfaz.Automatico(volt1, volt2, gamma1, gamma2)

        sistema.volt[0] = volt1
        sistema.volt[1] = volt2
        sistema.gamma[0] = gamma1
        sistema.gamma[1] = gamma2




    # interfaz.screen.blit(interfaz.background, (0, 0))
    # interfaz.screen.blit(interfaz.textSurf, (0,0))


    ####### Simulación del sistema ######
    if first_it:
        sistema.ti = time.time()
        first_it = False

    alturas = sistema.sim()

    ####### Updates interfaz #################

##    # Tanque 1
##    interfaz.Tank_update(altura=alturas[0], posicion=interfaz.posTank1)
##
##    # Tanque 2
##    interfaz.Tank_update(altura=alturas[1], posicion=interfaz.posTank2)
##
##    # Tanque 3
##    interfaz.Tank_update(altura=alturas[2], posicion=interfaz.posTank3)
##
##    # Tanque 4
##    interfaz.Tank_update(altura=alturas[3], posicion=interfaz.posTank4)


    ############ UPDATE CLIENTE OPC ##################################
    cliente.alturas['H1'].set_value(alturas[0])
    cliente.alturas['H2'].set_value(alturas[1])
    cliente.alturas['H3'].set_value(alturas[2])
    cliente.alturas['H4'].set_value(alturas[3])

    cliente.temperaturas['T1'].set_value(22 + random.randrange(-7,7,1))
    cliente.temperaturas['T2'].set_value(22 + random.randrange(-7,7,1))
    cliente.temperaturas['T3'].set_value(22 + random.randrange(-7,7,1))
    cliente.temperaturas['T4'].set_value(22 + random.randrange(-7,7,1))


    # pygame.display.flip()
    # clock.tick(fps)

# pygame.quit()

