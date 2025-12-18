#!/usr/bin/env python3
"""
operator_ui.py - PyQt5-based Operator UI for AGISWARM

This UI provides a graphical interface for operators to:
- Load and sign proposed state changes
- Send signed commit tokens via UDP to the aggregator
- View the current proposed state

Requirements:
- PyQt5 (install with: pip install -r requirements-operator-ui.txt)
- NaCl for Ed25519 signing
- CBOR for message encoding

Configuration:
- UDP Target: 127.0.0.1:6000 (aggregator)
- Operator Key: operator.sk (Ed25519 secret key, hex-encoded)
- Proposed State: proposed_state.json (JSON format)

Usage:
    python operator_ui.py
"""

import sys
import json
import socket
import os
from pathlib import Path

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QTextEdit, QLabel, QMessageBox, QFileDialog
    )
    from PyQt5.QtCore import Qt
except ImportError:
    print("Error: PyQt5 is not installed.")
    print("Install it with: pip install -r requirements-operator-ui.txt")
    sys.exit(1)

try:
    import nacl.signing
    import nacl.encoding
except ImportError:
    print("Error: PyNaCl is not installed.")
    print("Install it with: pip install pynacl")
    sys.exit(1)

try:
    import cbor2
except ImportError:
    print("Error: cbor2 is not installed.")
    print("Install it with: pip install cbor2")
    sys.exit(1)


# Default paths and configuration
DEFAULT_OPERATOR_KEY_PATH = "operator.sk"
DEFAULT_PROPOSED_STATE_PATH = "proposed_state.json"
UDP_TARGET_HOST = "127.0.0.1"
UDP_TARGET_PORT = 6000


