#!/usr/bin/env python3
"""
DiskSpaceAnalyzer – cross-platform treesize-like tool
GUI (tkinter) + CLI (headless) for Windows, Linux, macOS
Author: Auto-generated for Rolf Greger
License: MIT
"""

import os
import sys
import json
import argparse
import threading
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from collections import defaultdict

# ──────────────────────────────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────────────────────────────
@dataclass
class Node:
    path: Path
    name: str
    size: int = 0
    children: Dict[str, 'Node'] = field(default_factory=dict)
    is_file: bool = False
    error: Optional[str] = None

    def add_child(self, child: 'Node'):
        self.children[child.name] = child

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.path),
            "size": self.size,
            "is_file": self.is_file,
            "error": self.error,
            "children": {k: v.to_dict() for k, v in self.children.items()}
        }

# ──────────────────────────────────────────────────────────────────────
# Scanner (threaded, with progress callback)
# ──────────────────────────────────────────────────────────────────────
class DiskScanner:
    def __init__(self, progress_cb=None, max_depth: int = 0, follow_symlinks: bool = False):
        self.progress_cb = progress_cb
        self.max_depth = max_depth  # 0 = unlimited
        self.follow_symlinks = follow_symlinks
        self._stop = False
        self._scanned = 0
        self._errors = 0

    def stop(self):
        self._stop = True

    def scan(self, root: Path) -> Node:
        self._stop = False
        self._scanned = 0
        self._errors = 0
        root_node = Node(path=root, name=root.name or str(root))
        self._scan_recursive(root_node, depth=0)
        return root_node

    def _scan_recursive(self, node: Node, depth: int):
        if self._stop:
            return
        if self.max_depth and depth >= self.max_depth:
            return

        try:
            entries = list(node.path.iterdir())
        except (PermissionError, OSError) as e:
            node.error = str(e)
            self._errors += 1
            return

        for entry in entries:
            if self._stop:
                break
            try:
                if entry.is_symlink() and not self.follow_symlinks:
                    continue
                if entry.is_file():
                    size = entry.stat().st_size
                    child = Node(path=entry, name=entry.name, size=size, is_file=True)
                    node.size += size
                    node.add_child(child)
                elif entry.is_dir():
                    child = Node(path=entry, name=entry.name)
                    node.add_child(child)
                    self._scan_recursive(child, depth + 1)
                    node.size += child.size
            except (PermissionError, OSError) as e:
                self._errors += 1
                continue

            self._scanned += 1
            if self.progress_cb and self._scanned % 50 == 0:
                self.progress_cb(self._scanned, self._errors)

        if self.progress_cb:
            self.progress_cb(self._scanned, self._errors)

# ──────────────────────────────────────────────────────────────────────
# Formatters
# ──────────────────────────────────────────────────────────────────────
def fmt_size(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} EB"

def fmt_pct(part: int, total: int) -> str:
    if total == 0:
        return "0.0%"
    return f"{part/total*100:.1f}%"

# ──────────────────────────────────────────────────────────────────────
# CLI Mode
# ──────────────────────────────────────────────────────────────────────
def cli_mode(args):
    print(f"Scanning: {args.path}")
    scanner = DiskScanner(max_depth=args.max_depth, follow_symlinks=args.follow_symlinks)
    start = time.time()
    root = scanner.scan(Path(args.path).resolve())
    elapsed = time.time() - start

    print(f"\nScan complete in {elapsed:.1f}s ({scanner._scanned} items, {scanner._errors} errors)")
    print(f"Total: {fmt_size(root.size)} ({root.size:,} bytes)\n")

    def print_tree(node: Node, prefix: str = "", is_last: bool = True, depth: int = 0):
        if args.max_depth and depth > args.max_depth:
            return
        if node.is_file and not args.files:
            return

        pct = fmt_pct(node.size, root.size)
        marker = "└── " if is_last else "├── "
        name = node.name
        if node.error:
            name += f" ⚠ {node.error}"
        print(f"{prefix}{marker}{name:50s} {fmt_size(node.size):>10s} ({pct})")

        children = sorted(node.children.values(), key=lambda n: n.size, reverse=True)
        if args.limit and len(children) > args.limit:
            children = children[:args.limit]
        new_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(children):
            print_tree(child, new_prefix, i == len(children) - 1, depth + 1)

    if args.tree:
        print_tree(root)
    else:
        # Flat top-N
        def collect(node: Node, out: List[Node]):
            if not node.is_file or args.files:
                out.append(node)
            for c in node.children.values():
                collect(c, out)
        all_nodes = []
        collect(root, all_nodes)
        all_nodes.sort(key=lambda n: n.size, reverse=True)
        for n in all_nodes[:args.top]:
            print(f"{fmt_size(n.size):>10s}  {fmt_pct(n.size, root.size):>6s}  {n.path}")

    if args.json:
        print(json.dumps(root.to_dict(), indent=2))

