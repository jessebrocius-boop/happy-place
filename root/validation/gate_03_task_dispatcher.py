"""
Gate 03: Task Dispatcher
MCE (Minimal Computational Elegance) Standard Implementation

Async-based dispatcher that routes prioritized tasks to their designated node.
Silent operation: No heartbeat logging; audit trail records only dispatch events.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Callable, Optional
from datetime import datetime

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

def _setup_audit_logger() -> logging.Logger:
    """Initialize audit logger pointing to knowledge/corpus/validation_audit.log"""
    audit_log_path = Path(__file__).parent.parent.parent / "knowledge" / "corpus" / "validation_audit.log"
    audit_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("validation_audit")
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers
    if not logger.handlers:
        handler = logging.FileHandler(audit_log_path, mode='a')
        formatter = logging.Formatter(
            fmt='%(asctime)s | GATE_03 | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

audit_logger = _setup_audit_logger()


# ============================================================================
# TASK DISPATCHER CLASS
# ============================================================================

class Dispatcher:
    """
    Asynchronous dispatcher for SCQOS task routing.
    Routes tasks popped from the PriorityQueue to their designated node.
    
    Design principles:
    - Silent operation: No heartbeat/polling logs
    - Audit-only: Records only DISPATCHED and ERROR events
    - Async-native: Uses asyncio for non-blocking I/O
    - MCE compliance: Minimal dependencies, elegant routing logic
    """
    
    def __init__(
        self,
        queue: 'PriorityQueue',
        poll_interval: float = 0.1,
        task_timeout: float = 30.0,
        node_handlers: Optional[Dict[str, Callable]] = None
    ):
        """
        Initialize the dispatcher.
        
        Args:
            queue: PriorityQueue instance to pull tasks from
            poll_interval: Time (seconds) to sleep between queue checks
            task_timeout: Maximum seconds to allow per task execution
            node_handlers: Dict mapping node names to handler callables
        """
        self.queue = queue
        self.poll_interval = poll_interval
        self.task_timeout = task_timeout
        self.node_handlers = node_handlers or {}
        self._is_running = False
        self._tasks_dispatched = 0
        self._tasks_failed = 0
    
    def register_node_handler(self, node_name: str, handler: Callable) -> None:
        """
        Register a handler function for a specific node.
        
        Args:
            node_name: Name of the destination node
            handler: Async callable that executes the task on that node
        """
        self.node_handlers[node_name] = handler
    
    async def dispatch_task(self, task_id: str, priority: int, payload: Any) -> bool:
        """
        Route and execute task to designated node.
        
        Args:
            task_id: Unique task identifier
            priority: Original priority level (1-10)
            payload: Task payload with destination and execution data
        
        Returns:
            True if dispatch successful, False otherwise
        """
        destination = payload.get("destination", "UNKNOWN_NODE")
        handler = self.node_handlers.get(destination)
        
        try:
            if handler is None:
                # No handler registered; log warning and skip
                audit_logger.warning(
                    f"DISPATCHED | task_id={task_id} | destination={destination} | "
                    f"status=NO_HANDLER"
                )
                self._tasks_failed += 1
                return False
            
            # Execute handler with timeout protection
            result = await asyncio.wait_for(
                handler(task_id, payload),
                timeout=self.task_timeout
            )
            
            # Log successful dispatch
            audit_logger.info(
                f"DISPATCHED | task_id={task_id} | priority={priority} | "
                f"destination={destination} | status=SUCCESS"
            )
            self._tasks_dispatched += 1
            return True
            
        except asyncio.TimeoutError:
            audit_logger.error(
                f"DISPATCHED | task_id={task_id} | destination={destination} | "
                f"status=TIMEOUT | timeout={self.task_timeout}s"
            )
            self._tasks_failed += 1
            return False
            
        except Exception as e:
            audit_logger.error(
                f"DISPATCHED | task_id={task_id} | destination={destination} | "
                f"status=ERROR | error={type(e).__name__}: {str(e)}"
            )
            self._tasks_failed += 1
            return False
    
    async def run(self, max_iterations: Optional[int] = None) -> None:
        """
        Main execution loop: continuously dispatch tasks from queue.
        
        Args:
            max_iterations: If set, stop after this many iterations (useful for testing)
        """
        self._is_running = True
        iteration = 0
        
        try:
            while self._is_running:
                if max_iterations and iteration >= max_iterations:
                    break
                
                # Non-blocking check for tasks
                if not self.queue.is_empty():
                    task_id, priority, payload = self.queue.dequeue()
                    await self.dispatch_task(task_id, priority, payload)
                else:
                    # Brief sleep to prevent busy-waiting
                    await asyncio.sleep(self.poll_interval)
                
                iteration += 1
                
        except KeyboardInterrupt:
            audit_logger.info(
                f"DISPATCHER_SHUTDOWN | tasks_dispatched={self._tasks_dispatched} | "
                f"tasks_failed={self._tasks_failed}"
            )
            self._is_running = False
    
    def stop(self) -> None:
        """Signal the dispatcher to stop running."""
        self._is_running = False
    
    def get_stats(self) -> Dict[str, int]:
        """Return dispatcher statistics."""
        return {
            "dispatched": self._tasks_dispatched,
            "failed": self._tasks_failed,
            "queue_size": self.queue.size()
        }


# ============================================================================
# SMOKE TEST
# ============================================================================

async def smoke_test():
    """
    Demonstrate Gate 03 dispatcher functionality with mock node handlers.
    
    Creates a priority queue, registers node handlers, enqueues tasks,
    and dispatches them asynchronously in priority order.
    """
    print("\n" + "="*70)
    print("GATE 03: TASK DISPATCHER SMOKE TEST")
    print("="*70)
    
    # Import PriorityQueue here to avoid circular dependency
    from .gate_02_priority_queue import PriorityQueue
    
    # Initialize queue and dispatcher
    pq = PriorityQueue()
    dispatcher = Dispatcher(
        queue=pq,
        poll_interval=0.05,
        task_timeout=5.0
    )
    
    # Define mock node handlers
    async def handle_alpha_node(task_id: str, payload: Any) -> str:
        """Mock handler for ALPHA node"""
        await asyncio.sleep(0.05)
        return f"ALPHA_EXECUTED: {task_id}"
    
    async def handle_beta_node(task_id: str, payload: Any) -> str:
        """Mock handler for BETA node"""
        await asyncio.sleep(0.05)
        return f"BETA_EXECUTED: {task_id}"
    
    async def handle_gamma_node(task_id: str, payload: Any) -> str:
        """Mock handler for GAMMA node"""
        await asyncio.sleep(0.05)
        return f"GAMMA_EXECUTED: {task_id}"
    
    # Register node handlers
    dispatcher.register_node_handler("ALPHA", handle_alpha_node)
    dispatcher.register_node_handler("BETA", handle_beta_node)
    dispatcher.register_node_handler("GAMMA", handle_gamma_node)
    
    # Enqueue test tasks
    test_tasks = [
        ("dispatch_001", 5, {"destination": "ALPHA", "data": "payload_a"}),
        ("dispatch_002", 1, {"destination": "BETA", "data": "payload_b"}),
        ("dispatch_003", 3, {"destination": "GAMMA", "data": "payload_c"}),
        ("dispatch_004", 2, {"destination": "ALPHA", "data": "payload_d"}),
        ("dispatch_005", 10, {"destination": "BETA", "data": "payload_e"}),
    ]
    
    print("\n[ENQUEUE PHASE]")
    print(f"Enqueuing {len(test_tasks)} tasks to dispatcher...\n")
    
    for task_id, priority, payload in test_tasks:
        pq.enqueue(task_id, priority, payload=payload)
        destination = payload.get("destination", "UNKNOWN")
        print(f"  ✓ Enqueued: {task_id} | Priority {priority} | Node: {destination}")
    
    print(f"\nQueue size: {pq.size()} tasks")
    
    # Run dispatcher for limited iterations
    print("\n[DISPATCH PHASE]")
    print("Running dispatcher to process all tasks...\n")
    
    # Create dispatcher task that runs for a limited number of iterations
    dispatch_task = asyncio.create_task(dispatcher.run(max_iterations=100))
    
    # Wait for queue to empty (with timeout)
    try:
        await asyncio.wait_for(
            _wait_for_empty_queue(pq),
            timeout=5.0
        )
    except asyncio.TimeoutError:
        print("  ⚠ Dispatch timeout - queue still has tasks")
    
    dispatcher.stop()
    await dispatch_task
    
    # Print results
    stats = dispatcher.get_stats()
    print(f"\n[DISPATCH RESULTS]")
    print(f"  ✓ Tasks dispatched: {stats['dispatched']}")
    print(f"  ✗ Tasks failed: {stats['failed']}")
    print(f"  Queue remaining: {stats['queue_size']}")
    
    if stats['dispatched'] == len(test_tasks):
        print(f"\n✓ Smoke test PASSED - All {len(test_tasks)} tasks dispatched successfully")
    else:
        print(f"\n⚠ Smoke test PARTIAL - {stats['dispatched']}/{len(test_tasks)} tasks dispatched")
    
    print("="*70 + "\n")


async def _wait_for_empty_queue(queue: 'PriorityQueue', check_interval: float = 0.05) -> None:
    """Helper: Async wait until queue is empty"""
    while not queue.is_empty():
        await asyncio.sleep(check_interval)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    asyncio.run(smoke_test())
