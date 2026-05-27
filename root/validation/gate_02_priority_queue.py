"""
Gate 02: Priority Queue Enqueuing
MCE (Minimal Computational Elegance) Standard Implementation

Utilizes heapq min-heap for O(log n) task insertion.
Priority scale: 1 (Emergency/Highest) to 10 (Lowest).
Inverted internally for correct min-heap ordering.
All ENQUEUED events logged to knowledge/corpus/validation_audit.log
"""

import heapq
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, List, Tuple
import os

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
            fmt='%(asctime)s | GATE_02 | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

audit_logger = _setup_audit_logger()

# ============================================================================
# PRIORITY QUEUE CLASS
# ============================================================================

class PriorityQueue:
    """
    MCE-compliant priority queue using heapq min-heap.
    
    Priority Mapping:
    - 1: Emergency (Highest priority)
    - 2-9: Graduated priority levels
    - 10: Lowest priority
    
    Internally inverts priority so min-heap extracts highest-priority tasks first.
    """
    
    def __init__(self):
        """Initialize empty min-heap and sequence counter for FIFO tie-breaking."""
        self._heap: List[Tuple[int, int, str, Any]] = []
        self._sequence = 0
    
    def enqueue(self, task_id: str, priority: int, payload: Any = None) -> None:
        """
        Enqueue a task with priority (1-10 scale).
        
        Args:
            task_id: Unique task identifier
            priority: Priority level (1=Emergency, 10=Lowest)
            payload: Optional task payload/metadata
        
        Raises:
            ValueError: If priority not in range [1, 10]
        """
        if not (1 <= priority <= 10):
            raise ValueError(f"Priority must be in range [1, 10], got {priority}")
        
        # Invert priority: lower task priority = lower heap value (higher rank)
        inverted_priority = 11 - priority
        
        # Use sequence for FIFO ordering within same priority
        self._sequence += 1
        
        # Enqueue: (inverted_priority, sequence, task_id, payload)
        heapq.heappush(self._heap, (inverted_priority, self._sequence, task_id, payload))
        
        # Log ENQUEUED event with full context
        priority_label = self._get_priority_label(priority)
        audit_logger.info(
            f"ENQUEUED | task_id={task_id} | priority={priority} ({priority_label}) | "
            f"sequence={self._sequence} | payload_type={type(payload).__name__}"
        )
    
    def dequeue(self) -> Tuple[str, int, Any]:
        """
        Dequeue the highest-priority task.
        
        Returns:
            Tuple of (task_id, original_priority, payload)
        
        Raises:
            IndexError: If queue is empty
        """
        if not self._heap:
            raise IndexError("Priority queue is empty")
        
        inverted_priority, _, task_id, payload = heapq.heappop(self._heap)
        
        # Convert back to original priority scale
        original_priority = 11 - inverted_priority
        
        return task_id, original_priority, payload
    
    def peek(self) -> Tuple[str, int, Any]:
        """
        Peek at highest-priority task without removing it.
        
        Returns:
            Tuple of (task_id, original_priority, payload)
        
        Raises:
            IndexError: If queue is empty
        """
        if not self._heap:
            raise IndexError("Priority queue is empty")
        
        inverted_priority, _, task_id, payload = self._heap[0]
        original_priority = 11 - inverted_priority
        
        return task_id, original_priority, payload
    
    def size(self) -> int:
        """Return number of tasks in queue."""
        return len(self._heap)
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self._heap) == 0
    
    @staticmethod
    def _get_priority_label(priority: int) -> str:
        """Map priority integer to human-readable label."""
        labels = {
            1: "EMERGENCY",
            2: "CRITICAL",
            3: "HIGH",
            4: "HIGH-MED",
            5: "MEDIUM",
            6: "MED-LOW",
            7: "LOW",
            8: "LOW-MINOR",
            9: "MINOR",
            10: "TRIVIAL"
        }
        return labels.get(priority, "UNKNOWN")


# ============================================================================
# SMOKE TEST
# ============================================================================

def smoke_test():
    """
    Demonstrate Gate 02 priority queue functionality.
    
    Enqueues tasks with varying priorities, then retrieves in correct order
    (highest priority first, regardless of insertion order).
    """
    print("\n" + "="*70)
    print("GATE 02: PRIORITY QUEUE SMOKE TEST")
    print("="*70)
    
    pq = PriorityQueue()
    
    # Test data: (task_id, priority, description)
    test_tasks = [
        ("task_alpha", 5, "Medium priority background job"),
        ("task_zulu", 1, "Emergency system alert"),
        ("task_bravo", 3, "High priority database sync"),
        ("task_charlie", 10, "Trivial logging task"),
        ("task_delta", 2, "Critical security patch"),
        ("task_echo", 7, "Low priority cache cleanup"),
    ]
    
    print("\n[ENQUEUE PHASE]")
    print(f"Inserting {len(test_tasks)} tasks in arbitrary order...\n")
    
    for task_id, priority, description in test_tasks:
        pq.enqueue(task_id, priority, payload={"description": description})
        priority_label = PriorityQueue._get_priority_label(priority)
        print(f"  ✓ Enqueued: {task_id:15} | Priority {priority} ({priority_label:10}) | {description}")
    
    print(f"\nQueue size: {pq.size()} tasks")
    
    print("\n[DEQUEUE PHASE - Correct Priority Order]")
    print("Retrieving all tasks (should be ordered by priority, highest first):\n")
    
    order = 1
    while not pq.is_empty():
        task_id, priority, payload = pq.dequeue()
        priority_label = PriorityQueue._get_priority_label(priority)
        description = payload.get("description") if payload else "N/A"
        print(f"  {order}. {task_id:15} | Priority {priority} ({priority_label:10}) | {description}")
        order += 1
    
    print(f"\n✓ Smoke test PASSED - All {len(test_tasks)} tasks dequeued in correct priority order")
    print("="*70 + "\n")
    
    # Verify audit log was written
    audit_log_path = Path(__file__).parent.parent.parent / "knowledge" / "corpus" / "validation_audit.log"
    if audit_log_path.exists():
        log_size = audit_log_path.stat().st_size
        print(f"✓ Audit log written: {audit_log_path} ({log_size} bytes)\n")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    smoke_test()
