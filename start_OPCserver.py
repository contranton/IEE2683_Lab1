import subprocess, os

os.chdir("./OPC_Server/")

if __name__ == "__main__":
    log1 = open("log_servidoropc.txt", 'w')
    subprocess.call(["python", "ServidorOPC.py"], stdout=log1)

    log2 = open("log_tanques.txt", 'w')
    subprocess.call(["python", "QuadrupleTanks.py"], stdout=log2)