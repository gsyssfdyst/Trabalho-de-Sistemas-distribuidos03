import socket
import threading
import time
import pickle
from utils import LamportClock, log_event

class Process:
    def __init__(self, process_id, port, peers):
        self.process_id = process_id
        self.port = port
        self.peers = peers  # lista de portas dos peers
        self.clock = LamportClock()
        self.state = {"counter": 0, "status": "ON"}
        self.running = True

        # Eleição
        self.coordinator_id = max([self.process_id] + [peer[0] for peer in self.peers])
        self.election_lock = threading.Lock()
        self.election_in_progress = False

    def start(self):
        threading.Thread(target=self._run_server, daemon=True).start()
        threading.Thread(target=self._generate_events, daemon=True).start()
        threading.Thread(target=self._detect_coordinator_failure, daemon=True).start()

    def _run_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("localhost", self.port))
            server.listen()
            while self.running:
                try:
                    conn, addr = server.accept()
                    threading.Thread(target=self._handle_connection, args=(conn,), daemon=True).start()
                except Exception as e:
                    log_event(f"Process {self.process_id} server error: {e}")

    def _handle_connection(self, conn):
        with conn:
            try:
                data = conn.recv(4096)
                if not data:
                    return
                msg = pickle.loads(data)
                msg_type = msg.get("type")
                if msg_type == "ELECTION":
                    self._handle_election_message(msg)
                elif msg_type == "COORDINATOR":
                    self._handle_coordinator_message(msg)
                elif msg_type == "ELECTION_OK":
                    self._handle_election_ok(msg)
                elif msg_type == "RING_ELECTION":
                    self._handle_ring_election(msg)
                elif msg_type == "RING_COORDINATOR":
                    self._handle_ring_coordinator(msg)
                else:
                    self._handle_message(msg)
            except Exception as e:
                log_event(f"Process {self.process_id} connection error: {e}")

    def _handle_message(self, msg):
        sender_port = msg["from"]
        timestamp = msg.get("timestamp", 0)
        payload = msg.get("payload", "")

        self.clock.update(timestamp)
        self.clock.increment()
        log_event(f"Process {self.process_id} received message from {sender_port} with timestamp {timestamp}. Clock: {self.clock.time}")

    # --- Bully Election Methods ---

    def _detect_coordinator_failure(self):
        while self.running:
            time.sleep(5)
            if self.process_id == self.coordinator_id:
                continue  # sou o coordenador
            try:
                coord_port = self._get_port_by_id(self.coordinator_id)
                if coord_port is None:
                    continue
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(2)
                    sock.connect(("localhost", coord_port))
                    msg = {
                        "type": "APP",
                        "from": self.port,
                        "timestamp": self.clock.time,
                        "payload": "ping"
                    }
                    sock.sendall(pickle.dumps(msg))
            except Exception:
                log_event(f"Processo {self.process_id} detectou a falha do coordenador {self.coordinator_id}.")
                self._run_bully_election()

    def _run_bully_election(self):
        with self.election_lock:
            if self.election_in_progress:
                return
            self.election_in_progress = True
        higher = [peer for peer in self.peers if peer[0] > self.process_id]
        if not higher:
            # Eu sou o maior, me torno coordenador
            self.coordinator_id = self.process_id
            self._announce_coordinator()
            log_event(f"Processo {self.process_id} foi eleito o novo coordenador.")
            self.election_in_progress = False
            return
        received_ok = threading.Event()
        # Envia mensagem de eleição para todos com ID maior
        for peer_id, peer_port in higher:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(2)
                    sock.connect(("localhost", peer_port))
                    msg = {
                        "type": "ELECTION",
                        "from_id": self.process_id,
                        "from_port": self.port
                    }
                    sock.sendall(pickle.dumps(msg))
                log_event(f"Processo {self.process_id} enviou mensagem de eleição para o processo {peer_id}.")
            except Exception:
                continue
        # Aguarda resposta OK
        def wait_ok():
            try:
                received_ok.wait(timeout=3)
            except Exception:
                pass
        t = threading.Thread(target=wait_ok)
        t.start()
        t.join()
        if not received_ok.is_set():
            # Ninguém respondeu, sou coordenador
            self.coordinator_id = self.process_id
            self._announce_coordinator()
            log_event(f"Processo {self.process_id} foi eleito o novo coordenador.")
        self.election_in_progress = False

    def _handle_election_message(self, msg):
        from_id = msg["from_id"]
        from_port = msg["from_port"]
        # Responde OK se meu ID é maior
        if self.process_id > from_id:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(2)
                    sock.connect(("localhost", from_port))
                    msg_ok = {
                        "type": "ELECTION_OK",
                        "from_id": self.process_id
                    }
                    sock.sendall(pickle.dumps(msg_ok))
                log_event(f"Processo {self.process_id} respondeu ELECTION_OK para {from_id}.")
            except Exception:
                pass
            # Inicia eleição se ainda não estiver em progresso
            self._run_bully_election()

    def _handle_election_ok(self, msg):
        # Recebeu OK, não se torna coordenador
        with self.election_lock:
            self.election_in_progress = False

    def _announce_coordinator(self):
        for peer_id, peer_port in self.peers:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(2)
                    sock.connect(("localhost", peer_port))
                    msg = {
                        "type": "COORDINATOR",
                        "from_id": self.process_id
                    }
                    sock.sendall(pickle.dumps(msg))
            except Exception:
                pass

    def _handle_coordinator_message(self, msg):
        new_coord = msg["from_id"]
        self.coordinator_id = new_coord
        log_event(f"Processo {self.process_id} reconhece {new_coord} como novo coordenador.")
        with self.election_lock:
            self.election_in_progress = False

    def _get_port_by_id(self, proc_id):
        if proc_id == self.process_id:
            return self.port
        for pid, pport in self.peers:
            if pid == proc_id:
                return pport
        return None

    # --- Ring Election Methods ---

    def _run_ring_election(self):
        with self.election_lock:
            if self.election_in_progress:
                return
            self.election_in_progress = True
        # Inicia token de eleição com seu próprio ID
        token = [self.process_id]
        next_id, next_port = self._get_next_ring_peer()
        if next_port is None:
            self.election_in_progress = False
            return
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                sock.connect(("localhost", next_port))
                msg = {
                    "type": "RING_ELECTION",
                    "token": token
                }
                sock.sendall(pickle.dumps(msg))
            log_event(f"Processo {self.process_id} iniciou eleição anel e enviou token para {next_id}.")
        except Exception:
            pass

    def _handle_ring_election(self, msg):
        token = msg["token"]
        if self.process_id not in token:
            token.append(self.process_id)
        next_id, next_port = self._get_next_ring_peer()
        if next_port is None:
            return
        if token[0] == self.process_id and len(token) > 1:
            # Token retornou ao iniciador, escolhe maior ID
            new_coord = max(token)
            self.coordinator_id = new_coord
            self._announce_ring_coordinator(new_coord)
            log_event(f"Processo {self.process_id} foi eleito o novo coordenador (anel).")
            with self.election_lock:
                self.election_in_progress = False
        else:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(2)
                    sock.connect(("localhost", next_port))
                    msg = {
                        "type": "RING_ELECTION",
                        "token": token
                    }
                    sock.sendall(pickle.dumps(msg))
                log_event(f"Processo {self.process_id} passou token de eleição anel para {next_id}.")
            except Exception:
                pass

    def _announce_ring_coordinator(self, coord_id):
        # Envia mensagem de coordenador pelo anel
        next_id, next_port = self._get_next_ring_peer()
        if next_port is None:
            return
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                sock.connect(("localhost", next_port))
                msg = {
                    "type": "RING_COORDINATOR",
                    "coordinator_id": coord_id,
                    "initiator": self.process_id
                }
                sock.sendall(pickle.dumps(msg))
        except Exception:
            pass

    def _handle_ring_coordinator(self, msg):
        coord_id = msg["coordinator_id"]
        initiator = msg["initiator"]
        self.coordinator_id = coord_id
        log_event(f"Processo {self.process_id} reconhece {coord_id} como novo coordenador (anel).")
        if initiator != self.process_id:
            next_id, next_port = self._get_next_ring_peer()
            if next_port is not None:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(2)
                        sock.connect(("localhost", next_port))
                        sock.sendall(pickle.dumps(msg))
                except Exception:
                    pass
        with self.election_lock:
            self.election_in_progress = False

    def _get_next_ring_peer(self):
        # Retorna (id, port) do próximo processo no anel
        all_ids = [self.process_id] + [peer[0] for peer in self.peers]
        all_ports = [self.port] + [peer[1] for peer in self.peers]
        sorted_ids_ports = sorted(zip(all_ids, all_ports))
        idx = [i for i, (pid, _) in enumerate(sorted_ids_ports) if pid == self.process_id][0]
        next_idx = (idx + 1) % len(sorted_ids_ports)
        return sorted_ids_ports[next_idx]

    # --- Eventos e Mensagens normais ---

    def _generate_events(self):
        while self.running:
            time.sleep(2)
            self.clock.increment()
            self.state["counter"] += 1
            log_event(f"Process {self.process_id} generated internal event. Clock: {self.clock.time}")
            self._send_message()

    def _send_message(self):
        self.clock.increment()
        for peer_id, peer_port in self.peers:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(2)
                    sock.connect(("localhost", peer_port))
                    msg = {
                        "type": "APP",
                        "from": self.port,
                        "timestamp": self.clock.time,
                        "payload": f"msg from {self.process_id}"
                    }
                    sock.sendall(pickle.dumps(msg))
                log_event(f"Process {self.process_id} sent message to {peer_port}. Clock: {self.clock.time}")
            except Exception as e:
                log_event(f"Process {self.process_id} failed to send message to {peer_port}: {e}")
