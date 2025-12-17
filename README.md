# Secure, Real-Time Distributed Edge-Lattice Control Fabric

A distributed deterministic control compute mesh, robust to unreliable networks, designed for OpenWRT wireless routers and simulation on standard systems.

---

## Architecture Diagram

```ascii
         +-------------------+          (Air Gap: netns/veth)         +-------------------+
         |   Operator CLI    |<---------[Bridge Node]<===============>|   Aggregator LB   |
         +-------------------+             |                     /-\  +-------------------+
                  ^                         |                     | (Primary+Backup)
       CommitToken |                 +------+--+           Task/Result |
                  |                  |  veth  |        |      ^        |
                  |                  +---/----+        |      |        |
           Human-in-loop                   |           |      |        |
                 (Ed25519 PoA)             |      +----+---+--+--+-----+------+
                                 [802.11s Mesh]   |       |     |     |      |
                                                 (UDP/CBOR)|    |     |      |
                                                  |      (Worker Nodes x N)
                                                  |      [ID, Q1.31 only]
                                                 \|/
   +-------------+   +--------------+   +--------------+   +--------------+
   |  Worker 1   |   |  Worker 2    |...|  Worker N    |
   +-------------+   +--------------+   +--------------+
```

## Key Features

- **Fixed Point:** Q1.31 saturating, no FPU/emulation.
- **Coded Computing:** Rateless block design (fountain-style), tolerate dropped/slow workers.
- **LLFT:** Primary/Backup Leader with fast failover and strong message order.
- **PoA:** Every state commit requires Ed25519 signature (Proof-of-Authority).
- **Zero-Bridge:** Mesh network air-gapped via kernel network namespaces, firewall, veth bridge.

---

## Quickstart: Local Simulation

1. **Install dependencies:**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2. **Generate Ed25519 Keys for Operator:**

    ```bash
    python operator/keygen.py
    ```

3. **Start the simulation:**

    ```bash
    ./scripts/run_simulation.sh
    # in a new terminal
    python operator/operator_cli.py
    ```

4. **Inspect metrics:**

    - `metrics.csv` contains per-cycle timings/jitter
    - Aggregator/worker logs in `logs/`

5. **Test:**

    ```bash
    pytest tests/
    ```

---

## OpenWRT/Deployment Overview

- Mesh setup: see `bridge/openwrt_mesh_example.sh`
- Air gap/netns script: `bridge/netns_setup.sh`
- For real OpenWRT workers, port or cross-compile `worker/c_worker`.

---

## Structure

- `configs/` : Example fixed-point SSM matrices/configs
- `aggregator/`: Aggregator node, core logic, coded computing, LLFT, PoA
- `worker/`: Simulation Python node, optional C worker for OpenWRT
- `operator/`: Human CLI, keygen, signing
- `bridge/`: Shell scripts for netns, isolation, OpenWRT configs
- `scripts/`: Run orchestrators (simulation, latency/jitter measurement)
- `tests/`: Unit and integration test suite

---

## References

See architecture and implementation notes in the main docstring for literature and operational best practices.

---

