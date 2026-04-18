"""
╔══════════════════════════════════════════════════════════════════════╗
║          FILE SYSTEM MANAGEMENT SYSTEM — Final Year Project          ║
║          Built with Python + Streamlit                               ║
╚══════════════════════════════════════════════════════════════════════╝

Modules:
  1. models.py      — File, Directory, Disk classes (OOP core)
  2. allocator.py   — Contiguous / Linked / Indexed allocation
  3. free_space.py  — Bit-vector free-space manager
  4. metrics.py     — Fragmentation & utilisation calculations
  5. app.py         — Streamlit UI (this file)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import math

from models import File, Directory, Disk
from allocator import ContiguousAllocator, LinkedAllocator, IndexedAllocator
from free_space import BitVectorFreeSpace
from metrics import compute_metrics

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="FS Manager",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# GLOBAL CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
}

/* ── Dark terminal theme ── */
.stApp {
    background: #111318;
    color: #e2e8f0;
}

section[data-testid="stSidebar"] {
    background: #111318 !important;
    border-right: 1px solid #1e2332;
}

/* ── Cards ── */
.fs-card {
    background: #151820;
    border: 1px solid #1e2332;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
}

.fs-card-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #4ade80;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.6rem;
}

/* ── Block grid ── */
.block-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 3px;
    margin-top: 0.5rem;
}

.blk {
    width: 18px; height: 18px;
    border-radius: 3px;
    font-size: 0px;
    transition: transform .15s;
}
.blk:hover { transform: scale(1.4); }
.blk-free   { background: #1e2332; border: 1px solid #2d3555; }
.blk-cont   { background: #3b82f6; }
.blk-linked { background: #a855f7; }
.blk-index  { background: #f59e0b; }
.blk-inode  { background: #ef4444; }

/* ── Metric boxes ── */
.metric-row { display: flex; gap: 1rem; margin-bottom: 1rem; }
.metric-box {
    flex: 1;
    background: #151820;
    border: 1px solid #1e2332;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
}
.metric-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem;
    font-weight: 700;
    color: #4ade80;
}
.metric-lbl { font-size: 0.72rem; color: #64748b; margin-top: 4px; }

/* ── Tree view ── */
.tree-node {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    line-height: 1.8;
    color: #94a3b8;
}
.tree-dir  { color: #60a5fa; font-weight: 600; }
.tree-file { color: #e2e8f0; }

/* ── Status pills ── */
.pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 99px;
    font-size: 0.72rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
}
.pill-ok  { background: #14532d; color: #4ade80; }
.pill-err { background: #450a0a; color: #f87171; }
.pill-warn{ background: #422006; color: #fbbf24; }

/* ── Sidebar nav ── */
div[data-testid="stSidebarNav"] { display: none; }

.sidebar-logo {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1rem;
    color: #60a5fa;
    font-weight: 700;
    letter-spacing: 0.05em;
    margin-bottom: 1.5rem;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid #1e2332;
}

/* ── Tables ── */
thead tr th {
    background: #151820 !important;
    color: #4ade80 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important;
}

/* ── Buttons ── */
.stButton > button {
    background: #1a2540;
    color: #60a5fa;
    border: 1px solid #2d3f6e;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    transition: all .2s;
}
.stButton > button:hover {
    background: #2d3f6e;
    color: #fff;
    border-color: #60a5fa;
}

/* selectbox, text_input labels */
label { color: #94a3b8 !important; font-size: 0.82rem !important; }

/* alerts */
.stAlert { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# SESSION STATE BOOTSTRAP
# ──────────────────────────────────────────────
def init_state():
    if "disk" not in st.session_state:
        st.session_state.disk = Disk(total_blocks=100, block_size=512)
    if "root" not in st.session_state:
        st.session_state.root = Directory("/", parent=None)
    if "cwd" not in st.session_state:
        st.session_state.cwd = st.session_state.root
    if "log" not in st.session_state:
        st.session_state.log = []

init_state()

disk: Disk           = st.session_state.disk
root: Directory      = st.session_state.root
cwd: Directory       = st.session_state.cwd


def log(msg: str, level: str = "ok"):
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.log.append({"ts": ts, "msg": msg, "level": level})

def get_allocator(method: str):
    if method == "Contiguous":
        return ContiguousAllocator(disk)
    elif method == "Linked":
        return LinkedAllocator(disk)
    else:
        return IndexedAllocator(disk)

def cwd_path() -> str:
    parts, d = [], st.session_state.cwd
    while d is not None:
        parts.append(d.name)
        d = d.parent
    return "/".join(reversed(parts)).replace("//", "/") or "/"


# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo">🗄️ FS MANAGER v1.0</div>', unsafe_allow_html=True)

    menu = st.radio(
        "OPERATION",
        ["📊 Dashboard", "📁 Create File", "🗑️ Delete File",
         "📖 Read File", "✏️ Write File",
         "📂 Directory Ops", "📋 FAT Table", "📜 Activity Log"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown('<div class="fs-card-title">Allocation Method</div>', unsafe_allow_html=True)
    alloc_method = st.selectbox(
        "Method", ["Contiguous", "Linked", "Indexed"], label_visibility="collapsed"
    )
    st.markdown(f"""
    <div style='font-size:0.72rem; color:#64748b; line-height:1.6;'>
    {'🔵 Blocks are stored consecutively.' if alloc_method=='Contiguous'
     else '🟣 Each block points to the next.' if alloc_method=='Linked'
     else '🟡 Index block holds all pointers.'}
    </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f'<div style="font-family:JetBrains Mono;font-size:0.75rem;color:#4ade80;">📍 {cwd_path()}</div>',
                unsafe_allow_html=True)

    if st.button("🔄 Reset Disk"):
        for key in ["disk","root","cwd","log"]:
            del st.session_state[key]
        st.rerun()


