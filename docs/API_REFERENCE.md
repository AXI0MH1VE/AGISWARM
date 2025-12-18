# AGISWARM API Reference

## Operator UI API

### Overview

The Operator UI (`operator/operator_ui.py`) provides a PyQt5-based graphical interface for managing operator commitments in the AGISWARM system.

### Configuration

#### Network Configuration
- **UDP Target Host**: `127.0.0.1`
- **UDP Target Port**: `6000`
- **Protocol**: UDP/CBOR

The Operator UI sends signed commit tokens to the aggregator's control endpoint at `127.0.0.1:6000`.

#### File Paths

##### Operator Key (`operator.sk`)
- **Default Path**: `operator.sk` (current working directory)
- **Format**: Raw binary, 32 bytes
- **Type**: Ed25519 secret key (NaCl/libsodium format)
- **Generation**: Use `python operator/keygen.py`

**Security Note**: The operator key file is sensitive. Never commit it to version control. It is automatically excluded via `.gitignore`.

##### Proposed State (`proposed_state.json`)
- **Default Path**: `proposed_state.json` (current working directory)
- **Format**: JSON
- **Schema**: Application-specific state structure

Example:
```json
{
  "epoch": 12345,
  "config": {
    "workers": 10,
    "threshold": 7
  },
  "timestamp": 1703001234
}
```

### Message Format

#### Commit Token Message

When the operator signs and sends a commit, the UI creates a CBOR-encoded message with the following structure:

```python
{
    "type": "commit_token",          # Message type identifier
    "state": {...},                   # The proposed state (JSON object)
    "signature": b'...',              # Ed25519 signature (64 bytes)
    "verify_key": b'...'              # Public verification key (32 bytes)
}
```

**Encoding**: CBOR (RFC 8949)

**Signature Algorithm**: Ed25519 (RFC 8032)
- Signs the UTF-8 encoded JSON representation of the state
- Produces a 64-byte signature
- Includes the 32-byte public verification key

### UI Components

#### Main Window
- **Title**: "AGISWARM Operator Control Panel"
- **Size**: 800x600 pixels (default)

#### Controls

1. **Load Operator Key Button**
   - Opens file dialog to select `.sk` file
   - Validates key is 32 bytes
   - Displays success/error status

2. **Load Proposed State Button**
   - Loads JSON from `proposed_state.json`
   - Validates JSON syntax
   - Displays formatted state in text area

3. **Sign & Send Commit Button**
   - Signs the loaded state with operator key
   - Encodes as CBOR message
   - Sends via UDP to aggregator
   - Shows confirmation dialog

#### Status Display
- **Status Label**: Shows current state (key loaded, ready, error)
- **Color Coding**:
  - Green (`#ccffcc`): Success/ready
  - Red (`#ffcccc`): Error
  - Gray (`#f0f0f0`): Neutral/initializing

#### Activity Log
- Displays timestamped events
- Shows success (✓) and error (✗) messages
- Read-only text area
- Maximum height: 150 pixels

### Error Handling

The UI provides explicit error messages via `QMessageBox` dialogs for:

1. **Missing Operator Key**
   - File not found at specified path
   - Invalid key file size (not 32 bytes)
   - File read errors

2. **Missing Proposed State**
   - File not found at `proposed_state.json`
   - Invalid JSON syntax
   - File read errors

3. **Transmission Errors**
   - Network connectivity issues
   - UDP socket errors
   - CBOR encoding errors

Each error message includes:
- Clear description of the problem
- Suggestions for resolution
- Relevant file paths or commands

### Dependencies

Required for Operator UI:
```python
PyQt5>=5.15.0    # GUI framework
pynacl           # Ed25519 signing
cbor2            # CBOR encoding
```

Install with:
```bash
pip install -r requirements-operator-ui.txt
```

### Usage Example

```bash
# Generate operator key (if not exists)
python operator/keygen.py

# Create a proposed state file
cat > proposed_state.json <<EOF
{
  "epoch": 1,
  "workers": 5,
  "threshold": 3
}
EOF

# Launch the UI
python operator/operator_ui.py
```

In the UI:
1. Click "Load Operator Key" (or it loads automatically from `operator.sk`)
2. Click "Load Proposed State" to load `proposed_state.json`
3. Review the displayed state
4. Click "Sign & Send Commit" to sign and transmit

### Security Considerations

1. **Key Storage**: Operator keys should be stored securely with restricted file permissions
   ```bash
   chmod 600 operator.sk
   ```

2. **Network Security**: The default configuration uses localhost (`127.0.0.1`). For remote operation, ensure:
   - Secure network channel (VPN, SSH tunnel, WireGuard)
   - Firewall rules restrict access to UDP port 6000
   - Consider TLS or authenticated encryption for production

3. **State Validation**: The aggregator must validate:
   - Ed25519 signature correctness
   - Operator authorization (verify key in authorized list)
   - State schema compliance
   - Replay attack prevention (sequence numbers, timestamps)

## Command-Line Interface

For headless operation, use the CLI alternative:

```bash
python operator/operator_cli.py
```

The CLI provides the same signing and transmission functionality without GUI dependencies.

## Aggregator Integration

The aggregator listens on UDP port 6000 for commit tokens from the operator UI. The aggregator should:

1. Receive UDP datagrams on `0.0.0.0:6000`
2. Decode CBOR message
3. Verify message type is `"commit_token"`
4. Extract state, signature, and verify_key
5. Verify Ed25519 signature: `verify_key.verify(signature, json.dumps(state).encode())`
6. Check operator authorization (verify_key in allowed list)
7. Apply state change if valid

### Aggregator Code Example

```python
import socket
import cbor2
import nacl.signing
import nacl.encoding

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 6000))

while True:
    data, addr = sock.recvfrom(65535)
    try:
        msg = cbor2.loads(data)
        if msg.get("type") == "commit_token":
            state = msg["state"]
            signature = msg["signature"]
            verify_key_bytes = msg["verify_key"]
            
            # Verify signature
            verify_key = nacl.signing.VerifyKey(verify_key_bytes)
            state_bytes = json.dumps(state).encode("utf-8")
            verify_key.verify(state_bytes, signature)
            
            # Check authorization (verify_key in authorized_keys)
            # Apply state change
            print(f"Commit accepted from {addr}: {state}")
    except Exception as e:
        print(f"Invalid commit token from {addr}: {e}")
```

## Further Reading

- **PyQt5 Documentation**: https://www.riverbankcomputing.com/static/Docs/PyQt5/
- **NaCl Documentation**: https://pynacl.readthedocs.io/
- **CBOR Specification**: https://cbor.io/
- **Ed25519 Signature Scheme**: https://ed25519.cr.yp.to/
