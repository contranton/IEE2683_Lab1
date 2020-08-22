# References:
# https://medium.com/@data.corgi9/real-time-graph-using-flask-75f6696deb55
# https://flask-socketio.readthedocs.io/en/latest/
# https://github.com/maxcountryman/flask-login

from gevent import monkey
monkey.patch_all()

DATA_INTERVAL = 1       # In ms.

import json, time, random

from flask import Flask, Response, render_template, url_for, request, redirect, make_response, session
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, login_required, UserMixin, login_user, logout_user, current_user

from threading import Thread, Lock

from controller import Controller
global control

#####################################
# Data source
global x_
x_ = 0
def get_message():
    global x_
    #time.sleep(DATA_INTERVAL/1000)
    x_ += random.random()*2 - 1
    return x_

def event_stream(lock, do_stop):
    while True:
        if do_stop(): break
        time.sleep(DATA_INTERVAL/1000)
        try:
            h = control.heights_vals
            v = control.voltages_vals
            t = control.timestamp
        except:
            print(" * [DBG] Shutting down data collection worker\n\n")
            return

        d = dict(t=t,
                 data=dict(h1=h[1], h2=h[2], h3=h[3], h4=h[4],
                           v1=v[1], v2=v[2]))
        with lock:
            socketio.emit('server_push', {'data': d}, broadcast=True, namespace='/dashboard')

########################################
# User class (very basic, only for names and some basic state)

class User(UserMixin):

    users = {}
    usernames_for_logout = set()
    editor = ""

    def __init__(self, username):
        self.username = username
        self.has_control = False

    @property
    def id(self):
        return self.username

    @classmethod
    def get_user_list(cls): return [usr for usr in cls.usernames_for_logout]


######################################
# Flask server setup
app = Flask(__name__)
app.secret_key = 'omg nadie va a saber que esta es mi 11ave secreta por favor no me 1a roben pls :3'

# WebSocket for low-latency broadcasting
socketio = SocketIO(app)

# Login manager for authentification
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    if id in User.users.keys():
        User.usernames_for_logout.add(id)
    return User.users.get(id)

# @login_manager.request_loader
# def request_loader(request):
#     username = request.form.get("username")
#     return User(username)

@app.before_first_request
def clear_trash():
    print("Server restart")
    User.users.clear()
    User.usernames_for_logout = set()

# Main routing
@app.route('/')
def landing():
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    #print(current_user.username + " logged in")
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        redirect(url_for('dashboard'))

    if request.method == 'GET':
        return '''
               <div style="display: flex;flex-flow: column;align-items: center;">
                <h1 style="font-family:sans-serif">Ingrese su nombre:</h1>
                <form action='login' method='POST'>
                    <input type='text' name='username' id='user' placeholder='Usuario'></input>
                    <input type='submit' name='submit'></input>
                </form>
               </div>
               '''
    # Get username
    username = request.form['username']

    # Create user
    u = User(username)

    # Store in database
    User.users[u.get_id()] = u
    User.usernames_for_logout.add(u.get_id())

    # Register with flask-login
    login_user(u, remember=True)

    return redirect(url_for('dashboard'))

# Client responses

@socketio.on('client_connect', namespace='/dashboard')
def update_users_on_connect():
    print((current_user.get_id() or "") + " logged in")
    emit('server_userlist', {'data': json.dumps(User.get_user_list())},broadcast=True)
    try:
        emit('server_user-login', {'data': dict(can_control=(User.editor==""), editor=User.editor)})
    except AttributeError:
        print("Error sending stuff")
        return

@socketio.on('client_disconnect', namespace='/dashboard')
@login_required
def update_users_on_disconnect():
    Thread(target=attempt_remove_user, args=(current_user.get_id(),)).start()
    User.usernames_for_logout.remove(current_user.get_id())

    if current_user.has_control:
        User.editor = ""
        emit("server_enable-ctrl", broadcast=True)
    logout_user()
    emit('server_userlist', {'data': json.dumps(User.get_user_list())}, broadcast=True)
    redirect(url_for('login'))

@socketio.on('disconnect', namespace="/dashboard")
def kick_users_on_disconnect():
    logout_user()
    redirect(url_for('login'))

def attempt_remove_user(id):
    print("Gonna kill " + str(id))
    time.sleep(3)
    if id in User.usernames_for_logout:
        print("Cancelled logging out " + id)
        return
    else:
        User.users.pop(id)
        print(id + " logged out")
        socketio.emit('server_userlist', {'data': json.dumps(User.get_user_list())}, broadcast=True)
        User.editor=""
        socketio.emit('server_enable-ctrl', broadcast=True)
        return

@socketio.on('ctrl-mode', namespace='/dashboard')
def change_control():
    if(current_user.has_control):
        current_user.has_control = False
        User.editor = ""
        emit('server_user-end-ctrl')
        emit('server_enable-ctrl', broadcast=True, include_self=False)
    else:
        current_user.has_control = True
        User.editor = current_user.get_id()
        emit('server_user-begin-ctrl')
        emit('server_disable-ctrl', data=User.editor, broadcast=True, include_self=False)

@socketio.on('client_set-voltage1', namespace='/dashboard')
def set_voltage1(value):
    if (type(value) is not float) and (type(value) is not int):
        return
    control.set_voltages(v1=value)

@socketio.on('client_set-voltage2', namespace='/dashboard')
def set_voltage2(value):
    if type(value) is not float:
        return
    control.set_voltages(v2=value)

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for("login"))

if __name__ == '__main__':
    global control
    control = Controller("opc.tcp://localhost:4840/freeopcua/server/")

    lock = Lock()
    stop_thread = False
    p = Thread(target=event_stream, args=(lock, lambda: stop_thread))
    try:
        p.start()
        socketio.run(app, debug=True, host='0.0.0.0')
    finally:
        stop_thread = True
        socketio.emit("server_force-disconnect", broadcast=True, namespace="/dashboard")
        print(" * [DBG] Stopping")
        control.close()