# Cliente OPC e Interfaz de Usuario

En este directorio se encuentran los módulos detallados en el informe. 

[controller.py] se encarga de las comunicaciones OPC desde y hacia la planta, y provee además una interfaz hacia el PID implementado en [pid.py].

Por otro lado, [dashboard.py] corre un servidor de Flask que presenta una interfaz definida en [static/html/index.html] y en [static/js/dashboard.js].

Por el instante, el controlador se ejecuta solo cuando el backend se ejecuta, pero desacoplarlos es una tarea trivial.