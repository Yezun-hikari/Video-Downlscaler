# Video Compressor Tool

Ein einfaches, plattformübergreifendes Tool zum Komprimieren von Videos auf eine bestimmte Dateigröße bei bestmöglicher Qualität.

## Funktionen

*   **Drag & Drop**: Ziehen Sie Videodateien einfach in das Fenster.
*   **Zielgröße wählen**: Geben Sie die gewünschte Dateigröße in MB an.
*   **Automatische Optimierung**: Das Tool berechnet die optimale Bitrate und skaliert das Video bei Bedarf herunter, um die Qualität zu erhalten.
*   **Multi-Plattform**: Verfügbar für Windows, macOS und Linux.

## Installation und Nutzung

### Vorkompilierte Versionen

Laden Sie die neueste Version für Ihr Betriebssystem von der [Releases-Seite](../../releases) herunter.

1.  Entpacken Sie das ZIP-Archiv.
2.  Starten Sie `VideoCompressor` (bzw. `.exe` oder `.app`).

### Aus Quellcode ausführen

Voraussetzungen:
*   Python 3.9 oder höher
*   Empfohlen: Virtuelle Umgebung (venv)

1.  Repository klonen:
    ```bash
    git clone <repo-url>
    cd <repo-folder>
    ```

2.  Abhängigkeiten installieren:
    ```bash
    pip install -r requirements.txt
    ```

3.  Starten:
    ```bash
    python src/main.py
    ```

## Entwicklung & Build

Der Build-Prozess wird über GitHub Actions automatisiert. Um die Anwendung lokal zu bauen:

1.  Installieren Sie PyInstaller:
    ```bash
    pip install pyinstaller
    ```

2.  Führen Sie den Build-Befehl aus (angepasst an Ihr OS, siehe `.github/workflows/build.yml` für Details):
    ```bash
    pyinstaller --name="VideoCompressor" --windowed --onefile --collect-all imageio_ffmpeg src/main.py
    ```

3.  Die ausführbare Datei befindet sich im `dist/` Ordner.

## Lizenz

MIT
