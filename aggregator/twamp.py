import asyncio
import time
import argparse
import csv

async def twamp_server(port=9000):
    sock = asyncio.DatagramProtocol()
    loop = asyncio.get_event_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: sock, local_addr=('0.0.0.0', port)
    )
    print(f"TWAMP server on {port}")
    while True:
        data, addr = await loop.sock_recv(transport.get_extra_info('socket'), 4096)
        transport.sendto(data, addr)

async def twamp_client(target, port=9000, samples=200, outfile=None):
    latencies = []
    sock = asyncio.DatagramProtocol()
    loop = asyncio.get_event_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: sock, remote_addr=(target, port)
    )
    for i in range(samples):
        t0 = time.time()
        data = b'twamp-%d' % i
        transport.sendto(data)
        await asyncio.sleep(0.005)
        t1 = time.time()
        latencies.append((i, (t1-t0)*1000.0))
    if outfile:
        with open(outfile, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['sample', 'latency_ms'])
            writer.writerows(latencies)
    print(f"TWAMP results: mean={sum(l[1] for l in latencies)/samples:.2f} ms")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', action='store_true')
    parser.add_argument('--client', action='store_true')
    parser.add_argument('--target', type=str, default='127.0.0.1')
    parser.add_argument('--port', type=int, default=9000)
    parser.add_argument('--samples', type=int, default=200)
    parser.add_argument('--outfile', type=str)
    args = parser.parse_args()
    if args.server:
        asyncio.run(twamp_server(args.port))
    elif args.client:
        asyncio.run(twamp_client(args.target, args.port, args.samples, args.outfile))
    else:
        print("Specify --server or --client")

