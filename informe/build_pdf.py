"""Arma informe/Informe_E1_Vallehondo_V1.pdf desde informe/informe.html (requiere Google Chrome).

Uso: python informe/build_pdf.py   (después de python run.py, que genera las figuras)
"""
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ACTA_DOCX = AQUI / "acta_reunion.docx"
HTML = AQUI / "informe.html"
TMP = AQUI / "_informe_render.html"
PDF = AQUI / "Informe_E1_Vallehondo_V1.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def acta_html() -> str:
    """Convierte el acta .docx a HTML (textutil de macOS) y deja solo el cuerpo."""
    out = subprocess.run(["textutil", "-convert", "html", "-stdout", str(ACTA_DOCX)],
                         capture_output=True, text=True, check=True).stdout
    return re.search(r"<body>(.*)</body>", out, re.S).group(1)


def main():
    html = HTML.read_text(encoding="utf-8").replace("{{ACTA}}", acta_html())
    TMP.write_text(html, encoding="utf-8")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={PDF}", TMP.as_uri()], check=True, capture_output=True)
    TMP.unlink()
    print(f"PDF generado: {PDF}")


if __name__ == "__main__":
    sys.exit(main())