# ──────────────────────────────────────────────
# HELPERS — VISUALIZATIONS
# ──────────────────────────────────────────────
def render_block_map():
    fs = disk.free_space
    html = '<div class="block-grid">'
    for i in range(disk.total_blocks):
        if fs.is_free(i):
            html += f'<div class="blk blk-free" title="Block {i}: FREE"></div>'
        else:
            owner = disk.block_owner.get(i, ("?", "cont"))
            method = owner[1] if isinstance(owner, tuple) else "cont"
            cls = {"cont":"blk-cont","linked":"blk-linked","indexed":"blk-index","inode":"blk-inode"}.get(method,"blk-cont")
            html += f'<div class="blk {cls}" title="Block {i}: {owner[0] if isinstance(owner,tuple) else owner}"></div>'
    html += "</div>"
    return html


def render_dir_tree(directory: Directory, prefix="", is_last=True) -> str:
    connector = "└── " if is_last else "├── "
    lines = [f'<span class="tree-dir">{prefix}{connector}📁 {directory.name}/</span>']
    child_prefix = prefix + ("    " if is_last else "│   ")

    # sub-directories
    subdirs = list(directory.subdirs.values())
    all_items = [(d, True) for d in subdirs] + [(f, False) for f in directory.files.values()]
    for idx, (item, is_dir) in enumerate(all_items):
        last = (idx == len(all_items) - 1)
        conn2 = "└── " if last else "├── "
        pref2 = child_prefix + ("    " if last else "│   ")
        if is_dir:
            lines.append(render_dir_tree(item, child_prefix, last))
        else:
            perm_str = item.permissions_str()
            lines.append(
                f'<span class="tree-file">{child_prefix}{conn2}📄 {item.name} '
                f'<span style="color:#64748b;font-size:0.7rem">[{item.size_blocks}blk | {perm_str}]</span></span>'
            )
    return "\n".join(lines)


