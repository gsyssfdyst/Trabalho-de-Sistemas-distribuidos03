import socket
import threading
import time
import pickle
from utils import LamportClock, log_event

class Process:
    def __init__(self, process_id, port, peers, coordinator_port=None):
        self.process_id = process_id
        self.port = port
        self.peers = peers  # lista de portas dos peers
        self.coordinator_port = coordinator_port
        self.clock = LamportClock()
        self.state = {"counter": 0, "status": "ON"}
        self.running = True

        # Snapshot state
        self.snapshot_active = False
        self.local_snapshot = None
        self.channel_states = {}  # canal: lista de mensagens em trânsito
        self.marker_received = {}  # canal: bool
        self.snapshot_lock = threading.Lock()

        # Para coleta global
        self.snapshots_collected = {}
        self.is_coordinator = (self.coordinator_port == self.port)

    def start(self):
        threading.Thread(target=self._run_server, daemon=True).start()
        threading.Thread(target=self._generate_events, daemon=True).start()

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
                if msg_type == "MARKER":
                    self._handle_marker(msg)
                elif msg_type == "SNAPSHOT_RESULT":
                    self._handle_snapshot_result(msg)
                else:
                    self._handle_message(msg)
            except Exception as e:
                log_event(f"Process {self.process_id} connection error: {e}")

    def _handle_message(self, msg):
        sender_port = msg["from"]
        timestamp = msg["timestamp"]
        payload = msg["payload"]

        with self.snapshot_lock:
            if self.snapshot_active and not self.marker_received.get(sender_port, False):
                # Registrar mensagem em trânsito
                self.channel_states.setdefault(sender_port, []).append((payload, timestamp))

        self.clock.update(timestamp)
        self.clock.increment()
        log_event(f"Process {self.process_id} received message from {sender_port} with timestamp {timestamp}. Clock: {self.clock.time}")

    def _handle_marker(self, msg):
        sender_port = msg["from"]
        initiator = msg["initiator"]
        with self.snapshot_lock:
            if not self.snapshot_active:
                # Primeiro marcador recebido
                self.snapshot_active = True
                self.local_snapshot = {
                    "process_id": self.process_id,
                    "state": self.state.copy(),
                    "clock": self.clock.time
                }
                log_event(f"Process {self.process_id} recorded local snapshot: {self.local_snapshot}")
                # Inicializa canais
                for peer in self.peers:
                    if peer != sender_port:
                        self.marker_received[peer] = False
                        self.channel_states[peer] = []
                self.marker_received[sender_port] = True
                # Envia marcador para todos os peers
                for peer in self.peers:
                    self._send_marker(peer, initiator)
            else:
                self.marker_received[sender_port] = True

            # Parar de registrar mensagens do canal de quem enviou o marcador
            # (feito acima ao marcar marker_received)

            # Se recebeu marcador de todos os canais de entrada, snapshot local está completo
            if all(self.marker_received.get(peer, False) for peer in self.peers):
                log_event(f"Process {self.process_id} completed local snapshot.")
                self.snapshot_active = False
                # Envia resultado ao coordenador
                if self.coordinator_port:
                    self._send_snapshot_result(initiator)

    def _send_marker(self, peer_port, initiator):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                sock.connect(("localhost", peer_port))
                msg = {
                    "type": "MARKER",
                    "from": self.port,
                    "initiator": initiator
                }
                sock.sendall(pickle.dumps(msg))
            log_event(f"Process {self.process_id} sent MARKER to {peer_port}")
        except Exception as e:
            log_event(f"Process {self.process_id} failed to send MARKER to {peer_port}: {e}")

    def _send_snapshot_result(self, initiator):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                sock.connect(("localhost", initiator))
                msg = {
                    "type": "SNAPSHOT_RESULT",
                    "from": self.port,
                    "snapshot": {
                        "local_state": self.local_snapshot,
                        "channel_states": self.channel_states
                    }
                }
                sock.sendall(pickle.dumps(msg))
            log_event(f"Process {self.process_id} sent SNAPSHOT_RESULT to coordinator {initiator}")
        except Exception as e:
            log_event(f"Process {self.process_id} failed to send SNAPSHOT_RESULT: {e}")

    def _handle_snapshot_result(self, msg):
        # Só o coordenador recebe
        if not self.is_coordinator:
            return
        sender = msg["from"]
        self.snapshots_collected[sender] = msg["snapshot"]
        log_event(f"Coordinator received snapshot from {sender}")
        # Se recebeu de todos os peers, exibe o snapshot global
        if len(self.snapshots_collected) == len(self.peers):
            self.snapshots_collected[self.port] = {
                "local_state": self.local_snapshot,
                "channel_states": self.channel_states
            }
            log_event("=== GLOBAL SNAPSHOT RESULT ===")
            for proc, snap in self.snapshots_collected.items():
                log_event(f"Process {proc}: {snap['local_state']}")
                for ch, msgs in snap["channel_states"].items():
                    log_event(f"  Channel {ch} -> {proc}: {msgs}")
            log_event("=============================")

    def _generate_events(self):
        while self.running:
            time.sleep(2)
            self.clock.increment()
            self.state["counter"] += 1
            log_event(f"Process {self.process_id} generated internal event. Clock: {self.clock.time}")
            self._send_message()

    def _send_message(self):
        self.clock.increment()
        for peer_port in self.peers:
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

    def initiate_snapshot(self):
        with self.snapshot_lock:
            if self.snapshot_active:
                return
            self.snapshot_active = True
            self.local_snapshot = {
                "process_id": self.process_id,
                "state": self.state.copy(),
                "clock": self.clock.time
            }
            log_event(f"Process {self.process_id} initiated and recorded local snapshot: {self.local_snapshot}")
            # Inicializa canais
            for peer in self.peers:
                self.marker_received[peer] = False
                self.channel_states[peer] = []
            # Marca que já recebeu de si mesmo (não existe canal de si para si)
            # Envia marcador para todos os peers
            for peer in self.peers:
                self._send_marker(peer, self.port)
            # Se não tem peers, já finaliza
            if not self.peers:
                self.snapshot_active = False
