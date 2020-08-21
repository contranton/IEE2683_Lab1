
# Laboratorio 1 IEE2683 - Agosto 2020
## Integrantes 
- Pedro Ariztia
- Javier Contreras
- Camila Turrieta

## Instrucciones

Antes que todo instalar los requisitos:
`pip install -r requirements`

Luego correr en primer lugar `run_server.bat` para inicializar la planta y el servidor OPC, y finalmente `run_client.bat` para lanzar el controlador desarrollado. Tras lanzar este último, el _dashboard_ se accede por medio de un navegador web en la dirección [http://localhost:5000/](http://localhost:5000/).

## Instrucciones de Siding:
>El servidor deben levantarlo en algún computador dentro de su red de área local mediante los archivos que se >encuentran a continuación. Noten que esta versión no tiene interfaz gráfica.
>Para levantar el servidor, deben ejecutar el script ServidorOPC.py y luego, en paralelo el script QuadrupleTank.py. >Naturalmente, el primer script se encarga se gestionar las comunicaciones, mientras que el segundo emula el proceso >industrial a controlar.


## Referencias para OPC UA:
- OPC para Python: https://python-opcua.readthedocs.io/en/latest/
- OPC UA detallado: https://documentation.unified-automation.com/uasdkhp/1.0.0/html/_l1_opc_ua_fundamentals.html