# ──────────────────────────────────────────────────────────────────────
# GUI Mode (tkinter – stdlib, no extra deps)
# ──────────────────────────────────────────────────────────────────────
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    TK_AVAILABLE = True
except Exception:
    TK_AVAILABLE = False

class DiskSpaceGUI:
    def __init__(self, root_path: Optional[Path] = None):
        self.root = tk.Tk()
        self.root.title("DiskSpaceAnalyzer")
        self.root.geometry("1100x700")
        self.root.minsize(800, 500)

        self.tree_root: Optional[Node] = None
        self.scanner: Optional[DiskScanner] = None
        self.scan_thread: Optional[threading.Thread] = None

        self._build_ui()
        if root_path:
            self.start_scan(root_path)

    def _build_ui(self):
        # Toolbar
        tb = ttk.Frame(self.root)
        tb.pack(fill=tk.X, padx=4, pady=4)

        ttk.Button(tb, text="📁 Ordner wählen", command=self.choose_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb, text="🔄 Neu scannen", command=self.rescan).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb, text="⏹ Stop", command=self.stop_scan).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb, text="💾 Export JSON", command=self.export_json).pack(side=tk.LEFT, padx=2)
        ttk.Button(tb, text="📋 CSV Export", command=self.export_csv).pack(side=tk.LEFT, padx=2)

        ttk.Separator(tb, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)

        self.show_files_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tb, text="Dateien anzeigen", variable=self.show_files_var,
                        command=self.refresh_tree).pack(side=tk.LEFT, padx=4)

        self.limit_var = tk.IntVar(value=200)
        ttk.Label(tb, text="Limit/Node:").pack(side=tk.LEFT)
        ttk.Spinbox(tb, from_=50, to=5000, increment=50, width=6,
                    textvariable=self.limit_var, command=self.refresh_tree).pack(side=tk.LEFT)

        ttk.Separator(tb, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        self.status_var = tk.StringVar(value="Bereit")
        ttk.Label(tb, textvariable=self.status_var).pack(side=tk.LEFT, padx=4)

        # Progressbar
        self.pb = ttk.Progressbar(self.root, mode='indeterminate')
        self.pb.pack(fill=tk.X, padx=4)

        # Treeview
        columns = ("size", "pct", "type", "path")
        self.tree = ttk.Treeview(self.root, columns=columns, show="tree headings", selectmode="extended")
        self.tree.heading("#0", text="Name", anchor=tk.W)
        self.tree.heading("size", text="Größe", anchor=tk.E)
        self.tree.heading("pct", text="%", anchor=tk.E)
        self.tree.heading("type", text="Typ", anchor=tk.CENTER)
        self.tree.heading("path", text="Pfad", anchor=tk.W)
        self.tree.column("#0", width=350, minwidth=200)
        self.tree.column("size", width=100, minwidth=80, anchor=tk.E)
        self.tree.column("pct", width=50, minwidth=40, anchor=tk.E)
        self.tree.column("type", width=50, minwidth=40, anchor=tk.CENTER)
        self.tree.column("path", width=400, minwidth=200)

        vsb = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(self.root, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4,0), pady=4)
        vsb.pack(side=tk.LEFT, fill=tk.Y, pady=4, padx=(0,4))
        hsb.pack(side=tk.BOTTOM, fill=tk.X, padx=4)

        # Tags for coloring
        self.tree.tag_configure('dir', foreground='#4a90d9')
        self.tree.tag_configure('file', foreground='#e0e0e0')
        self.tree.tag_configure('error', foreground='#ff6b6b')
        self.tree.tag_configure('big', foreground='#ffd93d', background='#2a2a2a')

        # Context menu
        self.ctx_menu = tk.Menu(self.root, tearoff=0)
        self.ctx_menu.add_command(label="Im Explorer öffnen", command=self.open_in_explorer)
        self.ctx_menu.add_command(label="Pfad kopieren", command=self.copy_path)
        self.ctx_menu.add_command(label="Eigenschaften", command=self.show_properties)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", self.on_double_click)

    def choose_folder(self):
        path = filedialog.askdirectory(title="Zu scannenden Ordner wählen")
        if path:
            self.start_scan(Path(path))

    def start_scan(self, path: Path):
        if self.scan_thread and self.scan_thread.is_alive():
            return
        self.status_var.set(f"Scanne: {path} …")
        self.pb.start(10)
        self.tree_root = None
        self.tree.delete(*self.tree.get_children())

        self.scanner = DiskScanner(progress_cb=self._scan_progress, max_depth=0)
        self.scan_thread = threading.Thread(target=self._run_scan, args=(path,), daemon=True)
        self.scan_thread.start()

    def _run_scan(self, path: Path):
        try:
            self.tree_root = self.scanner.scan(path.resolve())
            self.root.after(0, self._scan_done)
        except Exception as e:
            self.root.after(0, lambda: self._scan_error(str(e)))

    def _scan_progress(self, scanned: int, errors: int):
        self.root.after(0, lambda: self.status_var.set(f"Gescannt: {scanned:,} Einträge  |  Fehler: {errors}"))

    def _scan_done(self):
        self.pb.stop()
        self.status_var.set(f"Fertig: {fmt_size(self.tree_root.size)}  |  {self.scanner._scanned:,} Einträge  |  {self.scanner._errors} Fehler")
        self.populate_tree(self.tree_root)

    def _scan_error(self, msg: str):
        self.pb.stop()
        self.status_var.set(f"Fehler: {msg}")
        messagebox.showerror("Scan-Fehler", msg)

    def stop_scan(self):
        if self.scanner:
            self.scanner.stop()
        self.status_var.set("Scan gestoppt")

    def rescan(self):
        if self.tree_root:
            self.start_scan(self.tree_root.path)

    def populate_tree(self, node: Node, parent_id: str = ""):
        limit = self.limit_var.get()
        children = sorted(node.children.values(), key=lambda n: n.size, reverse=True)
        if limit and len(children) > limit:
            children = children[:limit]

        for child in children:
            if child.is_file and not self.show_files_var.get():
                continue

            pct = fmt_pct(child.size, self.tree_root.size)
            tags = ('dir',) if not child.is_file else ('file',)
            if child.error:
                tags = ('error',)
            elif child.size > self.tree_root.size * 0.1:
                tags = ('big',)

            iid = self.tree.insert(parent_id, tk.END, text=child.name,
                                   values=(fmt_size(child.size), pct,
                                           "📁" if not child.is_file else "📄",
                                           str(child.path)),
                                   tags=tags, open=False)
            # lazy load children on expand
            if not child.is_file and child.children:
                self.tree.insert(iid, tk.END, text="…", values=("", "", "", ""), tags=('placeholder',))

        self.tree.tag_bind('placeholder', '<Button-1>', lambda e: "break")

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        if self.tree_root:
            self.populate_tree(self.tree_root)

    def export_json(self):
        if not self.tree_root:
            return
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("JSON", "*.json")],
                                            title="Als JSON speichern")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.tree_root.to_dict(), f, indent=2)
            self.status_var.set(f"Exportiert: {path}")

    def export_csv(self):
        if not self.tree_root:
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")],
                                            title="Als CSV speichern")
        if path:
            rows = []
            def collect(n: Node):
                rows.append((str(n.path), n.size, fmt_size(n.size),
                             fmt_pct(n.size, self.tree_root.size), "file" if n.is_file else "dir"))
                for c in n.children.values():
                    collect(c)
            collect(self.tree_root)
            import csv
            with open(path, 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(["Pfad", "Bytes", "Größe", "Anteil", "Typ"])
                w.writerows(rows)
            self.status_var.set(f"CSV exportiert: {path}")

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.ctx_menu.post(event.x_root, event.y_root)

    def _get_selected_node(self) -> Optional[Node]:
        sel = self.tree.selection()
        if not sel:
            return None
        # walk path to find node
        item = sel[0]
        path_parts = []
        while item:
            path_parts.append(self.tree.item(item, "text"))
            item = self.tree.parent(item)
        path_parts.reverse()
        # traverse tree_root
        node = self.tree_root
        for name in path_parts[1:]:  # skip root
            if name in node.children:
                node = node.children[name]
            else:
                return None
        return node

    def open_in_explorer(self):
        node = self._get_selected_node()
        if node:
            import subprocess, platform
            path = str(node.path)
            if platform.system() == "Windows":
                subprocess.run(["explorer", "/select,", path] if node.is_file else ["explorer", path])
            elif platform.system() == "Darwin":
                subprocess.run(["open", "-R", path] if node.is_file else ["open", path])
            else:
                subprocess.run(["xdg-open", str(node.path.parent)])

    def copy_path(self):
        node = self._get_selected_node()
        if node:
            self.root.clipboard_clear()
            self.root.clipboard_append(str(node.path))
            self.status_var.set(f"Kopiert: {node.path}")

    def show_properties(self):
        node = self._get_selected_node()
        if node:
            info = (f"Name: {node.name}\n"
                    f"Pfad: {node.path}\n"
                    f"Größe: {fmt_size(node.size)} ({node.size:,} Bytes)\n"
                    f"Typ: {'Datei' if node.is_file else 'Verzeichnis'}\n"
                    f"Kinder: {len(node.children)}")
            if node.error:
                info += f"\nFehler: {node.error}"
            messagebox.showinfo("Eigenschaften", info)

    def on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if item and self.tree.item(item, "values")[2] == "📁":
            # toggle expand
            if self.tree.item(item, "open"):
                self.tree.item(item, open=False)
            else:
                self.tree.item(item, open=True)
                # lazy load children
                children = self.tree.get_children(item)
                if children and self.tree.item(children[0], "tags")[0] == 'placeholder':
                    self.tree.delete(children[0])
                    node = self._get_selected_node()
                    if node:
                        self.populate_tree(node, item)

    def run(self):
        self.root.mainloop()

# ──────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="DiskSpaceAnalyzer – cross-platform disk usage visualizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /home                    # CLI tree view
  %(prog)s /home --top 20           # Top 20 largest
  %(prog)s /home --tree --files     # Tree with files
  %(prog)s /home --json > out.json  # Machine readable
  %(prog)s --gui                    # GUI mode
  %(prog)s --gui /mnt/data          # GUI with start path
        """
    )
    parser.add_argument("path", nargs="?", default=".", help="Pfad zum Scannen (default: .)")
    parser.add_argument("--gui", action="store_true", help="GUI-Modus starten")
    parser.add_argument("--tree", action="store_true", help="Baum-Anzeige (CLI)")
    parser.add_argument("--files", action="store_true", help="Dateien in Baum anzeigen")
    parser.add_argument("--top", type=int, default=50, help="Top-N größte Einträge (flat)")
    parser.add_argument("--limit", type=int, default=200, help="Max Kinder pro Verzeichnis (GUI/CLI)")
    parser.add_argument("--max-depth", type=int, default=0, help="Max Rekursionstiefe (0=unbegrenzt)")
    parser.add_argument("--follow-symlinks", action="store_true", help="Symlinks folgen")
    parser.add_argument("--json", action="store_true", help="JSON-Output")
    parser.add_argument("--csv", action="store_true", help="CSV-Output (CLI)")

    args = parser.parse_args()

    if args.gui:
        if not TK_AVAILABLE:
            print("tkinter nicht verfügbar – GUI nicht möglich.", file=sys.stderr)
            sys.exit(1)
        gui = DiskSpaceGUI(Path(args.path).resolve() if args.path != "." else None)
        gui.run()
    else:
        cli_mode(args)

if __name__ == "__main__":
    main()