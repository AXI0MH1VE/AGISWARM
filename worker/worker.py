import asyncio
import random
import cbor2
import time
import sys
sys.path.insert(0, '../aggregator')
from fixed_point import matvec_fixed

class WorkerProtocol(asyncio.DatagramProtocol):
    def __init__(self, worker_id, jitter_range, failure_prob):
        self.id = worker_id
        self.jitter = jitter_range
        self.fail = failure_prob

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        if random.random() < self.fail:
            return # Simulated packet loss/crash

        msg = cbor2.loads(data)
        if msg['t'] == 'TASK':
            asyncio.create_task(self.process_task(msg, addr))

    async def process_task(self, msg, addr):
        sleep_ms = random.uniform(*self.jitter)
        await asyncio.sleep(sleep_ms / 1000.0)
        
        # Extract coded matrix block and x_fixed vector from the message
        x_fixed = msg['x']
        coeffs = msg['c']
        
        # Compute matrix-vector product: y = M * x
        # If coded matrix M is provided, use it; otherwise fall back to identity-like behavior
        if 'M' in msg and msg['M']:
            coded_matrix = msg['M']
            result_vec = matvec_fixed(coded_matrix, x_fixed)
        else:
            # Fallback for backward compatibility: simple coded computation
            result_vec = []
            for i in range(len(x_fixed)):
                acc = 0
                for c_idx, coeff in enumerate(coeffs):
                    if c_idx < len(x_fixed):
                        acc += coeff * x_fixed[c_idx]
                result_vec.append(acc)
        
        resp = {
            "t": "RES",
            "seq": msg['seq'],
            "tid": msg['tid'],
            "w": self.id,
            "y": result_vec,
            "c": msg['c']
        }
        self.transport.sendto(cbor2.dumps(resp), addr)

async def main():
    port = int(sys.argv[1])
    transport, protocol = await asyncio.get_event_loop().create_datagram_endpoint(
        lambda: WorkerProtocol(port, (5, 30), 0.1),
        local_addr=('127.0.0.1', port)
    )
    print(f"Worker listening on {port}")
    await asyncio.Future() # Run forever

if __name__ == "__main__":
    asyncio.run(main())

