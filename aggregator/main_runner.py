import asyncio
from aggregator.aggregator import Aggregator

async def main():
    agg = Aggregator("configs/app_config.yaml", "configs/example_matrix.json")
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: agg, local_addr=('127.0.0.1', 6000)
    )
    print("Aggregator running on 6000")
    while True:
        await agg.run_cycle()
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(main())

