import asyncio
import logging
import json
import time
import cbor2
import numpy as np
from .fixed_point import to_fixed, matvec_fixed, add_sat
from .coding import RatelessCoder
from .cbor_schemas import pack_task, pack_proposed_state
from .poa_gate import PoAGate

logging.basicConfig(level=logging.INFO, format='%(asctime)s | AGG | %(message)s')

def import_yaml(f):
    import yaml
    return yaml.safe_load(f)

class Aggregator(asyncio.DatagramProtocol):
    def __init__(self, config_path, matrix_path):
        with open(config_path) as f: self.cfg = import_yaml(f)
        with open(matrix_path) as f: self.mat = json.load(f)
        self.N = self.cfg['system']['N']
        self.R = self.cfg['system']['R']
        self.worker_base_port = self.cfg['transport']['worker_port_start']
        self.x_curr = [to_fixed(x) for x in self.mat['x0']]
        self.u = [to_fixed(u) for u in self.mat['u']]
        self.B_fixed = [[to_fixed(val) for val in row] for row in self.mat['B']]
        self.seq = 0
        self.coder = RatelessCoder(self.mat['A'], self.R)
        self.poa = PoAGate("authorized_keys.txt")
        self.results_buffer = []
        self.cycle_start_ts = 0
        self.transport = None
        self.next_state_buffer = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        try:
            msg = cbor2.loads(data)
            if msg['t'] == 'RES':
                self.handle_result(msg)
            elif msg['t'] == 'COMMIT':
                self.handle_commit(msg)
        except Exception as e:
            logging.error(f"Bad packet: {e}")

    def handle_result(self, msg):
        if msg['seq'] != self.seq: return
        self.results_buffer.append((msg['c'], msg['y']))

    def handle_commit(self, msg):
        if msg['seq'] != self.seq: return
        is_valid = self.poa.verify(str(self.seq).encode(), msg['sig'], msg['pk'])
        if is_valid:
            self.commit_and_advance()
        else:
            logging.warning("Invalid Signature received!")

    async def run_cycle(self):
        self.seq += 1
        self.results_buffer = []
        self.cycle_start_ts = time.time()
        logging.info(f"--- Starting Cycle {self.seq} ---")
        for i in range(self.N):
            coeffs, coded_row_block = self.coder.generate_task(self.x_curr)
            payload = pack_task(self.seq, i, coeffs, self.x_curr, coded_row_block)
            self.transport.sendto(payload, ('127.0.0.1', self.worker_base_port + i))
        while len(self.results_buffer) < self.R:
            if (time.time() - self.cycle_start_ts) > 0.5:
                logging.error("Cycle Timeout - Stragglers detected")
                return
            await asyncio.sleep(0.005)
        Ax_next = self.coder.decode(self.results_buffer)
        Bu = matvec_fixed(self.B_fixed, self.u)
        x_next_candidate = [add_sat(a, b) for a, b in zip(Ax_next, Bu)]
        logging.info(f"Proposed State: {[x/2**31 for x in x_next_candidate]}")
        with open("proposed_state.json", "w") as f:
            json.dump({"seq": self.seq, "x": x_next_candidate}, f)
        self.next_state_buffer = x_next_candidate
        # Wait for COMMIT message from operator_cli.py

    def commit_and_advance(self):
        self.x_curr = self.next_state_buffer
        logging.info(f"Cycle {self.seq} COMMITTED. T_cycle: {(time.time()-self.cycle_start_ts)*1000:.2f}ms")
        # Could trigger external events or metrics here

