"""
metrics.py — Performance Metrics

Calculates:
    - Disk utilisation %
    - Used / free block counts
    - Blocks by allocation method
    - Internal fragmentation (wasted bytes inside allocated blocks)
    - External fragmentation (number of free holes)
    - Total file count (recursive)
"""

import math
from typing import Dict


def compute_metrics(disk, root) -> Dict:
    """
    Compute and return a metrics dictionary for the dashboard.

    Parameters
    ----------
    disk : Disk
    root : Directory (root of the FS tree)

    Returns
    -------
    dict with keys:
        utilisation, used_blocks, free_blocks, total_files,
        internal_frag, external_frag,
        cont_blocks, linked_blocks, indexed_blocks
    """

    # ── Basic counts ──────────────────────────
    free  = disk.free_space.free_count()
    used  = disk.total_blocks - free
    util  = (used / disk.total_blocks) * 100.0

    # ── Method breakdown ──────────────────────
    cont_blocks    = sum(1 for v in disk.block_owner.values() if isinstance(v, tuple) and v[1] == "cont")
    linked_blocks  = sum(1 for v in disk.block_owner.values() if isinstance(v, tuple) and v[1] == "linked")
    indexed_blocks = sum(1 for v in disk.block_owner.values() if isinstance(v, tuple) and v[1] in ("indexed","inode"))

    # ── Internal fragmentation ────────────────
    # Each file may not perfectly fill its last block.
    # internal_frag = Σ (blocks_allocated * block_size - file_size)
    all_files = root.all_files_recursive()
    internal_frag = 0
    for f in all_files:
        allocated_bytes = len(f.allocated_blocks) * disk.block_size
        internal_frag  += max(0, allocated_bytes - f.size)

    # ── External fragmentation ─────────────────
    # Number of distinct free-block runs (holes).
    external_frag = disk.free_space.count_free_runs()

    # ── Total files ───────────────────────────
    total_files = root.total_files()

    return {
        "utilisation"    : round(util, 2),
        "used_blocks"    : used,
        "free_blocks"    : free,
        "total_files"    : total_files,
        "internal_frag"  : internal_frag,
        "external_frag"  : external_frag,
        "cont_blocks"    : cont_blocks,
        "linked_blocks"  : linked_blocks,
        "indexed_blocks" : indexed_blocks,
    }
