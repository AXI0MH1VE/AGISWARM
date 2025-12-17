#!/bin/bash

# Kill previous
danger() { echo "$*" >&2; }
pkill -f "python worker/worker.py" 2>/dev/null || danger "No previous workers"
pkill -f "python aggregator/main_runner.py" 2>/dev/null || danger "No previous aggregator"

echo "Starting Edge-Lattice Simulation..."
mkdir -p logs

# Start Workers
for i in {0..7}; do
    PORT=$((6001 + i))
    python worker/worker.py $PORT > logs/worker_$i.log 2>&1 &
    echo "Started Worker $i on port $PORT"
done

# Start Aggregator
# (Requires main_runner to wrap aggregator)
cat <<EOF > aggregator/main_runner.py
import asyncio
from aggregator import Aggregator

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
EOF

python aggregator/main_runner.py > logs/aggregator.log 2>&1 &
AGG_PID=$!
echo "Aggregator PID: $AGG_PID"

echo "System Running. Start 'python operator/operator_cli.py' to drive the control loop."
echo "Logs in ./logs/"
wait $AGG_PID

