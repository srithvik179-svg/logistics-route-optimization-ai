"""Optimized priority queue implementation for A* pathfinding using Python's heapq."""

import heapq
from typing import List, Tuple, Any


class AStarPriorityQueue:
    """Optimized Min-Heap wrapper for priority queue operations in search loops.

    Uses an insertion counter to avoid comparisons on node IDs when priorities match.
    """

    def __init__(self) -> None:
        self._heap: List[Tuple[float, int, str]] = []
        self._counter: int = 0

    def push(self, node_id: str, priority: float) -> None:
        """Pushes a node onto the queue with a priority score (f = g + h).

        Args:
            node_id: Unique Node ID.
            priority: Evaluation score (f-score).
        """
        heapq.heappush(self._heap, (priority, self._counter, node_id))
        self._counter += 1

    def pop(self) -> Tuple[float, str]:
        """Pops the node with the lowest priority score.

        Returns:
            Tuple[float, str]: The priority score and Node ID.
        """
        priority, _, node_id = heapq.heappop(self._heap)
        return priority, node_id

    def is_empty(self) -> bool:
        """Checks if the priority queue is empty.

        Returns:
            bool: True if queue has no elements, else False.
        """
        return len(self._heap) == 0

    def size(self) -> int:
        """Returns the size of the queue.

        Returns:
            int: Number of elements in the queue.
        """
        return len(self._heap)
