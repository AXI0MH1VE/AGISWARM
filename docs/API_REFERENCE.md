# AGISWARM API Reference

## Table of Contents
1. [Overview](#overview)
2. [Message Protocol](#message-protocol)
3. [Aggregator API](#aggregator-api)
4. [Worker API](#worker-api)
5. [Operator API](#operator-api)
6. [Network Protocol](#network-protocol)
7. [Configuration API](#configuration-api)
8. [Cryptographic API](#cryptographic-api)
9. [Error Handling](#error-handling)
10. [Examples and Tutorials](#examples-and-tutorials)

---

## Overview

### API Design Principles

AGISWARM APIs are designed with the following principles:
- **Real-time Performance**: Optimized for sub-millisecond latency
- **Deterministic Behavior**: Fixed-point arithmetic and predictable timing
- **Fault Tolerance**: Graceful handling of network partitions and failures
- **Security**: Cryptographic authentication and message integrity
- **Simplicity**: Minimal dependencies and clear interfaces

### API Categories

1. **Internal APIs**: Python interfaces within components
2. **Network APIs**: UDP-based communication protocols
3. **Configuration APIs**: YAML-based configuration management
4. **Cryptographic APIs**: Ed25519 key management and signing

### Protocol Stack

```
┌─────────────────────────────────────┐
│           Application Layer         │
│  (Aggregator/Worker/Operator APIs)  │
├─────────────────────────────────────┤
│           Message Protocol          │
│         (CBOR serialization)        │
├─────────────────────────────────────┤
│           Network Layer             │
│           (UDP/802.11s mesh)        │
├─────────────────────────────────────┤
│           Security Layer            │
│        (Ed25519 signatures)         │
└─────────────────────────────────────┘
```

---

## Message Protocol

### Message Format

All AGISWARM messages use CBOR (Concise Binary Object Representation) for efficient serialization.

#### Common Message Structure

```python
@dataclass
class AGISWARMMessage:
    """Base class for all AGISWARM messages"""
    message_type: str
    version: str = "1.0"
    timestamp: float
    source_id: str
    sequence_number: int
    signature: Optional[bytes] = None
```

#### Message Types

| Type | Purpose | Direction |
|------|---------|-----------|
| `task` | Distribute computational tasks | Aggregator → Worker |
| `result` | Return task results | Worker → Aggregator |
| `heartbeat` | System health monitoring | Worker → Aggregator |
| `commit` | State commit (PoA) | Operator → Aggregator |
| `config` | Configuration updates | Operator → Aggregator |
| `status` | System status query | Any → Aggregator |

### Task Distribution Message

```python
@dataclass
class TaskMessage(AGISWARMMessage):
    """Task distribution message"""
    message_type: str = "task"
    task_id: str
    worker_id: str
    operation: str
    data: Dict[str, Any]
    priority: int = 1
    timeout: float = 1.0
    
    # Example task data structure
    data_examples = {
        "matrix_multiply": {
            "matrix_a": [[1, 2], [3, 4]],
            "matrix_b": [[5, 6], [7, 8]],
            "result_shape": [2, 2]
        },
        "fixed_point_compute": {
            "operation": "multiply",
            "operand_a": "Q1.31_value_1",
            "operand_b": "Q1.31_value_2"
        },
        "control_update": {
            "setpoint": "Q1.31_value",
            "feedback": "Q1.31_value",
            "control_law": "PID_parameters"
        }
    }
```

#### Task Message Example

```python
# Create a task message
task_msg = TaskMessage(
    timestamp=time.time(),
    source_id="aggregator_01",
    sequence_number=1001,
    task_id="task_001",
    worker_id="worker_01",
    operation="matrix_multiply",
    data={
        "matrix_a": [[1.0, 2.0], [3.0, 4.0]],
        "matrix_b": [[5.0, 6.0], [7.0, 8.0]],
        "precision": "Q1.31"
    },
    priority=1,
    timeout=0.1
)

# Serialize to CBOR
import cbor
message_data = cbor.dumps(task_msg.__dict__)

# Send via UDP
socket.sendto(message_data, (worker_ip, worker_port))
```

### Result Message

```python
@dataclass
class ResultMessage(AGISWARMMessage):
    """Task result message"""
    message_type: str = "result"
    task_id: str
    worker_id: str
    status: str  # "success", "error", "timeout"
    result: Any
    computation_time: float
    error_message: Optional[str] = None
    
    # Status codes
    STATUS_SUCCESS = "success"
    STATUS_ERROR = "error"
    STATUS_TIMEOUT = "timeout"
    STATUS_CANCELLED = "cancelled"
```

#### Result Message Example

```python
# Process task result
result_msg = ResultMessage(
    timestamp=time.time(),
    source_id="worker_01",
    sequence_number=2001,
    task_id="task_001",
    worker_id="worker_01",
    status=ResultMessage.STATUS_SUCCESS,
    result=[[19.0, 22.0], [43.0, 50.0]],  # Matrix multiplication result
    computation_time=0.005,  # 5ms computation time
    error_message=None
)

# Sign the message (for security)
from cryptography.hazmat.primitives.asymmetric import ed25519
private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_data)
signature = private_key.sign(cbor.dumps(result_msg.__dict__))
result_msg.signature = signature
```

### Heartbeat Message

```python
@dataclass
class HeartbeatMessage(AGISWARMMessage):
    """System health monitoring message"""
    message_type: str = "heartbeat"
    worker_id: str
    status: str  # "healthy", "degraded", "unhealthy"
    cpu_usage: float
    memory_usage: float
    network_latency: float
    task_queue_size: int
    
    # Status codes
    STATUS_HEALTHY = "healthy"
    STATUS_DEGRADED = "degraded"
    STATUS_UNHEALTHY = "unhealthy"
```

---

## Aggregator API

### Class Reference

```python
class Aggregator:
    """Main aggregator class for task distribution and result aggregation"""
    
    def __init__(self, config_path: str, matrix_path: str):
        """
        Initialize aggregator
        
        Args:
            config_path: Path to YAML configuration file
            matrix_path: Path to fixed-point matrix configuration
        """
        self.config = self._load_config(config_path)
        self.matrix = self._load_matrix(matrix_path)
        self.workers = {}
        self.task_queue = asyncio.Queue()
        self.result_cache = {}
        self.message_handlers = {
            'result': self._handle_result,
            'heartbeat': self._handle_heartbeat,
            'status': self._handle_status
        }
    
    async def start(self, host: str = '127.0.0.1', port: int = 6000):
        """
        Start the aggregator UDP server
        
        Args:
            host: Host address to bind to
            port: UDP port to listen on
        """
        self.server = await asyncio.get_event_loop().create_datagram_endpoint(
            lambda: AggregatorProtocol(self),
            local_addr=(host, port)
        )
        logger.info(f"Aggregator started on {host}:{port}")
    
    async def stop(self):
        """Stop the aggregator"""
        if hasattr(self, 'server'):
            self.server.close()
            await self.server.wait_closed()
    
    async def distribute_task(self, task: Task) -> str:
        """
        Distribute task to available workers
        
        Args:
            task: Task object containing operation and data
            
        Returns:
            Task ID for tracking
        """
        task_id = str(uuid.uuid4())
        
        # Select workers using load balancing
        selected_workers = self._select_workers(task)
        
        # Create fountain-coded task distribution
        coded_task = self._create_fountain_code(task, selected_workers)
        
        # Distribute to workers
        for worker_id, worker_task in coded_task.items():
            await self._send_task(worker_id, worker_task)
        
        # Track task
        self.active_tasks[task_id] = {
            'task': task,
            'workers': selected_workers,
            'start_time': time.time(),
            'status': 'distributed'
        }
        
        return task_id
    
    async def _select_workers(self, task: Task) -> List[str]:
        """
        Select workers for task distribution using load balancing
        
        Args:
            task: Task to distribute
            
        Returns:
            List of worker IDs
        """
        available_workers = [
            worker_id for worker_id, worker_info in self.workers.items()
            if worker_info['status'] == 'healthy'
        ]
        
        if not available_workers:
            raise NoHealthyWorkersError("No healthy workers available")
        
        # Sort by current load
        worker_loads = [
            (worker_id, self.workers[worker_id]['current_load'])
            for worker_id in available_workers
        ]
        worker_loads.sort(key=lambda x: x[1])
        
        # Select workers based on redundancy requirements
        redundancy = self.config.get('fault_tolerance', 2)
        selected = [worker_id for worker_id, _ in worker_loads[:redundancy]]
        
        return selected
    
    def _create_fountain_code(self, task: Task, worker_ids: List[str]) -> Dict[str, Task]:
        """
        Create fountain-coded task distribution
        
        Args:
            task: Original task
            worker_ids: List of worker IDs to distribute to
            
        Returns:
            Dictionary mapping worker_id to coded task
        """
        # Implement rateless fountain coding
        # This is a simplified version - actual implementation would use
        # sophisticated fountain codes like Raptor codes
        
        coded_tasks = {}
        task_data = self._serialize_task_data(task)
        
        for i, worker_id in enumerate(worker_ids):
            # Create unique coded task for each worker
            coded_task = Task(
                task_id=f"{task.task_id}_coded_{i}",
                operation=task.operation,
                data={
                    'coded_data': self._encode_fountain(task_data, i, len(worker_ids)),
                    'worker_index': i,
                    'total_workers': len(worker_ids),
                    'original_task_id': task.task_id
                },
                priority=task.priority,
                timeout=task.timeout
            )
            coded_tasks[worker_id] = coded_task
        
        return coded_tasks
    
    async def _send_task(self, worker_id: str, task: Task):
        """Send task to specified worker"""
        worker_info = self.workers[worker_id]
        
        # Serialize task message
        message = TaskMessage(
            timestamp=time.time(),
            source_id=self.aggregator_id,
            sequence_number=self._get_next_sequence(),
            task_id=task.task_id,
            worker_id=worker_id,
            operation=task.operation,
            data=task.data,
            priority=task.priority,
            timeout=task.timeout
        )
        
        # Sign message for security
        message.signature = self._sign_message(message)
        
        # Send via UDP
        await self._send_udp_message(worker_info['address'], message)
    
    async def _handle_result(self, message: ResultMessage):
        """Handle incoming result message"""
        task_id = message.task_id
        worker_id = message.worker_id
        
        if task_id not in self.active_tasks:
            logger.warning(f"Received result for unknown task: {task_id}")
            return
        
        # Store result
        if task_id not in self.result_cache:
            self.result_cache[task_id] = []
        
        self.result_cache[task_id].append({
            'worker_id': worker_id,
            'result': message.result,
            'status': message.status,
            'computation_time': message.computation_time,
            'timestamp': message.timestamp,
            'signature': message.signature
        })
        
        # Check if we have enough results to decode
        if self._can_decode_result(task_id):
            try:
                final_result = self._decode_and_aggregate(task_id)
                await self._complete_task(task_id, final_result)
            except Exception as e:
                logger.error(f"Failed to decode result for task {task_id}: {e}")
                await self._fail_task(task_id, str(e))
    
    def _can_decode_result(self, task_id: str) -> bool:
        """Check if we have enough coded results to decode original data"""
        results = self.result_cache[task_id]
        task_info = self.active_tasks[task_id]
        required_results = len(task_info['workers'])
        
        # Need at least as many results as original workers
        successful_results = [
            r for r in results 
            if r['status'] == ResultMessage.STATUS_SUCCESS
        ]
        
        return len(successful_results) >= required_results
    
    def _decode_and_aggregate(self, task_id: str) -> Any:
        """Decode fountain codes and aggregate final result"""
        results = self.result_cache[task_id]
        task_info = self.active_tasks[task_id]
        
        # Implement fountain code decoding
        # This is a simplified version
        
        successful_results = [
            r for r in results 
            if r['status'] == ResultMessage.STATUS_SUCCESS
        ]
        
        # Decode using received coded results
        decoded_data = self._decode_fountain(successful_results)
        
        # Apply original operation
        if task_info['task'].operation == 'matrix_multiply':
            # Decode matrix multiplication result
            return self._decode_matrix_result(decoded_data)
        else:
            # For other operations, return decoded data directly
            return decoded_data
    
    async def _complete_task(self, task_id: str, result: Any):
        """Mark task as completed"""
        task_info = self.active_tasks[task_id]
        completion_time = time.time() - task_info['start_time']
        
        # Log metrics
        await self._log_metrics(task_id, completion_time, len(task_info['workers']))
        
        # Update task status
        task_info['status'] = 'completed'
        task_info['result'] = result
        task_info['completion_time'] = completion_time
        
        # Clean up old task data
        del self.active_tasks[task_id]
        del self.result_cache[task_id]
        
        logger.info(f"Task {task_id} completed in {completion_time:.3f}s")
```

### Aggregator Configuration

```python
# Example aggregator configuration (configs/app_config.yaml)
aggregator:
  # Network configuration
  udp_port: 6000
  bind_address: "0.0.0.0"
  
  # Performance configuration
  max_workers: 16
  cycle_time_ms: 50  # 20Hz control frequency
  timeout_ms: 40
  fault_tolerance: 2  # Number of redundant workers
  
  # Fountain coding configuration
  fountain_codes:
    enabled: true
    redundancy_factor: 2
    code_rate: 0.5
    
  # Leader election configuration
  leader_election:
    enabled: true
    heartbeat_interval: 1.0
    election_timeout: 5.0
    
  # Logging configuration
  logging:
    level: "INFO"
    file: "/var/log/aggregator.log"
    max_size: "100MB"
    backup_count: 5
    
  # Security configuration
  security:
    require_signatures: true
    allowed_sources: ["operator_01", "operator_02"]
    key_rotation_interval: 3600  # 1 hour
```

---

## Worker API

### Class Reference

```python
class Worker:
    """Worker class for processing computational tasks"""
    
    def __init__(self, worker_id: str, aggregator_addr: Tuple[str, int]):
        """
        Initialize worker
        
        Args:
            worker_id: Unique worker identifier
            aggregator_addr: (host, port) tuple for aggregator
        """
        self.worker_id = worker_id
        self.aggregator_addr = aggregator_addr
        self.status = WorkerStatus.INITIALIZING
        self.current_load = 0
        self.computation_cache = {}
        
        # Fixed-point arithmetic engine
        self.fp_engine = FixedPointEngine()
        
        # Cryptographic signing
        self.private_key = self._load_private_key()
        self.public_key = self.private_key.public_key()
    
    async def start(self):
        """Start the worker"""
        self.status = WorkerStatus.STARTING
        
        # Connect to aggregator
        await self._connect_to_aggregator()
        
        # Start heartbeat task
        asyncio.create_task(self._heartbeat_loop())
        
        # Start message handling
        asyncio.create_task(self._message_handler())
        
        self.status = WorkerStatus.HEALTHY
        logger.info(f"Worker {self.worker_id} started")
    
    async def stop(self):
        """Stop the worker"""
        self.status = WorkerStatus.STOPPING
        # Clean up resources
        await self._cleanup()
        self.status = WorkerStatus.STOPPED
    
    async def process_task(self, task: Task) -> Result:
        """
        Process a computational task
        
        Args:
            task: Task to process
            
        Returns:
            Result object containing computation outcome
        """
        start_time = time.time()
        
        try:
            # Validate task
            self._validate_task(task)
            
            # Check cache
            cache_key = self._get_cache_key(task)
            if cache_key in self.computation_cache:
                result = self.computation_cache[cache_key]
                logger.debug(f"Task {task.task_id} served from cache")
                return result
            
            # Execute computation
            result_data = await self._execute_computation(task)
            
            # Create result
            result = Result(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status=Result.STATUS_SUCCESS,
                result=result_data,
                computation_time=time.time() - start_time
            )
            
            # Cache result
            self.computation_cache[cache_key] = result
            
            # Sign result
            result.signature = self._sign_result(result)
            
            return result
            
        except Exception as e:
            # Create error result
            error_result = Result(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status=Result.STATUS_ERROR,
                result=None,
                computation_time=time.time() - start_time,
                error_message=str(e)
            )
            error_result.signature = self._sign_result(error_result)
            return error_result
    
    async def _execute_computation(self, task: Task) -> Any:
        """Execute the actual computation"""
        operation = task.operation
        
        if operation == "matrix_multiply":
            return await self._matrix_multiply(task.data)
        elif operation == "fixed_point_compute":
            return await self._fixed_point_compute(task.data)
        elif operation == "control_update":
            return await self._control_update(task.data)
        else:
            raise UnsupportedOperationError(f"Unsupported operation: {operation}")
    
    async def _matrix_multiply(self, data: Dict[str, Any]) -> List[List[float]]:
        """
        Perform matrix multiplication using Q1.31 arithmetic
        
        Args:
            data: Dictionary containing matrix_a, matrix_b
            
        Returns:
            Result matrix
        """
        matrix_a = data['matrix_a']
        matrix_b = data['matrix_b']
        precision = data.get('precision', 'Q1.31')
        
        if precision == 'Q1.31':
            # Use fixed-point arithmetic
            fp_a = [[self.fp_engine.from_float(val) for val in row] for row in matrix_a]
            fp_b = [[self.fp_engine.from_float(val) for val in row] for row in matrix_b]
            
            # Perform fixed-point multiplication
            fp_result = self._matrix_multiply_fp(fp_a, fp_b)
            
            # Convert back to float
            result = [[self.fp_engine.to_float(val) for val in row] for row in fp_result]
            return result
        else:
            # Use floating-point arithmetic
            return self._matrix_multiply_float(matrix_a, matrix_b)
    
    def _matrix_multiply_fp(self, a: List[List[Q1_31]], b: List[List[Q1_31]]) -> List[List[Q1_31]]:
        """Matrix multiplication using Q1.31 fixed-point arithmetic"""
        rows_a, cols_a = len(a), len(a[0])
        rows_b, cols_b = len(b), len(b[0])
        
        if cols_a != rows_b:
            raise ValueError(f"Matrix dimensions don't match: {cols_a} != {rows_b}")
        
        result = [[self.fp_engine.zero() for _ in range(cols_b)] for _ in range(rows_a)]
        
        for i in range(rows_a):
            for j in range(cols_b):
                for k in range(cols_a):
                    result[i][j] = self.fp_engine.add(
                        result[i][j],
                        self.fp_engine.multiply(a[i][k], b[k][j])
                    )
        
        return result
    
    async def _fixed_point_compute(self, data: Dict[str, Any]) -> Q1_31:
        """
        Perform fixed-point computation
        
        Args:
            data: Dictionary containing operation and operands
            
        Returns:
            Fixed-point result
        """
        operation = data['operation']
        operand_a = self.fp_engine.from_float(data['operand_a'])
        operand_b = self.fp_engine.from_float(data['operand_b'])
        
        if operation == "add":
            return self.fp_engine.add(operand_a, operand_b)
        elif operation == "subtract":
            return self.fp_engine.subtract(operand_a, operand_b)
        elif operation == "multiply":
            return self.fp_engine.multiply(operand_a, operand_b)
        elif operation == "divide":
            return self.fp_engine.divide(operand_a, operand_b)
        else:
            raise UnsupportedOperationError(f"Unsupported operation: {operation}")
    
    async def _control_update(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Perform control system update
        
        Args:
            data: Dictionary containing setpoint, feedback, control law
            
        Returns:
            Control output
        """
        setpoint = self.fp_engine.from_float(data['setpoint'])
        feedback = self.fp_engine.from_float(data['feedback'])
        
        # PID control calculation
        error = self.fp_engine.subtract(setpoint, feedback)
        
        # Simplified PID (would need integral and derivative state in real implementation)
        kp = self.fp_engine.from_float(data.get('kp', 1.0))
        control_output = self.fp_engine.multiply(kp, error)
        
        return {
            'control_output': self.fp_engine.to_float(control_output),
            'error': self.fp_engine.to_float(error),
            'timestamp': time.time()
        }
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat messages to aggregator"""
        while self.status == WorkerStatus.HEALTHY:
            try:
                heartbeat = HeartbeatMessage(
                    timestamp=time.time(),
                    source_id=self.worker_id,
                    sequence_number=self._get_next_sequence(),
                    worker_id=self.worker_id,
                    status="healthy",
                    cpu_usage=psutil.cpu_percent(),
                    memory_usage=psutil.virtual_memory().percent,
                    network_latency=await self._measure_latency(),
                    task_queue_size=0  # Would implement task queue monitoring
                )
                
                await self._send_message(heartbeat)
                await asyncio.sleep(self.config.get('heartbeat_interval', 5.0))
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(5.0)
    
    def _load_private_key(self) -> ed25519.Ed25519PrivateKey:
        """Load worker's private key for signing"""
        try:
            with open('operator/operator_private.key', 'rb') as f:
                key_data = f.read()
            return ed25519.Ed25519PrivateKey.from_private_bytes(key_data)
        except FileNotFoundError:
            # Generate temporary key for testing
            return ed25519.Ed25519PrivateKey.generate()
```

### Worker Status Enum

```python
from enum import Enum

class WorkerStatus(Enum):
    """Worker status enumeration"""
    INITIALIZING = "initializing"
    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
```

### Worker Configuration

```python
# Example worker configuration
worker:
  # Identification
  worker_id: "W001"
  
  # Network configuration
  aggregator:
    host: "192.168.100.1"
    port: 6000
  
  # Performance configuration
  max_concurrent_tasks: 4
  task_timeout: 30.0
  
  # Fixed-point configuration
  precision: "Q1.31"
  saturation: true
  
  # Caching configuration
  cache_size: 1000
  cache_ttl: 3600  # 1 hour
  
  # Monitoring configuration
  heartbeat_interval: 5.0
  metrics_interval: 60.0
  
  # Security configuration
  require_message_verification: true
```

---

## Operator API

### Class Reference

```python
class Operator:
    """Operator interface for human-in-the-loop control"""
    
    def __init__(self, aggregator_addr: Tuple[str, int], private_key_path: str):
        """
        Initialize operator
        
        Args:
            aggregator_addr: (host, port) tuple for aggregator
            private_key_path: Path to Ed25519 private key
        """
        self.aggregator_addr = aggregator_addr
        self.private_key = self._load_private_key(private_key_path)
        self.public_key = self.private_key.public_key()
        self.session_id = str(uuid.uuid4())
        
        # Command history
        self.command_history = []
        
        # Status tracking
        self.connected_aggregators = {}
        self.system_status = {}
    
    async def connect(self) -> bool:
        """
        Connect to aggregator
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Test connection with status query
            response = await self.send_command("status")
            logger.info(f"Connected to aggregator at {self.aggregator_addr}")
            return True
        except ConnectionError as e:
            logger.error(f"Failed to connect to aggregator: {e}")
            return False
    
    async def send_command(self, command: str, *args, **kwargs) -> Any:
        """
        Send command to aggregator
        
        Args:
            command: Command type
            *args: Command arguments
            **kwargs: Command keyword arguments
            
        Returns:
            Command response
        """
        # Create command message
        message = OperatorMessage(
            timestamp=time.time(),
            source_id=self.session_id,
            sequence_number=self._get_next_sequence(),
            command=command,
            args=args,
            kwargs=kwargs
        )
        
        # Sign message
        message.signature = self._sign_message(message)
        
        # Send and wait for response
        response = await self._send_and_wait(message)
        
        # Verify response signature
        if response.signature:
            self._verify_signature(response)
        
        self.command_history.append({
            'timestamp': time.time(),
            'command': command,
            'args': args,
            'kwargs': kwargs,
            'response': response
        })
        
        return response
    
    async def commit_state(self, state_data: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Commit signed state (Proof-of-Authority)
        
        Args:
            state_data: State data to commit
            metadata: Additional metadata
            
        Returns:
            True if commit successful
        """
        # Create state commit message
        commit_message = StateCommitMessage(
            timestamp=time.time(),
            source_id=self.session_id,
            sequence_number=self._get_next_sequence(),
            state_data=state_data,
            metadata=metadata or {},
            operator_id=self._get_operator_id()
        )
        
        # Sign commit message
        commit_message.signature = self._sign_message(commit_message)
        
        # Send to aggregator
        try:
            response = await self._send_and_wait(commit_message)
            return response.status == "committed"
        except Exception as e:
            logger.error(f"State commit failed: {e}")
            return False
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status
        
        Returns:
            System status information
        """
        response = await self.send_command("system_status")
        return response.data
    
    async def get_worker_list(self) -> List[Dict[str, Any]]:
        """
        Get list of active workers
        
        Returns:
            List of worker information
        """
        response = await self.send_command("workers_list")
        return response.data
    
    async def inject_fault(self, worker_id: str, fault_type: str) -> bool:
        """
        Inject fault for testing fault tolerance
        
        Args:
            worker_id: ID of worker to fault
            fault_type: Type of fault to inject
            
        Returns:
            True if fault injection successful
        """
        response = await self.send_command("inject_fault", worker_id, fault_type)
        return response.status == "fault_injected"
    
    async def get_metrics(self, time_range: str = "last_hour") -> Dict[str, Any]:
        """
        Get performance metrics
        
        Args:
            time_range: Time range for metrics
            
        Returns:
            Metrics data
        """
        response = await self.send_command("get_metrics", time_range=time_range)
        return response.data
    
    def _load_private_key(self, key_path: str) -> ed25519.Ed25519PrivateKey:
        """Load Ed25519 private key"""
        with open(key_path, 'rb') as f:
            key_data = f.read()
        return ed25519.Ed25519PrivateKey.from_private_bytes(key_data)
    
    def _get_operator_id(self) -> str:
        """Generate operator identifier from public key"""
        public_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return hashlib.sha256(public_bytes).hexdigest()[:16]
```

### Operator Commands

#### Command Interface

```python
class OperatorCommands:
    """Available operator commands"""
    
    # System control commands
    STATUS = "status"
    SYSTEM_STATUS = "system_status"
    SHUTDOWN = "shutdown"
    RESTART = "restart"
    
    # Worker management commands
    WORKERS_LIST = "workers_list"
    WORKER_INFO = "worker_info"
    START_WORKER = "start_worker"
    STOP_WORKER = "stop_worker"
    
    # Task management commands
    TASK_STATUS = "task_status"
    CANCEL_TASK = "cancel_task"
    
    # Configuration commands
    UPDATE_CONFIG = "update_config"
    GET_CONFIG = "get_config"
    RELOAD_CONFIG = "reload_config"
    
    # Metrics commands
    GET_METRICS = "get_metrics"
    RESET_METRICS = "reset_metrics"
    
    # Testing commands
    INJECT_FAULT = "inject_fault"
    LOAD_TEST = "load_test"
    PERFORMANCE_TEST = "performance_test"
    
    # Security commands
    STATE_COMMIT = "state_commit"
    KEY_ROTATION = "key_rotation"
    AUDIT_LOG = "audit_log"
```

#### Command Examples

```python
# Example operator usage
async def operator_example():
    # Initialize operator
    operator = Operator(
        aggregator_addr=("192.168.100.1", 6000),
        private_key_path="operator_private.key"
    )
    
    # Connect to system
    connected = await operator.connect()
    if not connected:
        print("Failed to connect to aggregator")
        return
    
    # Get system status
    status = await operator.get_system_status()
    print(f"System status: {status}")
    
    # Get worker list
    workers = await operator.get_worker_list()
    print(f"Active workers: {len(workers)}")
    for worker in workers:
        print(f"  - {worker['id']}: {worker['status']}")
    
    # Commit state change
    state_data = "config_update: setpoint=0.5"
    success = await operator.commit_state(state_data, {
        "author": "operator_01",
        "reason": "System reconfiguration"
    })
    print(f"State commit: {'success' if success else 'failed'}")
    
    # Get metrics
    metrics = await operator.get_metrics("last_hour")
    print(f"Performance metrics: {metrics}")
    
    # Test fault tolerance
    if workers:
        worker_id = workers[0]['id']
        success = await operator.inject_fault(worker_id, "network_drop")
        print(f"Fault injection: {'success' if success else 'failed'}")
```

---

## Network Protocol

### UDP Message Protocol

#### Message Framing

```
┌─────────────┬──────────────┬─────────────┬─────────────────┐
│  Version    │ Message Type │    Length   │    Payload      │
│  (1 byte)   │  (1 byte)    │  (2 bytes)  │  (Variable)     │
└─────────────┴──────────────┴─────────────┴─────────────────┘
```

#### Message Types

```python
class MessageType:
    """UDP message types"""
    TASK = 0x01
    RESULT = 0x02
    HEARTBEAT = 0x03
    STATUS = 0x04
    CONFIG = 0x05
    COMMIT = 0x06
    ERROR = 0xFF

class ProtocolVersion:
    """Protocol version"""
    VERSION_1_0 = 0x01
```

#### UDP Protocol Implementation

```python
class UDPProtocol:
    """UDP protocol implementation"""
    
    def __init__(self, max_message_size: int = 8192):
        self.max_message_size = max_message_size
        self.message_handlers = {}
    
    def encode_message(self, message: AGISWARMMessage) -> bytes:
        """Encode message to UDP packet"""
        # Serialize message data
        payload = cbor.dumps(message.__dict__)
        
        # Create header
        header = bytes([
            ProtocolVersion.VERSION_1_0,
            self._get_message_type_code(message.message_type),
            len(payload) >> 8,  # Length high byte
            len(payload) & 0xFF  # Length low byte
        ])
        
        return header + payload
    
    def decode_message(self, data: bytes) -> AGISWARMMessage:
        """Decode UDP packet to message"""
        if len(data) < 4:
            raise InvalidMessageError("Message too short")
        
        # Parse header
        version = data[0]
        msg_type = data[1]
        length = (data[2] << 8) | data[3]
        
        if version != ProtocolVersion.VERSION_1_0:
            raise UnsupportedProtocolError(f"Unsupported version: {version}")
        
        if length != len(data) - 4:
            raise InvalidMessageError("Invalid message length")
        
        # Parse payload
        payload = data[4:]
        message_dict = cbor.loads(payload)
        
        # Create appropriate message object
        message_class = self._get_message_class(msg_type)
        return message_class(**message_dict)
    
    def _get_message_type_code(self, message_type: str) -> int:
        """Convert message type string to code"""
        type_map = {
            'task': MessageType.TASK,
            'result': MessageType.RESULT,
            'heartbeat': MessageType.HEARTBEAT,
            'status': MessageType.STATUS,
            'config': MessageType.CONFIG,
            'commit': MessageType.COMMIT,
            'error': MessageType.ERROR
        }
        return type_map.get(message_type, MessageType.ERROR)
```

### Network Security

#### Message Signing

```python
class NetworkSecurity:
    """Network security and message authentication"""
    
    def __init__(self, private_key: ed25519.Ed25519PrivateKey):
        self.private_key = private_key
        self.public_key = private_key.public_key()
        self.allowed_signers = set()
    
    def sign_message(self, message: AGISWARMMessage) -> bytes:
        """Sign message with Ed25519"""
        # Create canonical message representation
        canonical_data = self._create_canonical_representation(message)
        
        # Sign the data
        signature = self.private_key.sign(canonical_data)
        return signature
    
    def verify_message(self, message: AGISWARMMessage, signature: bytes) -> bool:
        """Verify message signature"""
        try:
            canonical_data = self._create_canonical_representation(message)
            self.public_key.verify(signature, canonical_data)
            return True
        except Exception:
            return False
    
    def _create_canonical_representation(self, message: AGISWARMMessage) -> bytes:
        """Create canonical representation for signing"""
        # Exclude signature field from signing
        message_dict = message.__dict__.copy()
        message_dict.pop('signature', None)
        
        # Create deterministic serialization
        return cbor.dumps(message_dict, canonical=True)
```

---

## Configuration API

### YAML Configuration Format

#### Main Configuration

```yaml
# configs/app_config.yaml
# Main AGISWARM application configuration

# Aggregator configuration
aggregator:
  # Network settings
  udp_port: 6000
  bind_address: "0.0.0.0"
  max_message_size: 8192
  
  # Performance settings
  max_workers: 16
  cycle_time_ms: 50
  timeout_ms: 40
  fault_tolerance: 2
  
  # Leader election
  leader_election:
    enabled: true
    heartbeat_interval: 1.0
    election_timeout: 5.0
    
  # Logging
  logging:
    level: "INFO"
    file: "/var/log/aggregator.log"
    max_size: "100MB"
    backup_count: 5
    
  # Security
  security:
    require_signatures: true
    allowed_operators: ["*"]  # Allow all operators
    
# Worker configuration
worker:
  # Identification
  worker_id: "W001"
  
  # Network settings
  aggregator:
    host: "192.168.100.1"
    port: 6000
    
  # Performance settings
  max_concurrent_tasks: 4
  task_timeout: 30.0
  
  # Fixed-point arithmetic
  precision: "Q1.31"
  saturation: true
  
  # Caching
  cache_size: 1000
  cache_ttl: 3600
  
  # Monitoring
  heartbeat_interval: 5.0
  metrics_interval: 60.0
  
  # Security
  require_message_verification: true

# Operator configuration
operator:
  # Network settings
  aggregator:
    host: "192.168.100.1"
    port: 6000
    
  # Key management
  private_key: "operator_private.key"
  public_key: "operator_public.key"
  
  # Session settings
  session_timeout: 3600
  max_command_history: 1000
  
  # Security
  require_state_commit_signature: true

# Network configuration
network:
  # Interface settings
  mesh_interface: "wlan0"
  management_interface: "eth0"
  
  # Mesh networking
  mesh:
    ssid: "EDGE_LATTICE_01"
    channel: 13
    encryption: "sae"
    password: "SuperSecureSecretKey"
    
  # Network isolation
  isolation:
    enabled: true
    namespace: "control_net"
    veth_pair: ["veth_host", "veth_ns"]
    
  # Firewall
  firewall:
    enabled: true
    default_policy: "drop"
    rules_file: "/etc/nftables/agiswarm.conf"

# Fixed-point configuration
fixed_point:
  # Precision settings
  default_precision: "Q1.31"
  available_precisions:
    Q1_15:
      integer_bits: 1
      fractional_bits: 15
      saturation: true
    Q1_31:
      integer_bits: 1
      fractional_bits: 31
      saturation: true
    Q8_24:
      integer_bits: 8
      fractional_bits: 24
      saturation: true
      
  # Math operations
  math:
    saturation_arithmetic: true
    overflow_check: true
    rounding_mode: "nearest"

# Fountain coding configuration
fountain_codes:
  enabled: true
  default_redundancy: 2
  max_redundancy: 4
  
  # Code types
  code_types:
    rateless:
      enabled: true
      rate_adaptation: true
    fixed_rate:
      enabled: true
      rate: 0.5

# Metrics and monitoring
metrics:
  enabled: true
  interval: 60
  
  # Metrics collection
  collect:
    latency: true
    jitter: true
    throughput: true
    error_rate: true
    cpu_usage: true
    memory_usage: true
    
  # Storage
  storage:
    type: "csv"  # csv, json, database
    file: "metrics.csv"
    retention_days: 30
    
  # Reporting
  reporting:
    realtime: true
    alerts: true
    dashboard: false

# Security configuration
security:
  # Cryptography
  crypto:
    algorithm: "Ed25519"
    key_rotation_interval: 3600
    key_backup: true
    
  # Access control
  access_control:
    enabled: true
    roles:
      operator:
        permissions: ["read", "write", "commit"]
      viewer:
        permissions: ["read"]
        
  # Audit logging
  audit:
    enabled: true
    log_level: "INFO"
    log_file: "/var/log/audit.log"
    
# Development settings
development:
  debug_mode: false
  verbose_logging: false
  mock_data: false
  
  # Testing
  testing:
    enabled: false
    mock_workers: 0
    fault_injection: false
```

#### Matrix Configuration

```json
{
  "control_matrices": {
    "pid_controller": {
      "Kp": [1.0, 0.0, 0.0],
      "Ki": [0.1, 0.0, 0.0],
      "Kd": [0.01, 0.0, 0.0]
    },
    "state_feedback": {
      "matrix": [
        [1.2, 0.0, 0.5],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 0.8]
      ],
      "precision": "Q1.31"
    }
  },
  "transformation_matrices": {
    "coordinate_transform": {
      "rotation": [
        [0.0, -1.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0]
      ],
      "precision": "Q1.31"
    }
  }
}
```

### Configuration Loading

```python
class ConfigLoader:
    """Configuration loader and validator"""
    
    @staticmethod
    def load_config(config_path: str) -> Dict[str, Any]:
        """Load and validate configuration"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate configuration
        ConfigLoader._validate_config(config)
        
        return config
    
    @staticmethod
    def _validate_config(config: Dict[str, Any]) -> None:
        """Validate configuration structure and values"""
        required_sections = ['aggregator', 'worker', 'network']
        
        for section in required_sections:
            if section not in config:
                raise ConfigError(f"Missing required section: {section}")
        
        # Validate aggregator configuration
        agg_config = config['aggregator']
        if agg_config.get('udp_port', 0) not in range(1024, 65536):
            raise ConfigError("Invalid aggregator UDP port")
        
        if agg_config.get('max_workers', 0) < 1:
            raise ConfigError("Invalid max_workers value")
        
        # Validate worker configuration
        worker_config = config['worker']
        if not worker_config.get('worker_id'):
            raise ConfigError("Worker ID is required")
        
        if not worker_config.get('aggregator', {}).get('host'):
            raise ConfigError("Aggregator host is required")
        
        # Validate network configuration
        net_config = config['network']
        if net_config.get('mesh_interface') not in ['wlan0', 'wlan1', 'en0']:
            logger.warning(f"Unknown mesh interface: {net_config.get('mesh_interface')}")
    
    @staticmethod
    def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple configurations with proper precedence"""
        merged = {}
        
        for config in configs:
            merged = ConfigLoader._deep_merge(merged, config)
        
        return merged
    
    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigLoader._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
```

---

## Cryptographic API

### Key Management

```python
class KeyManager:
    """Cryptographic key management"""
    
    def __init__(self, key_directory: str = "keys"):
        self.key_directory = Path(key_directory)
        self.key_directory.mkdir(exist_ok=True)
    
    def generate_operator_keypair(self, name: str = "operator") -> Tuple[Path, Path]:
        """Generate Ed25519 key pair for operator"""
        # Generate private key
        private_key = ed25519.Ed25519PrivateKey.generate()
        
        # Serialize private key
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Serialize public key
        public_key = private_key.public_key()
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        # Save keys
        private_path = self.key_directory / f"{name}_private.key"
        public_path = self.key_directory / f"{name}_public.key"
        
        with open(private_path, 'wb') as f:
            f.write(private_bytes)
        
        with open(public_path, 'wb') as f:
            f.write(public_bytes)
        
        # Set permissions
        private_path.chmod(0o600)  # Owner read/write only
        public_path.chmod(0o644)   # Owner read/write, others read
        
        return private_path, public_path
    
    def load_private_key(self, key_path: Path) -> ed25519.Ed25519PrivateKey:
        """Load Ed25519 private key"""
        with open(key_path, 'rb') as f:
            key_data = f.read()
        
        return ed25519.Ed25519PrivateKey.from_private_bytes(key_data)
    
    def load_public_key(self, key_path: Path) -> ed25519.Ed25519PublicKey:
        """Load Ed25519 public key"""
        with open(key_path, 'rb') as f:
            key_data = f.read()
        
        return ed25519.Ed25519PublicKey.from_public_bytes(key_data)
    
    def export_public_key(self, public_key: ed25519.Ed25519PublicKey, format: str = "raw") -> bytes:
        """Export public key in specified format"""
        if format == "raw":
            return public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
        elif format == "pem":
            return public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        elif format == "ssh":
            return public_key.public_bytes(
                encoding=serialization.Encoding.OpenSSH,
                format=serialization.PublicFormat.OpenSSH
            )
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def import_public_key(self, key_data: bytes, format: str = "raw") -> ed25519.Ed25519PublicKey:
        """Import public key from specified format"""
        if format == "raw":
            return ed25519.Ed25519PublicKey.from_public_bytes(key_data)
        elif format == "pem":
            return serialization.load_pem_public_key(key_data)
        elif format == "ssh":
            return serialization.load_ssh_public_key(key_data)
        else:
            raise ValueError(f"Unsupported import format: {format}")
```

### Message Signing and Verification

```python
class MessageSigner:
    """Message signing and verification"""
    
    def __init__(self, private_key: ed25519.Ed25519PrivateKey):
        self.private_key = private_key
        self.public_key = private_key.public_key()
    
    def sign_message(self, message_data: Dict[str, Any]) -> bytes:
        """Sign message data"""
        # Create canonical representation
        canonical_data = self._create_canonical_bytes(message_data)
        
        # Sign the data
        signature = self.private_key.sign(canonical_data)
        return signature
    
    def verify_message(self, message_data: Dict[str, Any], signature: bytes) -> bool:
        """Verify message signature"""
        try:
            canonical_data = self._create_canonical_bytes(message_data)
            self.public_key.verify(signature, canonical_data)
            return True
        except Exception:
            return False
    
    def _create_canonical_bytes(self, message_data: Dict[str, Any]) -> bytes:
        """Create canonical bytes for signing"""
        # Remove signature field if present
        data_copy = message_data.copy()
        data_copy.pop('signature', None)
        
        # Sort keys for deterministic ordering
        sorted_data = {k: data_copy[k] for k in sorted(data_copy.keys())}
        
        # Serialize with canonical CBOR
        return cbor.dumps(sorted_data, canonical=True)

class SignatureValidator:
    """Signature validation utilities"""
    
    def __init__(self, trusted_public_keys: Dict[str, ed25519.Ed25519PublicKey]):
        self.trusted_keys = trusted_public_keys
    
    def validate_signature(self, message_data: Dict[str, Any], signature: bytes, signer_id: str) -> bool:
        """Validate signature from trusted signer"""
        if signer_id not in self.trusted_keys:
            return False
        
        public_key = self.trusted_keys[signer_id]
        
        try:
            # Create canonical representation
            data_copy = message_data.copy()
            data_copy.pop('signature', None)
            sorted_data = {k: data_copy[k] for k in sorted(data_copy.keys())}
            canonical_data = cbor.dumps(sorted_data, canonical=True)
            
            # Verify signature
            public_key.verify(signature, canonical_data)
            return True
        except Exception:
            return False
    
    def add_trusted_key(self, signer_id: str, public_key: ed25519.Ed25519PublicKey):
        """Add trusted public key"""
        self.trusted_keys[signer_id] = public_key
    
    def remove_trusted_key(self, signer_id: str):
        """Remove trusted public key"""
        self.trusted_keys.pop(signer_id, None)
```

### Certificate Management

```python
class CertificateManager:
    """Certificate and key rotation management"""
    
    def __init__(self, key_manager: KeyManager):
        self.key_manager = key_manager
        self.certificates = {}
    
    def create_certificate(self, subject: str, public_key: ed25519.Ed25519PublicKey, 
                         valid_from: datetime, valid_to: datetime) -> str:
        """Create certificate for public key"""
        cert_id = str(uuid.uuid4())
        
        certificate = {
            'id': cert_id,
            'subject': subject,
            'public_key': public_key,
            'valid_from': valid_from,
            'valid_to': valid_to,
            'revoked': False,
            'created_at': datetime.utcnow()
        }
        
        self.certificates[cert_id] = certificate
        return cert_id
    
    def revoke_certificate(self, cert_id: str):
        """Revoke certificate"""
        if cert_id in self.certificates:
            self.certificates[cert_id]['revoked'] = True
            self.certificates[cert_id]['revoked_at'] = datetime.utcnow()
    
    def validate_certificate(self, cert_id: str) -> bool:
        """Validate certificate is not expired or revoked"""
        cert = self.certificates.get(cert_id)
        if not cert or cert['revoked']:
            return False
        
        now = datetime.utcnow()
        if now < cert['valid_from'] or now > cert['valid_to']:
            return False
        
        return True
    
    def rotate_keys(self, operator_name: str) -> Tuple[Path, Path]:
        """Rotate operator keys"""
        # Generate new key pair
        new_private_path, new_public_path = self.key_manager.generate_operator_keypair(
            f"{operator_name}_new"
        )
        
        # Load new public key
        new_public_key = self.key_manager.load_public_key(new_public_path)
        
        # Create certificate for new key
        cert_id = self.create_certificate(
            subject=operator_name,
            public_key=new_public_key,
            valid_from=datetime.utcnow(),
            valid_to=datetime.utcnow() + timedelta(days=365)
        )
        
        return new_private_path, new_public_path
```

---

## Error Handling

### Error Types

```python
class AGISWARMError(Exception):
    """Base exception for all AGISWARM errors"""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code or self.__class__.__name__

class NetworkError(AGISWARMError):
    """Network-related errors"""
    pass

class MessageError(AGISWARMError):
    """Message format and processing errors"""
    pass

class ConfigurationError(AGISWARMError):
    """Configuration-related errors"""
    pass

class CryptographicError(AGISWARMError):
    """Cryptographic operation errors"""
    pass

class WorkerError(AGISWARMError):
    """Worker-related errors"""
    pass

class AggregatorError(AGISWARMError):
    """Aggregator-related errors"""
    pass

class TimeoutError(AGISWARMError):
    """Timeout errors"""
    pass

class PermissionError(AGISWARMError):
    """Permission and access control errors"""
    pass

# Specific error codes
class ErrorCodes:
    NETWORK_TIMEOUT = "NET_001"
    MESSAGE_INVALID_FORMAT = "MSG_001"
    CONFIG_MISSING_SECTION = "CFG_001"
    CRYPTO_KEY_INVALID = "CRY_001"
    WORKER_NOT_FOUND = "WRK_001"
    AGGREGATOR_NOT_AVAILABLE = "AGG_001"
    PERMISSION_DENIED = "PER_001"
```

### Error Handling Patterns

```python
class ErrorHandler:
    """Centralized error handling"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    async def handle_network_error(self, error: NetworkError, context: str):
        """Handle network errors"""
        self.logger.error(f"Network error in {context}: {error}")
        
        # Implement retry logic
        if context == "aggregator_connection":
            return await self._retry_aggregator_connection()
        elif context == "worker_communication":
            return await self._retry_worker_communication()
    
    async def handle_message_error(self, error: MessageError, message_data: bytes):
        """Handle message processing errors"""
        self.logger.error(f"Message error: {error}")
        
        # Log malformed message for analysis
        self.logger.debug(f"Malformed message data: {message_data.hex()}")
        
        # Send error response if applicable
        return await self._send_error_response(error)
    
    async def handle_cryptographic_error(self, error: CryptographicError, context: str):
        """Handle cryptographic errors"""
        self.logger.error(f"Cryptographic error in {context}: {error}")
        
        # Implement security measures
        if "signature_verification" in context:
            await self._handle_signature_failure()
        elif "key_loading" in context:
            await self._handle_key_loading_failure()
    
    def create_error_response(self, error: AGISWARMError, request_id: str = None) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'status': 'error',
            'error_code': error.error_code,
            'error_message': str(error),
            'request_id': request_id,
            'timestamp': time.time()
        }
```

### Retry and Circuit Breaker Patterns

```python
class RetryPolicy:
    """Retry policy with exponential backoff"""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    async def execute_with_retry(self, func, *args, **kwargs):
        """Execute function with retry policy"""
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_attempts - 1:
                    break
                
                # Calculate delay with exponential backoff
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                await asyncio.sleep(delay)
        
        raise last_exception

class CircuitBreaker:
    """Circuit breaker for fault tolerance"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        """Execute function through circuit breaker"""
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
```

---

## Examples and Tutorials

### Complete Example: Simple Matrix Multiplication

```python
#!/usr/bin/env python3
"""
Complete example: Matrix multiplication with AGISWARM
"""

import asyncio
import time
from typing import List, Tuple

# AGISWARM imports
from aggregator.aggregator import Aggregator
from worker.worker import Worker
from operator.operator_cli import Operator

async def main():
    """Main example function"""
    print("=== AGISWARM Matrix Multiplication Example ===")
    
    # Configuration
    AGGREGATOR_HOST = "127.0.0.1"
    AGGREGATOR_PORT = 6000
    
    # Start aggregator
    print("Starting aggregator...")
    aggregator = Aggregator("configs/app_config.yaml", "configs/example_matrix.json")
    await aggregator.start(AGGREGATOR_HOST, AGGREGATOR_PORT)
    
    # Start worker
    print("Starting worker...")
    worker = Worker("worker_01", (AGGREGATOR_HOST, AGGREGATOR_PORT))
    await worker.start()
    
    # Start operator
    print("Starting operator...")
    operator = Operator(
        aggregator_addr=(AGGREGATOR_HOST, AGGREGATOR_PORT),
        private_key_path="operator_private.key"
    )
    connected = await operator.connect()
    
    if not connected:
        print("Failed to connect to aggregator")
        return
    
    # Create test matrices
    matrix_a = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    matrix_b = [[9, 8, 7], [6, 5, 4], [3, 2, 1]]
    
    print(f"Matrix A: {matrix_a}")
    print(f"Matrix B: {matrix_b}")
    
    # Create and distribute task
    print("Creating matrix multiplication task...")
    task_data = {
        'matrix_a': matrix_a,
        'matrix_b': matrix_b,
        'operation': 'matrix_multiply',
        'precision': 'Q1.31'
    }
    
    # Use operator to distribute task
    response = await operator.send_command("create_task", task_data)
    task_id = response.task_id
    
    print(f"Task created with ID: {task_id}")
    
    # Wait for completion
    print("Waiting for task completion...")
    start_time = time.time()
    
    while True:
        # Check task status
        status_response = await operator.send_command("task_status", task_id)
        
        if status_response.status == "completed":
            result = status_response.result
            end_time = time.time()
            
            print(f"Task completed in {end_time - start_time:.3f} seconds")
            print(f"Result: {result}")
            
            # Verify result
            expected = [[30, 24, 18], [84, 69, 54], [138, 114, 90]]
            print(f"Expected: {expected}")
            
            # Calculate error
            total_error = sum(
                abs(result[i][j] - expected[i][j])
                for i in range(3) for j in range(3)
            )
            print(f"Total error: {total_error}")
            
            break
        
        elif status_response.status == "failed":
            print(f"Task failed: {status_response.error}")
            break
        
        await asyncio.sleep(0.1)
    
    # Get system metrics
    print("\nSystem metrics:")
    metrics = await operator.get_metrics("last_minute")
    for metric_name, metric_value in metrics.items():
        print(f"  {metric_name}: {metric_value}")
    
    # Cleanup
    print("\nShutting down...")
    await worker.stop()
    await aggregator.stop()

if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
```

### Custom Worker Implementation

```python
#!/usr/bin/env python3
"""
Custom worker implementation for specific computational tasks
"""

import asyncio
import numpy as np
from worker.worker import Worker
from worker.fixed_point import Q1_31

class CustomWorker(Worker):
    """Custom worker with specialized computational capabilities"""
    
    def __init__(self, worker_id: str, aggregator_addr):
        super().__init__(worker_id, aggregator_addr)
        self.specialized_tasks = {
            'fft_compute': self._fft_compute,
            'filter_apply': self._apply_filter,
            'neural_network_inference': self._neural_network_inference
        }
    
    async def process_task(self, task):
        """Override to handle custom task types"""
        if task.operation in self.specialized_tasks:
            return await self.specialized_tasks[task.operation](task)
        else:
            # Fall back to standard processing
            return await super().process_task(task)
    
    async def _fft_compute(self, task):
        """Fast Fourier Transform computation"""
        data = task.data
        signal = data['signal']
        sample_rate = data['sample_rate']
        
        # Convert to numpy array
        signal_array = np.array(signal, dtype=np.float64)
        
        # Perform FFT
        fft_result = np.fft.fft(signal_array)
        magnitude = np.abs(fft_result)
        phase = np.angle(fft_result)
        
        # Convert back to standard Python types
        result = {
            'magnitude': magnitude.tolist(),
            'phase': phase.tolist(),
            'frequencies': (np.fft.fftfreq(len(signal_array), 1/sample_rate)).tolist()
        }
        
        return Result(
            task_id=task.task_id,
            worker_id=self.worker_id,
            status=Result.STATUS_SUCCESS,
            result=result
        )
    
    async def _apply_filter(self, task):
        """Apply digital filter to signal"""
        data = task.data
        signal = data['signal']
        filter_coefficients = data['filter_coefficients']
        
        # Implement simple FIR filter
        filtered_signal = []
        for i in range(len(signal)):
            value = 0.0
            for j, coef in enumerate(filter_coefficients):
                if i - j >= 0:
                    value += coef * signal[i - j]
            filtered_signal.append(value)
        
        return Result(
            task_id=task.task_id,
            worker_id=self.worker_id,
            status=Result.STATUS_SUCCESS,
            result={'filtered_signal': filtered_signal}
        )
    
    async def _neural_network_inference(self, task):
        """Neural network inference"""
        data = task.data
        input_vector = data['input_vector']
        weights = data['weights']
        biases = data['biases']
        
        # Simple feedforward inference
        output = input_vector
        
        for layer_weights, layer_biases in zip(weights, biases):
            # Matrix multiplication
            new_output = []
            for i in range(len(layer_biases)):
                value = layer_biases[i]
                for j, weight in enumerate(layer_weights[i]):
                    value += weight * output[j]
                
                # Apply ReLU activation
                value = max(0, value)
                new_output.append(value)
            
            output = new_output
        
        return Result(
            task_id=task.task_id,
            worker_id=self.worker_id,
            status=Result.STATUS_SUCCESS,
            result={'output': output}
        )

async def run_custom_worker():
    """Run custom worker"""
    worker = CustomWorker(
        worker_id="custom_worker_01",
        aggregator_addr=("127.0.0.1", 6000)
    )
    await worker.start()

if __name__ == "__main__":
    asyncio.run(run_custom_worker())
```

This comprehensive API reference provides detailed documentation for all AGISWARM components, protocols, and interfaces, enabling developers to build custom extensions and integrations with the system.