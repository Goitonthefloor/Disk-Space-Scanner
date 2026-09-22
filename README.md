# Disk-Space-Scanner

Disk-Space-Scanner hilft dabei, schnell einen Überblick über die Speicherbelegung auf lokalen Laufwerken zu gewinnen. Das Tool durchsucht Verzeichnisse, identifiziert große Dateien und Ablage, die überwiegend liegen, und bereitet die Ergebnisse für eine schnelle Entscheidung über Aufräumaktionen auf. Ziel ist eine klare, leicht verständliche Sicht auf genutzten und freien Speicher, ohne dass Einrichtung oder Betrieb übermäßig kompliziert sein muss.

## Zielgruppe

Primär: Entwickler:innen und Systemadministrator:innen, die wiederholt analysieren wollen, wo Speicherplatz auf Servern oder Workstations verloren geht.
Sekundär: Power-User und EDV-Verantwortliche in kleinen Umgebungen, die kein Large-Scale Enterprise-Tool benötigen, aber strukturierte Ausgaben für Reports oder Tickets wollen.

## Konkrete Anwendungsfälle

1. Incident-Analyse nach „Disk full" auf einem Linux-/Windows-Host: Aufruf im betroffenen Mountpoint, um Hotspots zu finden.
2. Regelmäßige Hygiene-Audits auf CI-Runnern oder Bastion-Hosts, bei denen sich Logs und Caches über Zeit anhäufen.
3. Vorbereitung von Speicheroptimierungen/Reclaim-Sprints: mit Kommando schnelle Top-N-Listen von Dateien über einer Größe erzeugen.
4. Integration in Automatisierung: CI-Pipelines oder Wartungsskripts, die nur „zu große" Dateien als Warnung ausgeben wollen.
5. Erste Orientierung auf neuen Systemen: kurze, menschenlesbare Übersicht über Verzeichnisgrößen ohne komplexe Installation.

## Scope-Begrenzungen

- Es wird kein GUI-/Web-Dashboard bereitgestellt.
- Es ist keine dauerhafte Überwachung/Alerting-Komponente enthalten.
- Es wird keine cloud-spezifische Anbindung (z. B. Objektspeicher, virtuelle Laufwerke) nativ unterstützt.
- Es werden keine automatischen Lösch- oder Verschiebeaktionen durchgeführt; es handelt sich um Analyse/Sichtung, nicht um Aufräumbot.
- Lokale Dateisysteme stehen im Vordergrund; Netzwerk-Shares und Container-Overlay-Dateisysteme werden ggf. nicht vollständig abgedeckt.

## Voraussetzungen

- Python 3.11+

## Installation

```bash
git clone https://github.com/Goitonthefloor/Disk-Space-Scanner.git
cd Disk-Space-Scanner
python3 -m pip install -e .
```

Optional mit Testdependencies:

```bash
python3 -m pip install -e ".[dev]"
```

## Schnellstart

```bash
dss scan /pfad/zum/ordner --min-size 100MB --top 20
```

Weitere Beispiele:

```bash
# Aktuelles Verzeichnis, menschenlesbare Ausgabe
dss scan

# Nur Dateien ab 50 MiB, Top 10
dss scan /var/log --min-size 50MiB --top 10

# JSON für CI / Skripte
dss scan /data --min-size 1GB --json

# Symlinks mitverfolgen
dss scan /srv --follow-symlinks
```

### Wichtige Optionen

| Option | Bedeutung |
| --- | --- |
| `path` | Zu scannendes Verzeichnis (Standard: `.`) |
| `--min-size SIZE` | Nur Dateien ≥ Größe listen (`100MB`, `1GiB`, …) |
| `--top N` | Anzahl der größten Dateien (Standard: 20) |
| `--dir-top N` | Anzahl der größten Verzeichnisse (Standard: 15) |
| `--json` | Maschinenlesbare JSON-Ausgabe |
| `--follow-symlinks` | Symbolischen Links folgen |

Das CLI löscht oder verschiebt keine Dateien.

## Entwicklung

```bash
python3 -m pip install -e ".[dev]"
pytest
```

## Beitrag

Contributions sind willkommen. Bitte prüfe Issues/Discussions, bevor du einen größeren Feature-Branch öffnest. Forks, PRs und Fehlerberichte sind ausdrücklich erwünscht; beachte vor allem README/Scope Anpassungen, damit Doku und Implementierung synchron bleiben.
