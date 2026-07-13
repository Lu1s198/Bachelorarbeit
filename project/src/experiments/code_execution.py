"""Extraktion und Ausführung des vom LLM erzeugten Python-Codes.

Umsetzung des Code-Generierungs-Ansatzes (Kapitel 4.1): Das Modell erzeugt ein
ausführbares pandas-Skript, das anschließend deterministisch in einem separaten
Prozess ausgeführt wird. Der erzeugte Code ist ein nachvollziehbares,
wiederausführbares Artefakt.

Sicherheitshinweis: Hier wird von einem Modell erzeugter Code ausgeführt. Das
ist für die kontrollierte, lokale Durchführung dieser Arbeit vertretbar, sollte
aber niemals auf unkontrollierten Eingaben oder Produktivsystemen erfolgen. Die
Ausführung ist auf einen eigenen Prozess mit Timeout beschränkt.
"""

from __future__ import annotations

import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

_FENCE_RE = re.compile(r"```(?:python|py)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_code(text: str) -> str:
    """Extrahiert den Python-Code aus der Modellantwort.

    Bevorzugt einen Markdown-Codeblock; fällt sonst auf den gesamten Text zurück.
    """
    match = _FENCE_RE.search(text)
    return (match.group(1) if match else text).strip()


@dataclass
class ExecutionResult:
    success: bool             # Prozess ohne Fehler UND Ausgabedatei erzeugt
    return_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    output_exists: bool


def run_generated_code(
    code: str,
    script_path: Path,
    output_path: Path,
    timeout: int = 120,
) -> ExecutionResult:
    """Schreibt den Code, führt ihn aus und prüft, ob die Ausgabedatei entstand."""
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(code, encoding="utf-8")
    if output_path.exists():
        output_path.unlink()  # alte Ausgabe entfernen, damit output_exists valide ist

    start = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(script_path.parent),
        )
        return_code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        return_code, stdout, stderr = -1, exc.stdout or "", (exc.stderr or "") + "\n[TIMEOUT]"
    duration = time.perf_counter() - start

    output_exists = output_path.exists()
    return ExecutionResult(
        success=(return_code == 0 and output_exists),
        return_code=return_code,
        stdout=stdout[-4000:],
        stderr=stderr[-4000:],
        duration_seconds=duration,
        output_exists=output_exists,
    )
