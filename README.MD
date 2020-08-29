
# Laboratorio 1 IEE2683 - Agosto 2020

## Integrantes 

- Pedro Ariztia
- Javier Contreras
- Camila Turrieta

## Instrucciones

- Instalar los requisitos: `pip install -r requirements`

- Correr `run_server.bat` para inicializar la planta y el servidor OPC
  
- Correr `run_client.bat` (en una nueva terminal) para lanzar el controlador
  
- El _dashboard_ se encuentra en la dirección [http://localhost:5000/](http://localhost:5000/).

## Instrucciones de Siding

> El servidor deben levantarlo en algún computador dentro de su red de área local mediante los archivos que se encuentran a continuación. Noten que esta versión no tiene interfaz gráfica. Para levantar el servidor, deben ejecutar el script ServidorOPC.py y luego, en paralelo el script QuadrupleTank.py. Naturalmente, el primer script se encarga se gestionar las comunicaciones, mientras que el segundo emula el proceso industrial a controlar.

## Referencias para OPC UA

- OPC para Python: <https://python-opcua.readthedocs.io/en/latest/>
- OPC UA detallado: <https://documentation.unified-automation.com/uasdkhp/1.0.0/html/_l1_opc_ua_fundamentals.html>

# TODO:

- (DONE) Dashboard.py debe tener **una sola** función que broadcastee el estado del controlador
  - manual-ctrl-available: {true} o {false, "editor": NombreEditando}
  - Ganancias del PID
  - Quienes estan conectados

- Refresh-rate visual debe basarse en segundos transcurridos y no el número de datos recibidos
  - El segundo varía muchísimo dependiendo del rendimiento del servidor


- Entrada manual sinusoidal
- Alarmas
- Datos
- Filtro para componente derivada del PID
