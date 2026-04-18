# 🗄️ File System Management System
### Final Year Project — Python + Streamlit

---

## ▶️ How to Run

```bash
# 1. Clone / extract the project folder
cd fs_project

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the app
streamlit run app.py
```

The app opens in your browser at **http://localhost:8501**

---

## 📦 Project Structure

```
fs_project/
├── app.py          ← Streamlit UI (main entry point)
├── models.py       ← OOP classes: File, Directory, Disk
├── allocator.py    ← Allocation strategies (Contiguous/Linked/Indexed)
├── free_space.py   ← Bit-vector free-space manager
├── metrics.py      ← Fragmentation & utilisation metrics
├── requirements.txt
└── README.md
```

---

## 🧩 Module Explanations

### `models.py` — Core OOP Classes

| Class | Purpose |
|---|---|
| `File` | Stores name, size, blocks, permissions, content, timestamps |
| `Directory` | Tree node with `files` dict + `subdirs` dict + parent pointer |
| `Disk` | Fixed 100-block storage with block_owner map & free-space manager |

### `free_space.py` — Bit-Vector Manager
Maintains a Python boolean list where `False = free` and `True = occupied`.
- `find_contiguous(n)` — finds a run of n consecutive free blocks (for contiguous allocation)
- `find_free_blocks(n)` — finds any n free blocks (for linked/indexed)
- `count_free_runs()` — counts fragmentation holes

### `allocator.py` — Allocation Strategies

| Strategy | How it works | Overhead |
|---|---|---|
| **Contiguous** | n consecutive blocks; fast seek | External fragmentation |
| **Linked** | Any n blocks; each "points" to next | No direct access |
| **Indexed** | 1 index block + n data blocks | +1 block per file |

### `metrics.py` — Performance Metrics
- **Internal fragmentation** = `Σ(blocks × block_size) − file_size`
- **External fragmentation** = number of distinct free-block holes
- **Disk utilisation** = `used / total × 100%`

### `app.py` — Streamlit UI
8 pages accessible from the sidebar:
1. **Dashboard** — Live disk map, pie chart, fragmentation, directory tree
2. **Create File** — Name, size, permissions, allocation method selector
3. **Delete File** — Dropdown + confirm, auto-frees blocks
4. **Read File** — Metadata table + content viewer (checks read permission)
5. **Write File** — Overwrite or Append (checks write permission)
6. **Directory Ops** — `ls`, `mkdir`, `cd` tabs
7. **FAT Table** — Full File Allocation Table + block-owner map
8. **Activity Log** — Timestamped audit trail

---

## 🧪 Sample Test Cases

### Test 1 — Create a file with Contiguous allocation
1. Sidebar → Select **Contiguous**
2. Menu → **📁 Create File**
3. Name: `report.txt` | Size: `1024` bytes | Check Read + Write
4. Click **💾 Create File**
- **Expected:** 2 blocks allocated (1024/512), blue blocks appear on disk map.

### Test 2 — Linked allocation scatter
1. Select **Linked** in sidebar
2. Create `notes.txt` | Size: `512`
3. Dashboard → disk map shows purple block anywhere on disk.

### Test 3 — Indexed allocation overhead
1. Select **Indexed**
2. Create `data.bin` | Size: `1536` (3 data blocks needed)
3. FAT Table → block list has 4 entries (1 inode + 3 data).

### Test 4 — Not enough space
1. Repeat Create File until disk is near full
2. Try creating a large file
- **Expected:** Red error: "Contiguous allocation failed…"

### Test 5 — Permission denied on Read
1. Create `secret.txt` with **Read unchecked**
2. Menu → **📖 Read File** → select `secret.txt`
- **Expected:** "Permission denied: file has no read permission."

### Test 6 — Delete and reclaim space
1. Note free blocks in Dashboard
2. Delete any file
3. Dashboard → free blocks increase by file's block count.

### Test 7 — Directory navigation
1. Menu → **📂 Directory Ops** → mkdir tab → create `docs`
2. cd tab → navigate to `docs`
3. Path indicator in sidebar updates to `/docs`
4. Create a file inside `docs` — it appears only under that directory.

### Test 8 — Internal fragmentation
1. Create `tiny.txt` | Size: `1` byte
2. Dashboard → **Fragmentation** card shows **511 B** internal frag (1 block = 512 B used for 1 B).

---

## 🏗️ OOP Design Summary

```
Disk ──────────────────────────────────────
  │  total_blocks=100, block_size=512
  │  free_space: BitVectorFreeSpace
  │  block_owner: {blk_idx → (fname, method)}
  │
  └── used by Allocators ─────────────────
        ContiguousAllocator.allocate(n, fname)
        LinkedAllocator.allocate(n, fname)
        IndexedAllocator.allocate(n, fname)

Directory (tree) ──────────────────────────
  root /
  ├── files: {name → File}
  └── subdirs: {name → Directory}
                └── files: {...}

File ───────────────────────────────────────
  name, size, allocated_blocks,
  alloc_method, permissions, content, created
```

---

## 🔧 Configuration

Edit the top of `app.py` or `models.py` to change:

```python
Disk(total_blocks=100, block_size=512)
# ↑ change 100 → more blocks, 512 → different block size (bytes)
```
