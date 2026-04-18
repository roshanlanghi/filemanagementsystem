"""
allocator.py — Storage Allocation Strategies

Implements three classic disk allocation methods:

1. ContiguousAllocator  — Allocates n consecutive blocks.
2. LinkedAllocator      — Allocates n any-free blocks (linked via metadata).
3. IndexedAllocator     — Reserves one index block + (n-1) data blocks.

Each allocator:
  - Checks for sufficient free space.
  - Updates disk.free_space (BitVector).
  - Updates disk.block_owner mapping.
  - Raises MemoryError on failure.
"""

from typing import List
import math


class BaseAllocator:
    """Shared helpers for all allocators."""

    def __init__(self, disk):
        self.disk = disk

    def _mark(self, blocks: List[int], fname: str, method: str) -> None:
        """Mark a list of blocks as occupied in the bitvector and owner map."""
        for b in blocks:
            self.disk.free_space.allocate_block(b)
            self.disk.block_owner[b] = (fname, method)

    def allocate(self, n: int, fname: str) -> List[int]:
        raise NotImplementedError


# ─────────────────────────────────────────────
class ContiguousAllocator(BaseAllocator):
    """
    Contiguous Allocation
    ─────────────────────
    All n blocks are stored as a sequential run on disk.
    Fast sequential access; suffers from external fragmentation.
    Requires a contiguous free segment of size n.
    """

    def allocate(self, n: int, fname: str) -> List[int]:
        if n <= 0:
            n = 1
        blocks = self.disk.free_space.find_contiguous(n)
        if blocks is None:
            free = self.disk.free_space.free_count()
            raise MemoryError(
                f"Contiguous allocation failed: need {n} contiguous blocks, "
                f"but largest contiguous run is insufficient "
                f"(total free = {free})."
            )
        self._mark(blocks, fname, "cont")
        return blocks


# ─────────────────────────────────────────────
class LinkedAllocator(BaseAllocator):
    """
    Linked Allocation
    ─────────────────
    Blocks are scattered; each block conceptually points to the next.
    No external fragmentation; no direct access.
    Uses any n free blocks (non-contiguous OK).
    """

    def allocate(self, n: int, fname: str) -> List[int]:
        if n <= 0:
            n = 1
        blocks = self.disk.free_space.find_free_blocks(n)
        if blocks is None:
            free = self.disk.free_space.free_count()
            raise MemoryError(
                f"Linked allocation failed: need {n} blocks, "
                f"only {free} free blocks available."
            )
        self._mark(blocks, fname, "linked")
        return blocks


# ─────────────────────────────────────────────
class IndexedAllocator(BaseAllocator):
    """
    Indexed Allocation
    ──────────────────
    One block is reserved as the 'index block' (i-node) that stores
    pointers to all data blocks.  Supports direct access.
    Total blocks needed = n_data + 1 (for the index block itself).
    The index block is marked with method 'inode'.
    """

    def allocate(self, n: int, fname: str) -> List[int]:
        if n <= 0:
            n = 1
        total_needed = n + 1   # +1 for the index/inode block
        blocks = self.disk.free_space.find_free_blocks(total_needed)
        if blocks is None:
            free = self.disk.free_space.free_count()
            raise MemoryError(
                f"Indexed allocation failed: need {total_needed} blocks "
                f"(1 index + {n} data), only {free} free."
            )
        index_block  = blocks[0]
        data_blocks  = blocks[1:]

        # Mark index block distinctly
        self.disk.free_space.allocate_block(index_block)
        self.disk.block_owner[index_block] = (fname, "inode")

        # Mark data blocks
        self._mark(data_blocks, fname, "indexed")

        return blocks   # first element is index block, rest are data blocks
