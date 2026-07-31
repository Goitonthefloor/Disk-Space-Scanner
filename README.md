# Disk-Space-Scanner

Disk-Space-Scanner hilft dabei, schnell einen Überblick über die Speicherbelegung auf lokalen Laufwerken zu gewinnen. Das Tool durchsucht Verzeichnisse, identifiziert große Dateien und Ablage, die überwiegend liegen, und bereitet die Ergebnisse für eine schnelle Entscheidung über Aufräumaktionen auf. Ziel ist eine klare, leicht verständliche Sicht auf genutzten und freien Speicher, ohne dass Einrichtung oder Betrieb überfuld oder kompliziert sein muss.

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

Das Projekt ist aktuell als Starter/Platzhalter gedacht. In diesem Repo-Stand sind Funktionsumfang, Plattformunterstützung und Konfigurationsoptionen noch nicht aus Implementierung ableitbar; die folgenden Begrenzungen gelten deshalb vorläufig:

- Es wird kein GUI-/Web-Dashboard bereitgestellt.
- Es ist keine dauerhafte Überwachung/Alerting-Komponente enthalten.
- Es wird keine cloud-spezifische Anbindung (z. B. Objektspeicher, virtuelle Laufwerke) nativ unterstützt.
- Es werden keine automatischen Lösch- oder Verschiebeaktionen durchgeführt; es handelt sich um Analyse/Sichtung, nicht um Aufräumbot.
- Lokale Dateisysteme stehen im Vordergrund; Netzwerk-Shares und Container-Overlay-Dateisysteme werden ggf. nicht vollständig abgedeckt.

## Schnellstart

Voraussetzungen: Python 3.11+ / Node 18+ (abhängig vom später gewählten Stack — siehe geplante milestone im Repo).

```bash
git clone https://github.com/Goitonthefloor/Disk-Space-Scanner.git
cd Disk-Space-Scanner
# Hinweis: aktuell nur README vorhanden; Implementierung folgt.
```

Wenn du CLI-Nutzung erwartest, ziele später auf:

```bash
# geplant
dss scan /pfad/zum/ordner --min-size 100MB --top 20
```

## Beitrag

Contributions sind willkommen. Bitte prüfe Issues/Discussions, bevor du einen größeren Feature-Branch öffnest. Forks, PRs und Fehlerberichte sind ausdrücklich erwünscht; beachte vor allem README/Scope Anpassungen, damit Doku und Implementierung synchron bleiben.
