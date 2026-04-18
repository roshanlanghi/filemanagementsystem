"""
models.py — Core OOP classes for the File System Management System

Classes:
    File      — Represents a file with metadata and content
    Directory — Represents a folder node in the directory tree
    Disk      — Represents the simulated storage medium
"""

from datetime import datetime
from typing import Optional, Tuple, List, Dict
from free_space import BitVectorFreeSpace


# ─────────────────────────────────────────────
class File:
    """
    Represents a file stored on the simulated disk.

    Attributes:
        name            : file name (string)
        size            : size in bytes
        allocated_blocks: list of disk block indices
        alloc_method    : 'cont' | 'linked' | 'indexed'
        permissions     : (read, write, execute) boolean tuple
        content         : raw text content
        created         : datetime of creation
        size_blocks     : number of blocks occupied
    """

    def __init__(
        self,
        name: str,
        size: int,
        allocated_blocks: List[int],
        alloc_method: str = "cont",
        permissions: Tuple[bool, bool, bool] = (True, True, False),
        content: str = "",
    ):
        self.name             = name
        self.size             = size
        self.allocated_blocks = allocated_blocks
        self.alloc_method     = alloc_method        # 'cont' | 'linked' | 'indexed'
        self.permissions      = permissions          # (r, w, x)
        self.content          = content
        self.created          = datetime.now()
        self.size_blocks      = len(allocated_blocks)

    def permissions_str(self) -> str:
        """Return UNIX-style permission string, e.g. 'rw-'."""
        r, w, x = self.permissions
        return ("r" if r else "-") + ("w" if w else "-") + ("x" if x else "-")

    def to_dict(self) -> dict:
        """Serialise to dictionary for display/export."""
        return {
            "name"    : self.name,
            "size"    : self.size,
            "blocks"  : self.allocated_blocks,
            "method"  : self.alloc_method,
            "perms"   : self.permissions_str(),
            "created" : self.created.isoformat(),
            "content" : self.content,
        }

    def __repr__(self):
        return f"<File '{self.name}' size={self.size}B blocks={self.allocated_blocks}>"


# ─────────────────────────────────────────────
class Directory:
    """
    Represents a directory node in the file-system tree.

    Attributes:
        name    : directory name
        parent  : parent Directory (None for root)
        files   : dict[name → File]
        subdirs : dict[name → Directory]
        created : datetime of creation
    """

    def __init__(self, name: str, parent: Optional["Directory"] = None):
        self.name    = name
        self.parent  = parent
        self.files   : Dict[str, File]      = {}
        self.subdirs : Dict[str, "Directory"] = {}
        self.created = datetime.now()

    def all_files_recursive(self) -> List[File]:
        """Return every File under this directory (recursive)."""
        result = list(self.files.values())
        for sd in self.subdirs.values():
            result.extend(sd.all_files_recursive())
        return result

    def total_files(self) -> int:
        return len(self.all_files_recursive())

    def __repr__(self):
        return f"<Directory '{self.name}' files={len(self.files)} subdirs={len(self.subdirs)}>"


# ─────────────────────────────────────────────
class Disk:
    """
    Simulates a fixed-size storage medium divided into equal-sized blocks.

    Attributes:
        total_blocks : total number of blocks (default 100)
        block_size   : bytes per block (default 512)
        free_space   : BitVectorFreeSpace instance
        block_owner  : dict[block_idx → (file_name, alloc_method)]
    """

    def __init__(self, total_blocks: int = 100, block_size: int = 512):
        self.total_blocks = total_blocks
        self.block_size   = block_size
        self.free_space   = BitVectorFreeSpace(total_blocks)
        self.block_owner  : Dict[int, Tuple[str, str]] = {}

    @property
    def used_blocks(self) -> int:
        return self.total_blocks - self.free_space.free_count()

    @property
    def free_blocks(self) -> int:
        return self.free_space.free_count()

    def utilisation(self) -> float:
        return (self.used_blocks / self.total_blocks) * 100.0

    def __repr__(self):
        return (f"<Disk total={self.total_blocks} "
                f"used={self.used_blocks} free={self.free_blocks}>")