def fat_dataframe():
    rows = []
    for fname, f in st.session_state.cwd.files.items():
        rows.append({
            "Name": f.name,
            "Size (B)": f.size,
            "Blocks": len(f.allocated_blocks),
            "Block List": str(f.allocated_blocks[:8]) + ("…" if len(f.allocated_blocks) > 8 else ""),
            "Method": f.alloc_method,
            "Created": f.created.strftime("%H:%M:%S"),
            "Perms": f.permissions_str(),
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["Name","Size (B)","Blocks","Block List","Method","Created","Perms"]
    )


# ──────────────────────────────────────────────
# PAGES
# ──────────────────────────────────────────────

# ── 1. DASHBOARD ──────────────────────────────
if menu == "📊 Dashboard":
    st.markdown("## 📊 System Dashboard")

    m = compute_metrics(disk, root)

    col1, col2, col3, col4 = st.columns(4)
    boxes = [
        (f"{m['utilisation']:.1f}%",  "Disk Utilisation"),
        (f"{m['free_blocks']}",        "Free Blocks"),
        (f"{m['used_blocks']}",        "Used Blocks"),
        (f"{m['total_files']}",        "Total Files"),
    ]
    for col, (val, lbl) in zip([col1,col2,col3,col4], boxes):
        with col:
            st.markdown(f"""
            <div class="metric-box">
              <div class="metric-val">{val}</div>
              <div class="metric-lbl">{lbl}</div>
            </div>""", unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 2])

    with col_a:
        st.markdown('<div class="fs-card"><div class="fs-card-title">Disk Block Map</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:0.7rem;color:#64748b;margin-bottom:8px;">
        🔵 Contiguous &nbsp; 🟣 Linked &nbsp; 🟡 Indexed &nbsp; ⬛ Free
        </div>""", unsafe_allow_html=True)
        st.markdown(render_block_map(), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="fs-card"><div class="fs-card-title">Storage Breakdown</div>', unsafe_allow_html=True)
        labels = ["Free", "Contiguous", "Linked", "Indexed"]
        values = [m['free_blocks'], m['cont_blocks'], m['linked_blocks'], m['indexed_blocks']]
        fig = go.Figure(go.Pie(
            labels=labels, values=values,
            hole=0.55,
            marker_colors=["#1e2332","#3b82f6","#a855f7","#f59e0b"],
            textfont_size=11,
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8", height=260,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(font_size=11),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown('<div class="fs-card"><div class="fs-card-title">Fragmentation</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="metric-row">
          <div class="metric-box">
            <div class="metric-val" style="font-size:1.3rem">{m['internal_frag']} B</div>
            <div class="metric-lbl">Internal Fragmentation</div>
          </div>
          <div class="metric-box">
            <div class="metric-val" style="font-size:1.3rem">{m['external_frag']}</div>
            <div class="metric-lbl">External Frag Holes</div>
          </div>
        </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_d:
        st.markdown('<div class="fs-card"><div class="fs-card-title">Directory Tree</div>', unsafe_allow_html=True)
        tree_html = render_dir_tree(root)
        st.markdown(f'<div class="tree-node">{tree_html}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ── 2. CREATE FILE ─────────────────────────────
elif menu == "📁 Create File":
    st.markdown("## 📁 Create File")
    st.markdown(f"**Current directory:** `{cwd_path()}`")

    with st.form("create_form"):
        fname = st.text_input("File Name", placeholder="report.txt")
        fsize = st.number_input("File Size (bytes)", min_value=1, max_value=50000, value=512)
        content = st.text_area("Initial Content (optional)", height=100)
        perm_r = st.checkbox("Read", value=True)
        perm_w = st.checkbox("Write", value=True)
        perm_x = st.checkbox("Execute", value=False)
        submitted = st.form_submit_button("💾 Create File")

    if submitted:
        if not fname:
            st.error("❌ File name cannot be empty.")
        elif fname in st.session_state.cwd.files:
            st.error(f"❌ File **{fname}** already exists in this directory.")
            log(f"Create failed: '{fname}' already exists", "err")
        else:
            alloc = get_allocator(alloc_method)
            blocks_needed = math.ceil(fsize / disk.block_size)
            try:
                allocated = alloc.allocate(blocks_needed, fname)
                f = File(
                    name=fname, size=fsize,
                    allocated_blocks=allocated,
                    alloc_method=alloc_method.lower(),
                    permissions=(perm_r, perm_w, perm_x),
                    content=content,
                )
                st.session_state.cwd.files[fname] = f
                log(f"Created '{fname}' ({fsize}B, {blocks_needed} blocks, {alloc_method})", "ok")
                st.success(f"✅ File **{fname}** created using **{alloc_method}** allocation!")
                st.markdown(f"""
                <div class="fs-card">
                  <div class="fs-card-title">Allocation Summary</div>
                  <b>Blocks used:</b> {blocks_needed}<br>
                  <b>Block list:</b> <code>{allocated}</code><br>
                  <b>Permissions:</b> {f.permissions_str()}
                </div>""", unsafe_allow_html=True)
            except MemoryError as e:
                st.error(f"❌ {e}")
                log(f"Create failed: {e}", "err")


# ── 3. DELETE FILE ─────────────────────────────
elif menu == "🗑️ Delete File":
    st.markdown("## 🗑️ Delete File")
    st.markdown(f"**Current directory:** `{cwd_path()}`")

    files = list(st.session_state.cwd.files.keys())
    if not files:
        st.info("ℹ️ No files in the current directory.")
    else:
        sel = st.selectbox("Select file to delete", files)
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🗑️ Delete", type="primary"):
                f = st.session_state.cwd.files.pop(sel)
                for blk in f.allocated_blocks:
                    disk.free_space.free_block(blk)
                    disk.block_owner.pop(blk, None)
                log(f"Deleted '{sel}' — freed {len(f.allocated_blocks)} blocks", "warn")
                st.success(f"✅ **{sel}** deleted. Freed **{len(f.allocated_blocks)}** blocks.")
                st.rerun()


# ── 4. READ FILE ───────────────────────────────
elif menu == "📖 Read File":
    st.markdown("## 📖 Read File")
    files = list(st.session_state.cwd.files.keys())
    if not files:
        st.info("ℹ️ No files in current directory.")
    else:
        sel = st.selectbox("Select file", files)
        f: File = st.session_state.cwd.files[sel]
        if not f.permissions[0]:
            st.error("❌ Permission denied: file has no read permission.")
            log(f"Read denied on '{sel}'", "err")
        else:
            st.markdown(f"""
            <div class="fs-card">
              <div class="fs-card-title">File Metadata</div>
              <table style="width:100%;font-size:0.82rem;border-collapse:collapse;">
                <tr><td style="color:#64748b;padding:4px 0">Name</td><td><code>{f.name}</code></td></tr>
                <tr><td style="color:#64748b;padding:4px 0">Size</td><td>{f.size} bytes</td></tr>
                <tr><td style="color:#64748b;padding:4px 0">Blocks</td><td>{f.allocated_blocks}</td></tr>
                <tr><td style="color:#64748b;padding:4px 0">Method</td><td>{f.alloc_method}</td></tr>
                <tr><td style="color:#64748b;padding:4px 0">Created</td><td>{f.created.strftime("%Y-%m-%d %H:%M:%S")}</td></tr>
                <tr><td style="color:#64748b;padding:4px 0">Permissions</td><td><code>{f.permissions_str()}</code></td></tr>
              </table>
            </div>""", unsafe_allow_html=True)

            st.markdown("**File Content:**")
            st.code(f.content if f.content else "(empty file)", language="text")
            log(f"Read '{sel}'", "ok")


# ── 5. WRITE FILE ──────────────────────────────
elif menu == "✏️ Write File":
    st.markdown("## ✏️ Write / Append to File")
    files = list(st.session_state.cwd.files.keys())
    if not files:
        st.info("ℹ️ No files in current directory.")
    else:
        sel = st.selectbox("Select file", files)
        f: File = st.session_state.cwd.files[sel]
        if not f.permissions[1]:
            st.error("❌ Permission denied: file has no write permission.")
            log(f"Write denied on '{sel}'", "err")
        else:
            mode = st.radio("Write mode", ["Overwrite", "Append"], horizontal=True)
            new_content = st.text_area("Content", value=f.content if mode=="Append" else "", height=150)
            if st.button("💾 Save"):
                f.content = new_content
                f.size = len(new_content.encode())
                log(f"{'Overwrote' if mode=='Overwrite' else 'Appended to'} '{sel}'", "ok")
                st.success(f"✅ File **{sel}** updated.")


# ── 6. DIRECTORY OPS ───────────────────────────
elif menu == "📂 Directory Ops":
    st.markdown("## 📂 Directory Operations")
    st.markdown(f"**Current directory:** `{cwd_path()}`")

    tab_ls, tab_mkdir, tab_cd = st.tabs(["📋 ls — List", "📁 mkdir — Create Dir", "🔀 cd — Change Dir"])

    with tab_ls:
        st.markdown("### Files in current directory")
        df = fat_dataframe()
        if df.empty:
            st.info("Empty directory.")
        else:
            st.dataframe(df, use_container_width=True)

        st.markdown("### Sub-directories")
        subs = list(st.session_state.cwd.subdirs.keys())
        if subs:
            for s in subs:
                st.markdown(f"📁 **{s}/**")
        else:
            st.info("No sub-directories.")

    with tab_mkdir:
        dname = st.text_input("New directory name")
        if st.button("📁 Create Directory"):
            if not dname:
                st.error("Name cannot be empty.")
            elif dname in st.session_state.cwd.subdirs:
                st.error(f"Directory **{dname}** already exists.")
            else:
                new_dir = Directory(dname, parent=st.session_state.cwd)
                st.session_state.cwd.subdirs[dname] = new_dir
                log(f"mkdir '{dname}'", "ok")
                st.success(f"✅ Directory **{dname}** created.")

    with tab_cd:
        options = [".. (parent)"] + list(st.session_state.cwd.subdirs.keys())
        target = st.selectbox("Navigate to", options)
        if st.button("🔀 Change Directory"):
            if target == ".. (parent)":
                if st.session_state.cwd.parent is not None:
                    st.session_state.cwd = st.session_state.cwd.parent
                    log("cd ..", "ok")
                    st.rerun()
                else:
                    st.warning("Already at root.")
            else:
                st.session_state.cwd = st.session_state.cwd.subdirs[target]
                log(f"cd '{target}'", "ok")
                st.rerun()


# ── 7. FAT TABLE ───────────────────────────────
elif menu == "📋 FAT Table":
    st.markdown("## 📋 File Allocation Table")
    st.markdown(f"**Directory:** `{cwd_path()}`")

    df = fat_dataframe()
    if df.empty:
        st.info("No files to display.")
    else:
        st.dataframe(df, use_container_width=True, height=300)

    st.markdown("### Block-Owner Map")
    rows2 = [{"Block": k, "Owner": v[0] if isinstance(v,tuple) else v,
               "Method": v[1] if isinstance(v,tuple) else "—"}
             for k, v in sorted(disk.block_owner.items())]
    if rows2:
        st.dataframe(pd.DataFrame(rows2), use_container_width=True, height=250)
    else:
        st.info("Disk is empty.")


# ── 8. ACTIVITY LOG ────────────────────────────
elif menu == "📜 Activity Log":
    st.markdown("## 📜 Activity Log")
    entries = st.session_state.log[::-1]
    if not entries:
        st.info("No activity yet.")
    else:
        for e in entries:
            badge = {"ok":"pill-ok","err":"pill-err","warn":"pill-warn"}.get(e["level"],"pill-ok")
            icon  = {"ok":"✔","err":"✖","warn":"⚠"}.get(e["level"],"✔")
            st.markdown(f"""
            <div style="display:flex;gap:12px;align-items:center;
                        padding:8px 0;border-bottom:1px solid #1e2332;">
              <code style="color:#64748b;font-size:0.72rem">{e["ts"]}</code>
              <span class="pill {badge}">{icon}</span>
              <span style="font-size:0.83rem">{e["msg"]}</span>
            </div>""", unsafe_allow_html=True)
