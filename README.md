# Bachelorarbeit DHBW

LaTeX-Vorlage für eine Bachelorarbeit an der Dualen Hochschule Baden-Württemberg.

## Projektstruktur

```
.
├── config/              # Konfigurationsdateien
│   ├── config.tex      # Hauptkonfiguration und Metadaten
│   └── header.tex      # Kopf- und Fußzeilenkonfiguration
├── resources/          # Ressourcen
│   ├── cover.tex       # Titelblatt
│   ├── declaration.tex # Urheberechts-Erklärung
│   └── acronyms.tex    # Abkürzungsverzeichnis
├── content/            # Inhalte
│   └── chapters.tex    # Kapitelstruktur
├── bibliography.bib    # Literaturverzeichnis
└── main.tex            # Hauptdatei
```

## Setup

### Voraussetzungen

- LaTeX-Installation (z.B. MiKTeX, TeXLive oder MacTeX)
- Biber für Bibliografie

### Build-Anleitung

```bash
pdflatex main.tex
biber main
pdflatex main.tex
pdflatex main.tex
```

Oder nutze einen LaTeX-Editor wie:
- TeXstudio
- Visual Studio Code mit LaTeX Workshop Extension
- Overleaf (online)

## Anpassung

1. **Metadaten anpassen** in `config/config.tex`:
   - Titel und Untertitel
   - Dein Name und Matrikelnummer
   - Betreuer und Unternehmen
   - Bearbeitungszeitraum

2. **Inhalte schreiben** in `content/chapters.tex`

3. **Quellen hinzufügen** in `bibliography.bib`

4. **Abkürzungen definieren** in `resources/acronyms.tex`

## Features

- ✅ DHBW-konforme Formatierung
- ✅ Automatisches Inhaltsverzeichnis
- ✅ Abbildungs- und Tabellenverzeichnis
- ✅ Abkürzungsverzeichnis
- ✅ Literaturverzeichnis mit Biber
- ✅ Professionelle Kopf- und Fußzeilen
- ✅ Code-Highlighting mit Listings
- ✅ Deutsche Sprache und Formatierung

## Tipps

- Verwende `\ac{API}` für Abkürzungen (z.B. erste Nutzung wird expandiert)
- Nutze `\todo{Aufgabe}` für Todos im Text
- Füge Bilder mit `\includegraphics[width=...]{pfad}` ein
- Verwende `\cite{Quelle}` für Zitate
