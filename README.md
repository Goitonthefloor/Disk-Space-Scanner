# DiskSpaceAnalyzer

A cross‑platform, single‑file Python tool that visualises disk usage similar to *TreeSize*, *WinDirStat* or `ncdu`.  
It provides both a **command‑line interface (CLI)** and a **tkinter‑based graphical user interface (GUI)**.

## Features

- Scan any directory or mount point
- Show size, percentage, and file type in a tree or flat list
- Export results as **JSON** or **CSV**
- GUI with live progress, colour‑coding, context‑menu, and lazy‑loading of directories
- New: `--all` flag to scan **all mounted filesystems** and combine them under a virtual root *"Alle Dateisysteme"*
- New: `--list` flag to simply print all detected mount points
- No external dependencies (uses only the Python standard library; optional `psutil` as a fallback for mount detection)

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Goitonthefloor/Disk-Space-Scanner.git
   cd Disk-Space-Scanner
   ```

2. **Make the script executable (optional)**

   ```bash
   chmod +x diskspace_analyzer.py
   ```

3. **Run**

   ```bash
   python3 diskspace_analyzer.py [PATH] [OPTIONS]
   ```

   If you have Python 3.8+ installed, no further steps are required.

## Usage

### CLI

| Option | Description |
|--------|-------------|
| `PATH` | Directory to scan (default: current directory `.`) |
| `--gui` | Launch the graphical interface |
| `--tree` | Show output as a tree (CLI) |
| `--files` | Include files in the tree view |
| `--top N` | Show the N largest entries (flat list, default 50) |
| `--limit N` | Limit children per directory (GUI/CLI tree, default 200) |
| `--max-depth N` | Limit recursion depth (`0` = unlimited) |
| `--follow-symlinks` | Follow symbolic links during scan |
| `--list` | Print all detected mount points and exit |
| `--all` | Scan **all** mounted filesystems and combine results under a virtual root named "Alle Dateisysteme" |
| `--json` | Output the full tree as JSON (stdout) |
| `--help` | Show this help message |

#### Examples

```bash
# Simple scan of home directory, show top 20
python3 diskspace_analyzer.py /home --top 20

# Tree view with files, limited depth
python3 diskspace_analyzer.py /var/log --tree --files --max-depth 3

# Export JSON of the entire filesystem (requires suitable permissions)
sudo python3 diskspace_analyzer.py / --all --json > full_system.json

# List all mount points
python3 diskspace_analyzer.py --list

# Launch GUI starting at /mnt/data
python3 diskspace_analyzer.py --gui /mnt/data
```

### GUI

- **Toolbar**: Choose folder, rescan, stop, export JSON/CSV, show/hide files, set node‑limit.
- **Status bar**: Shows scanned entries, errors, and total size.
- **Treeview**: Displays name, size, percentage, type (folder/file), and full path.
  - Colour coding: directories (blue), files (light gray), errors (red), large nodes (>10 % of total) (yellow on dark).
- **Context‑menu (right‑click)**: Open in file explorer, copy path, show properties.
- **Double‑click** on a folder toggles expansion; lazy‑loading loads children on demand.
- **Progress bar** appears while scanning.

## Output Formats

### JSON

The `--json` flag prints the complete tree structure:

```json
{
  "name": "Alle Dateisysteme",
  "path": "ALL",
  "size": 1234567890,
  "is_file": false,
  "error": null,
  "children": [
    {
      "name": "/",
      "path": "/",
      "size": 987654321,
      "is_file": false,
      "error": null,
      "children": [...]
    },
    ...
  ]
}
```

### CSV

Export via GUI button or manually:

| Pfad | Bytes | Größe | Anteil | Typ |
|------|-------|-------|--------|-----|
| /home/user/file.mkv | 4523891200 | 4.2 GB | 35.2% | file |
| /var/log | 204857600 | 196 MB | 1.6% | dir |

## How `--all` works

When `--all` is specified, the script:

1. Detects all mount points:
   - Linux: reads `/proc/mounts` (filters out `proc`, `sysfs`, `devtmpfs`, `tmpfs`, `devpts`).
   - Fallback: uses `psutil.disk_partitions()` if available.
   - Windows: returns a list of existing drive letters (`C:\\`, `D:\\`, …).
2. For each mount point, runs a full scan.
3. Creates a virtual root node named **"Alle Dateisysteme"** whose children are the individual filesystem roots.
4. The size of the virtual root is the sum of all filesystems.

Thus you get a combined view as if all drives were part of a single hierarchy.

## Notes & Limitations

- The scanner respects filesystem permissions; directories you cannot read will be marked with an error icon and the error message.
- Symbolic links are ignored by default to avoid infinite loops; use `--follow-symlinks` to change this.
- On Windows, the GUI uses the native explorer via the context‑menu; on Linux it tries `xdg-open`, on macOS `open`.
- The tool is intentionally lightweight: no external Python packages are required. If `psutil` is not installed, mount detection still works via `/proc/mounts` (Linux) or a simple drive‑letter scan (Windows).

## License

MIT License – see the [LICENSE](LICENSE) file (if present) or the header inside `diskspace_analyzer.py`.

---

*Created for Rolf Greger (goitonthefloor) – July 2026*