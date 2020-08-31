# Cliente OPC e Interfaz de Usuario

En este directorio se encuentran los módulos detallados en el informe.

[controller.py](controller.py) se encarga de las comunicaciones OPC desde y hacia la planta, y provee además una interfaz hacia el PID implementado en [pid.py](pid.py).

Por otro lado, [dashboard.py](dashboard.py) corre un servidor de Flask que presenta una interfaz definida en [index.html](static/html/index.html) y en [dashboard.js](static/js/dashboard.js).

Por el instante, el controlador se ejecuta solo cuando el backend se ejecuta, pero desacoplarlos es una tarea trivial.

## Como correr el sistema e interfaz

1. En el directorio superior:
   1. Correr `pip install -r requirements.txt`
   2. Correr `run_server.bat`
   3. Correr `run_client.bat`
2. Acceder a `localhost:5000` en un navegador web