class OperatorUI(QMainWindow):
    """Main Operator UI window."""

    def __init__(self):
        super().__init__()
        self.operator_key_path = DEFAULT_OPERATOR_KEY_PATH
        self.proposed_state_path = DEFAULT_PROPOSED_STATE_PATH
        self.signing_key = None
        self.proposed_state = None
        self.init_ui()
        self.load_operator_key()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("AGISWARM Operator UI")
        self.setGeometry(100, 100, 800, 600)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Title
        title_label = QLabel("AGISWARM Operator Control Panel")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Status area
        self.status_label = QLabel("Status: Initializing...")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        main_layout.addWidget(self.status_label)

        # Proposed state display
        state_label = QLabel("Proposed State:")
        main_layout.addWidget(state_label)
        
        self.state_text = QTextEdit()
        self.state_text.setReadOnly(True)
        self.state_text.setStyleSheet("font-family: monospace;")
        main_layout.addWidget(self.state_text)

        # Button layout
        button_layout = QHBoxLayout()
        
        self.load_key_btn = QPushButton("Load Operator Key")
        self.load_key_btn.clicked.connect(self.load_operator_key_dialog)
        button_layout.addWidget(self.load_key_btn)
        
        self.load_state_btn = QPushButton("Load Proposed State")
        self.load_state_btn.clicked.connect(self.load_proposed_state)
        button_layout.addWidget(self.load_state_btn)
        
        self.sign_send_btn = QPushButton("Sign & Send Commit")
        self.sign_send_btn.clicked.connect(self.sign_and_send)
        self.sign_send_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        button_layout.addWidget(self.sign_send_btn)
        
        main_layout.addLayout(button_layout)

        # Log area
        log_label = QLabel("Activity Log:")
        main_layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        main_layout.addWidget(self.log_text)

    def log(self, message):
        """Add a message to the activity log."""
        self.log_text.append(message)

    def load_operator_key_dialog(self):
        """Open a file dialog to select operator key."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Operator Key File",
            "",
            "Key Files (*.sk);;All Files (*)"
        )
        if file_path:
            self.operator_key_path = file_path
            self.load_operator_key()

    def load_operator_key(self):
        """Load the operator's Ed25519 signing key."""
        try:
            key_path = Path(self.operator_key_path)
            if not key_path.exists():
                self.status_label.setText(f"Status: Operator key not found at {self.operator_key_path}")
                self.status_label.setStyleSheet("padding: 5px; background-color: #ffcccc;")
                self.log(f"Warning: Operator key not found at {self.operator_key_path}")
                self.log("Please generate a key using: python operator/keygen.py")
                return

            with open(key_path, "r") as f:
                sk_hex = f.read().strip()
            
            self.signing_key = nacl.signing.SigningKey(sk_hex, encoder=nacl.encoding.HexEncoder)
            self.status_label.setText(f"Status: Operator key loaded from {self.operator_key_path}")
            self.status_label.setStyleSheet("padding: 5px; background-color: #ccffcc;")
            self.log(f"✓ Operator key loaded successfully from {self.operator_key_path}")
            
        except Exception as e:
            error_msg = f"Failed to load operator key: {str(e)}"
            self.status_label.setText(f"Status: Error loading key")
            self.status_label.setStyleSheet("padding: 5px; background-color: #ffcccc;")
            self.log(f"✗ {error_msg}")
            QMessageBox.critical(
                self,
                "Key Loading Error",
                f"{error_msg}\n\nPlease ensure:\n"
                f"1. The file exists at {self.operator_key_path}\n"
                f"2. The file contains a valid hex-encoded Ed25519 secret key\n"
                f"3. Generate a key with: python operator/keygen.py"
            )

    def load_proposed_state(self):
        """Load the proposed state from JSON file."""
        try:
            state_path = Path(self.proposed_state_path)
            if not state_path.exists():
                raise FileNotFoundError(f"Proposed state file not found at {self.proposed_state_path}")
            
            with open(state_path, "r") as f:
                self.proposed_state = json.load(f)
            
            # Display the state
            formatted_state = json.dumps(self.proposed_state, indent=2)
            self.state_text.setPlainText(formatted_state)
            
            self.log(f"✓ Proposed state loaded from {self.proposed_state_path}")
            
            if self.signing_key:
                self.status_label.setText("Status: Ready to sign and send")
                self.status_label.setStyleSheet("padding: 5px; background-color: #ccffcc;")
            
        except FileNotFoundError as e:
            error_msg = str(e)
            self.log(f"✗ {error_msg}")
            QMessageBox.critical(
                self,
                "File Not Found",
                f"{error_msg}\n\nPlease ensure the proposed state file exists."
            )
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON format in {self.proposed_state_path}: {str(e)}"
            self.log(f"✗ {error_msg}")
            QMessageBox.critical(
                self,
                "JSON Parse Error",
                f"{error_msg}\n\nPlease ensure the file contains valid JSON."
            )
        except Exception as e:
            error_msg = f"Failed to load proposed state: {str(e)}"
            self.log(f"✗ {error_msg}")
            QMessageBox.critical(
                self,
                "Loading Error",
                error_msg
            )

    def sign_and_send(self):
        """Sign the proposed state and send it via UDP."""
        # Validate prerequisites
        if not self.signing_key:
            QMessageBox.warning(
                self,
                "Missing Key",
                "Operator key not loaded. Please load a valid operator.sk file."
            )
            return
        
        if not self.proposed_state:
            QMessageBox.warning(
                self,
                "Missing State",
                "Proposed state not loaded. Please load a proposed_state.json file."
            )
            return
        
        try:
            # Serialize the state
            state_bytes = json.dumps(self.proposed_state).encode("utf-8")
            
            # Sign the state
            signed_message = self.signing_key.sign(state_bytes)
            signature = signed_message.signature
            
            # Create CBOR message
            commit_token = {
                "type": "commit_token",
                "state": self.proposed_state,
                "signature": signature,
                "verify_key": bytes(self.signing_key.verify_key)
            }
            
            cbor_message = cbor2.dumps(commit_token)
            
            # Send via UDP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(cbor_message, (UDP_TARGET_HOST, UDP_TARGET_PORT))
            sock.close()
            
            self.log(f"✓ Commit token signed and sent to {UDP_TARGET_HOST}:{UDP_TARGET_PORT}")
            QMessageBox.information(
                self,
                "Success",
                f"Commit token successfully signed and sent to aggregator at {UDP_TARGET_HOST}:{UDP_TARGET_PORT}"
            )
            
        except Exception as e:
            error_msg = f"Failed to sign and send: {str(e)}"
            self.log(f"✗ {error_msg}")
            QMessageBox.critical(
                self,
                "Transmission Error",
                f"{error_msg}\n\nPlease ensure:\n"
                f"1. The aggregator is running\n"
                f"2. UDP port {UDP_TARGET_PORT} is accessible\n"
                f"3. Network connectivity is available"
            )


def main():
    """Main entry point for the Operator UI."""
    app = QApplication(sys.argv)
    window = OperatorUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
