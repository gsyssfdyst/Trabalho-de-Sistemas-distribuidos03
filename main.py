from process import Process
import time
import threading

def scenario_bully(processes):
    # Cenário A: Coordenador falha e retorna
    time.sleep(6)
    # Falha do coordenador (maior ID)
    coord_proc = max(processes, key=lambda p: p.process_id)
    coord_proc.running = False
    print(f"\n--- Coordenador {coord_proc.process_id} falhou! ---\n")
    time.sleep(8)
    # Coordenador retorna
    coord_proc.running = True
    coord_proc.start()
    print(f"\n--- Coordenador {coord_proc.process_id} retornou! ---\n")
    # Aguarda eleição e eventos
    time.sleep(10)
    # Finaliza todos
    for p in processes:
        p.running = False
    time.sleep(1)

def scenario_ring(processes):
    # Cenário B: Vários processos falham simultaneamente
    time.sleep(6)
    # Falham 2 processos de maior ID
    sorted_procs = sorted(processes, key=lambda p: p.process_id, reverse=True)
    for p in sorted_procs[:2]:
        p.running = False
        print(f"\n--- Processo {p.process_id} falhou! ---\n")
    time.sleep(4)
    # Inicia eleição anel a partir do menor ID vivo
    alive = [p for p in processes if p.running]
    if alive:
        alive[0]._run_ring_election()
    time.sleep(10)
    # Finaliza todos
    for p in processes:
        p.running = False
    time.sleep(1)

def main():
    # Definindo IDs e portas
    n = 5
    base_port = 5001
    ids_ports = [(i+1, base_port+i) for i in range(n)]
    processes = []
    for i, (proc_id, port) in enumerate(ids_ports):
        peers = [(pid, pport) for (pid, pport) in ids_ports if pid != proc_id]
        p = Process(proc_id, port, peers)
        processes.append(p)
    for p in processes:
        p.start()

    # Escolha de cenário
    print("Escolha o cenário de eleição:")
    print("1 - Bully (coordenador falha e retorna)")
    print("2 - Anel (vários processos falham)")
    choice = input("Digite 1 ou 2: ").strip()
    if choice == "1":
        scenario_bully(processes)
    else:
        scenario_ring(processes)

if __name__ == "__main__":
    main()
