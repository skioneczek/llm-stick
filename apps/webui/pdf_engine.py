# apps/webui/pdf_engine.py
from __future__ import annotations
import os, shutil, subprocess, tempfile
from typing import Optional, Tuple

ENGINE_ENV = os.getenv("PDF_ENGINE", "").strip().lower()  # "weasy" | "wkhtml" | ""
VENDOR_BIN = os.path.abspath(os.path.join(os.getcwd(), "vendor", "bin"))

def detect_pdf_engine() -> Tuple[Optional[str], str]:
    """
    Returns (engine, audit). engine in {"weasy", "wkhtml", None}
    Preference: env override -> weasyprint import -> wkhtmltopdf binary -> None
    """
    if ENGINE_ENV in {"weasy", "wkhtml"}:
        return ENGINE_ENV, f"PDF engine requested via env: {ENGINE_ENV}."
    try:
        import weasyprint  # type: ignore
        return "weasy", "PDF engine auto-selected: weasyprint."
    except Exception:
        pass
    wk = _which_wkhtml()
    if wk:
        return "wkhtml", f"PDF engine auto-selected: wkhtmltopdf ({wk})."
    return None, "PDF engine not available; falling back to browser Print to PDF."

def _which_wkhtml() -> Optional[str]:
    # search vendor/bin first, then PATH
    candidates = []
    exe = "wkhtmltopdf.exe" if os.name == "nt" else "wkhtmltopdf"
    vb = os.path.join(VENDOR_BIN, exe)
    if os.path.isfile(vb):
        candidates.append(vb)
    path_hit = shutil.which(exe)
    if path_hit:
        candidates.append(path_hit)
    return candidates[0] if candidates else None

def render_pdf_bytes(html: str) -> Tuple[Optional[bytes], str, str]:
    """
    Returns (pdf_bytes, audit_header, audit_detail).
    On success: (bytes, 'PDF export (engine weasyprint|wkhtml)', detail)
    On fallback: (None, 'PDF export fallback (engine missing)', detail)
    """
    engine, detect_audit = detect_pdf_engine()
    if engine == "weasy":
        try:
            from weasyprint import HTML  # type: ignore
            pdf = HTML(string=html, base_url="about:blank").write_pdf()
            return pdf, "PDF export (engine weasyprint)", detect_audit
        except Exception as e:
            return None, "PDF export fallback (engine error)", f"{detect_audit} weasyprint error: {e}"
    if engine == "wkhtml":
        wk = _which_wkhtml()
        if not wk:
            return None, "PDF export fallback (engine missing)", detect_audit
        with tempfile.TemporaryDirectory() as td:
            html_path = os.path.join(td, "in.html")
            pdf_path  = os.path.join(td, "out.pdf")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
            try:
                # --disable-external-links avoids accidental remote fetch attempts.
                cmd = [wk, "--quiet", "--disable-external-links", html_path, pdf_path]
                subprocess.run(cmd, check=True)
                with open(pdf_path, "rb") as f:
                    return f.read(), "PDF export (engine wkhtml)", detect_audit
            except Exception as e:
                return None, "PDF export fallback (engine error)", f"{detect_audit} wkhtmltopdf error: {e}"
    # fallback
    return None, "PDF export fallback (engine missing)", detect_audit
