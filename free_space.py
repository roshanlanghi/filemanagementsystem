"""
free_space.py — Free Space Management

Implements a bit-vector (bitmap) free-space manager.
Each bit represents one disk block: 0 = free, 1 = occupied.

Class:
    BitVectorFreeSpace
"""

from typing import List, Optional


class BitVectorFreeSpace:
    """
    Bit-vector (bitmap) free-space manager.

    Internally uses a Python list of booleans:
        bitvector[i] = False → block i is FREE
        bitvector[i] = True  → block i is OCCUPIED

    Methods:
        is_free(block)        → bool
        allocate_block(block) → marks block as occupied
        free_block(block)     → marks block as free
        find_free_blocks(n)   → returns list of n free block indices
        find_contiguous(n)    → returns list of n contiguous free blocks
        free_count()          → number of free blocks
    """

    def __init__(self, total_blocks: int):
        self.total_blocks = total_blocks
        self.bitvector    = [False] * total_blocks   # False = free

    # ── Query ──────────────────────────────────
    def is_free(self, block: int) -> bool:
        self._check(block)
        return not self.bitvector[block]

    def free_count(self) -> int:
        return self.bitvector.count(False)

    # ── Mutate ─────────────────────────────────
    def allocate_block(self, block: int) -> None:
        """Mark a specific block as occupied."""
        self._check(block)
        if self.bitvector[block]:
            raise ValueError(f"Block {block} is already allocated.")
        self.bitvector[block] = True

    def free_block(self, block: int) -> None:
        """Mark a specific block as free."""
        self._check(block)
        self.bitvector[block] = False

    # ── Search strategies ──────────────────────
    def find_free_blocks(self, n: int) -> Optional[List[int]]:
        """
        Find any n free blocks (not necessarily contiguous).
        Returns a list of indices or None if not enough free blocks.
        """
        result = [i for i, occupied in enumerate(self.bitvector) if not occupied]
        if len(result) < n:
            return None
        return result[:n]

    def find_contiguous(self, n: int) -> Optional[List[int]]:
        """
        Find a run of n contiguous free blocks.
        Returns the starting run's indices or None if not found.
        """
        start = -1
        count = 0
        for i, occupied in enumerate(self.bitvector):
            if not occupied:
                if start == -1:
                    start = i
                count += 1
                if count == n:
                    return list(range(start, start + n))
            else:
                start = -1
                count = 0
        return None

    def count_free_runs(self) -> int:
        """
        Count the number of distinct contiguous free regions.
        Used for external fragmentation metric.
        """
        runs, in_run = 0, False
        for occupied in self.bitvector:
            if not occupied and not in_run:
                runs += 1
                in_run = True
            elif occupied:
                in_run = False
        return runs

    # ── Internal ───────────────────────────────
    def _check(self, block: int) -> None:
        if block < 0 or block >= self.total_blocks:
            raise IndexError(f"Block index {block} out of range [0, {self.total_blocks-1}].")

    def __repr__(self):
        return (f"<BitVectorFreeSpace total={self.total_blocks} "
                f"free={self.free_count()} used={self.total_blocks-self.free_count()}>")
