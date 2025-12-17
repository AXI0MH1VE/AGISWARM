import asyncio
import time
import pytest

# Test LLFT (Leader/backup with fast failover) behavior
# This test simulates primary leader failure and verifies backup takeover

class MockLLFTNode:
    """Mock LLFT node that can act as primary or backup"""
    def __init__(self, node_id, is_primary=False):
        self.id = node_id
        self.is_primary = is_primary
        self.is_alive = True
        self.message_log = []
        self.seq = 0
        
    async def send_message(self, msg):
        """Simulate sending a message if node is primary and alive"""
        if self.is_primary and self.is_alive:
            self.seq += 1
            self.message_log.append((self.seq, msg, time.time()))
            return True
        return False
    
    def fail(self):
        """Simulate node failure"""
        self.is_alive = False
    
    def promote_to_primary(self):
        """Promote backup to primary"""
        self.is_primary = True

class LLFTCoordinator:
    """Coordinator that manages primary/backup failover"""
    def __init__(self, primary, backup):
        self.primary = primary
        self.backup = backup
        self.last_heartbeat = time.time()
        self.failover_timeout = 0.1  # 100ms timeout
        
    async def send_with_failover(self, msg):
        """Send message with automatic failover if primary fails"""
        # Try primary first
        if await self.primary.send_message(msg):
            self.last_heartbeat = time.time()
            return self.primary.id
        
        # If primary failed, promote backup
        if not self.primary.is_alive:
            self.backup.promote_to_primary()
            if await self.backup.send_message(msg):
                return self.backup.id
        
        return None
    
    def get_message_log(self):
        """Get ordered message log from active leader"""
        if self.primary.is_alive:
            return self.primary.message_log
        return self.backup.message_log

def test_llft_failover_basic():
    """Test that backup takes over when primary fails"""
    primary = MockLLFTNode("node-1", is_primary=True)
    backup = MockLLFTNode("node-2", is_primary=False)
    
    # Primary should be active
    assert primary.is_primary
    assert not backup.is_primary
    
    # Simulate primary failure
    primary.fail()
    assert not primary.is_alive
    
    # Backup should be promoted
    backup.promote_to_primary()
    assert backup.is_primary

@pytest.mark.asyncio
async def test_llft_failover_message_delivery():
    """Test ordered message delivery during failover"""
    primary = MockLLFTNode("primary-1", is_primary=True)
    backup = MockLLFTNode("backup-1", is_primary=False)
    coordinator = LLFTCoordinator(primary, backup)
    
    # Send messages through primary
    sender_1 = await coordinator.send_with_failover("msg1")
    assert sender_1 == "primary-1"
    sender_2 = await coordinator.send_with_failover("msg2")
    assert sender_2 == "primary-1"
    
    # Simulate primary failure
    primary.fail()
    
    # Next message should go through backup (now promoted)
    sender_3 = await coordinator.send_with_failover("msg3")
    assert sender_3 == "backup-1"
    
    # Verify backup is now primary
    assert backup.is_primary
    assert len(backup.message_log) == 1
    assert backup.message_log[0][1] == "msg3"

@pytest.mark.asyncio
async def test_llft_ordered_delivery():
    """Test that messages maintain sequential order"""
    primary = MockLLFTNode("leader-1", is_primary=True)
    backup = MockLLFTNode("leader-2", is_primary=False)
    coordinator = LLFTCoordinator(primary, backup)
    
    messages = ["task-1", "task-2", "task-3", "task-4", "task-5"]
    
    # Send first 3 messages via primary
    for i, msg in enumerate(messages[:3]):
        await coordinator.send_with_failover(msg)
    
    assert len(primary.message_log) == 3
    
    # Fail primary and send remaining via backup
    primary.fail()
    for msg in messages[3:]:
        await coordinator.send_with_failover(msg)
    
    # Verify backup received remaining messages
    assert len(backup.message_log) == 2
    assert backup.message_log[0][1] == "task-4"
    assert backup.message_log[1][1] == "task-5"
    
    # Verify sequence numbers are monotonic
    for i, (seq, msg, ts) in enumerate(backup.message_log):
        assert seq == i + 1

def test_llft_failover_demo():
    """Basic LLFT failover demonstration"""
    # Create primary and backup nodes
    primary = MockLLFTNode("primary", is_primary=True)
    backup = MockLLFTNode("backup", is_primary=False)
    
    # Verify initial state
    assert primary.is_primary and primary.is_alive
    assert not backup.is_primary
    
    # Simulate crash and failover
    primary.fail()
    backup.promote_to_primary()
    
    # Verify failover completed
    assert not primary.is_alive
    assert backup.is_primary

