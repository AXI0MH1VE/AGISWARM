# AGISWARM Installation Guide

## Core Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### Basic Installation

1. Clone the repository:
```bash
git clone https://github.com/AXI0MH1VE/AGISWARM.git
cd AGISWARM
```

2. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install core dependencies:
```bash
pip install -r requirements.txt
```

This installs the essential packages needed for AGISWARM operation:
- `asyncio` - Asynchronous I/O
- `cbor2` - CBOR encoding/decoding
- `pynacl` - Ed25519 signatures (NaCl/libsodium)
- `numpy` - Numerical computing
- `pyyaml` - YAML configuration
- `pandas` - Data analysis
- `matplotlib` - Plotting
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support

## Optional Components

### Operator UI (PyQt5-based GUI)

The Operator UI is an **optional** graphical interface for operators to manage state commits. It is not required for headless deployments or CLI-only usage.

#### Installation

To use the Operator UI, install the additional PyQt5 dependency:

```bash
pip install -r requirements-operator-ui.txt
```

This installs:
- `PyQt5>=5.15.0` - Qt5 GUI framework for Python

#### Why PyQt5 is Optional

PyQt5 is kept as an optional dependency because:
1. **Large Installation Size**: PyQt5 and its dependencies are substantial (~50-100 MB)
2. **Platform Dependencies**: Requires system Qt libraries on some platforms
3. **Headless Deployments**: Many deployments (servers, embedded systems) don't need a GUI
4. **Build Complexity**: Can have installation issues on certain systems

If you encounter issues installing PyQt5, refer to:
- [PyQt5 Installation Issues](https://forum.qt.io/topic/118699/pip-install-pyqt5-gives-tons-of-errors-why)
- [PyQt5 Troubleshooting](https://stackoverflow.com/questions/72424212/error-on-installing-pyqt5pip-install-pyqt5)

#### Using the Operator UI

Once installed, launch the UI with:

```bash
python operator/operator_ui.py
```

The UI provides:
- Graphical interface for loading proposed state files
- Ed25519 signature signing
- UDP transmission to aggregator
- Activity logging and status display

**Configuration**:
- **UDP Target**: `127.0.0.1:6000` (aggregator endpoint)
- **Operator Key**: `operator.sk` (32-byte Ed25519 secret key)
- **Proposed State**: `proposed_state.json` (JSON format)

Generate an operator key if needed:
```bash
python operator/keygen.py
```

### Alternative: CLI-Only Operation

If you don't want to install PyQt5, use the command-line interface instead:

```bash
python operator/operator_cli.py
```

The CLI provides the same functionality without GUI dependencies.

## Network Bridge Scripts (Linux/macOS)

### Cleanup Network (Linux)

Clean up network namespaces, bridges, and NFTables rules:

```bash
sudo bash bridge/cleanup_network.sh
```

This script:
- Removes the `mesh_ns` network namespace
- Cleans up NFTables rules (inet and bridge filter tables)
- Removes veth pairs

### WiFi Recovery (macOS)

Fix WiFi connectivity issues on macOS:

```bash
bash bridge/macos_wifi_fix.sh
```

This script:
- Cycles WiFi power (off/on)
- Flushes DNS cache
- Renews DHCP lease

**Note**: May require `sudo` for DNS cache flush operations.

## Testing

Run the test suite to verify installation:

```bash
pytest tests/
```

Run specific test modules:
```bash
pytest tests/test_integration.py
pytest tests/test_llft.py
```

## Troubleshooting

### PyQt5 Installation Issues

If you encounter errors installing PyQt5:

1. **Update pip and setuptools**:
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

2. **Use pre-built wheels**: Ensure you're using a compatible Python version (3.8-3.11 recommended)

3. **System dependencies** (Linux):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-pyqt5
   
   # Or install Qt libraries
   sudo apt-get install qt5-default
   ```

4. **Skip PyQt5**: Use the CLI interface instead of the UI

### Network Scripts Not Working

- **cleanup_network.sh**: Requires root/sudo and `nft`/`ip` utilities
- **macos_wifi_fix.sh**: macOS only, requires `networksetup` command

### Import Errors

If you see import errors:
1. Ensure virtual environment is activated
2. Reinstall requirements: `pip install -r requirements.txt`
3. Check Python version: `python --version` (3.8+ required)

## Next Steps

After installation, refer to:
- `README.md` - Architecture and quickstart guide
- `docs/API_REFERENCE.md` - API documentation
- `docs/COMPREHENSIVE_GUIDE.md` - Detailed operational guide
