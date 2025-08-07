from process import Process
import time

def main():
    # Definindo as portas
    ports = [5001, 5002, 5003]
    coordinator_port = ports[0]

    process1 = Process(1, ports[0], [ports[1], ports[2]], coordinator_port=coordinator_port)
    process2 = Process(2, ports[1], [ports[0], ports[2]], coordinator_port=coordinator_port)
    process3 = Process(3, ports[2], [ports[0], ports[1]], coordinator_port=coordinator_port)

    process1.start()
    process2.start()
    process3.start()

    time.sleep(8)
    process1.initiate_snapshot()

    # Aguarda o snapshot global ser coletado
    time.sleep(10)
    process1.running = False
    process2.running = False
    process3.running = False
    time.sleep(1)

if __name__ == "__main__":
    main()
