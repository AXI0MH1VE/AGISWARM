import sys
import time
import threading
import json
import nacl.signing
import nacl.encoding
import socket
import cbor2
import os
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QMessageBox, QTextEdit
from PyQt5.QtCore import QTimer

class OperatorUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Edge-Lattice Operator (PoA Gate)')
        self.resize(600, 300)
        self.key, self.vkey = self.load_key()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.last_seq = -1
        self.proposed_state = None
        self.deadman_timer = QTimer(self)
        self.deadman_timer.timeout.connect(self.deadman_expiry)
        self.cycles_left = 0
        self.init_ui()
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.check_state)
        self.poll_timer.start(300)
        self.safety_anomaly = False

    def load_key(self):
        with open("operator.sk", "r") as f:
            sk_hex = f.read().strip()
        signing_key = nacl.signing.SigningKey(sk_hex, encoder=nacl.encoding.HexEncoder)
        return signing_key, signing_key.verify_key

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.state_label = QLabel("Waiting for proposed state...")
        self.state_text = QTextEdit("")
        self.state_text.setReadOnly(True)
        self.sign_btn = QPushButton("Sign & Commit")
        self.sign_btn.clicked.connect(self.do_sign)
        self.sign_btn.setEnabled(False)
        self.deadman_label = QLabel("")
        self.anomaly_label = QLabel("")
        self.layout.addWidget(self.state_label)
        self.layout.addWidget(self.state_text)
        self.layout.addWidget(self.sign_btn)
        self.layout.addWidget(self.deadman_label)
        self.layout.addWidget(self.anomaly_label)
        self.setLayout(self.layout)

    def show_anomaly(self, msg):
        self.safety_anomaly = True
        self.anomaly_label.setText(f'<span style="color:red;">SAFETY ALERT: {msg}</span>')
        QMessageBox.critical(self, "Safety Alert", msg)
        self.sign_btn.setEnabled(False)
        self.deadman_timer.stop()

    def check_state(self):
        if not os.path.exists("proposed_state.json"): return
        with open("proposed_state.json", "r") as f:
            state = json.load(f)
        if state['seq'] == self.last_seq:
            return
        self.last_seq = state['seq']
        self.proposed_state = state
        self.state_label.setText(f"Cycle {state['seq']} Proposed State:")
        self.state_text.setText(json.dumps(state['x'], indent=2))
        self.sign_btn.setEnabled(True)
        self.anomaly_label.setText("")
        # Start/reset deadman timer (simulate deadline)
        self.cycles_left = 12
        self.deadman_label.setText(f"Commit window: {self.cycles_left*0.1:.1f}s left")
        self.deadman_timer.start(100)

    def deadman_expiry(self):
        self.cycles_left -= 1
        self.deadman_label.setText(f"Commit window: {self.cycles_left*0.1:.1f}s left")
        if self.cycles_left <= 0:
            self.deadman_timer.stop()
            self.sign_btn.setEnabled(False)
            self.show_anomaly("Operator did not sign in time! State rejected / Control paused.")

    def do_sign(self):
        if not self.proposed_state: return
        msg = str(self.proposed_state['seq']).encode()
        sig = self.key.sign(msg).signature
        payload = {
            "t": "COMMIT",
            "seq": self.proposed_state['seq'],
            "sig": sig,
            "pk": self.vkey.encode(encoder=nacl.encoding.HexEncoder).decode()
        }
        self.sock.sendto(cbor2.dumps(payload), ("127.0.0.1", 6000))
        self.sign_btn.setEnabled(False)
        self.deadman_timer.stop()
        self.state_label.setText(f"Cycle {self.proposed_state['seq']} COMMITTED!")
        self.deadman_label.setText("")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OperatorUI()
    window.show()
    sys.exit(app.exec_())

