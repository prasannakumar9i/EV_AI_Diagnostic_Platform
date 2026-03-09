"""
document_processing/pipeline.py
Full document processing pipeline: extract → clean → chunk → tag.
"""
import os
import re
import json
import unicodedata
import logging
from pathlib import Path
from typing import List, Dict, Optional
from collections import Counter

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 1. PDF TEXT EXTRACTOR
# ─────────────────────────────────────────────────────────────────────────────
class PDFExtractor:
    """
    Multi-strategy PDF extractor.
    Strategy order: pdfplumber → pypdf → pytesseract (OCR)
    """

    def extract(self, pdf_path: str) -> tuple[str, str]:
        """Returns (text, method_used)."""
        # Try pdfplumber
        try:
            import pdfplumber
            texts = []
            with pdfplumber.open(pdf_path) as pdf:
                for pg in pdf.pages:
                    t = pg.extract_text()
                    if t and len(t.strip()) > 30:
                        texts.append(t)
            if texts and sum(len(t) for t in texts) > 200:
                return "\n\n".join(texts), "pdfplumber"
        except Exception as e:
            logger.debug(f"pdfplumber failed: {e}")

        # Try pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            texts  = [p.extract_text() or "" for p in reader.pages]
            full   = "\n\n".join(texts)
            if len(full.strip()) > 100:
                return full, "pypdf"
        except Exception as e:
            logger.debug(f"pypdf failed: {e}")

        # Try OCR (pytesseract)
        try:
            from pdf2image import convert_from_path
            import pytesseract
            images = convert_from_path(pdf_path, dpi=200)
            texts  = [pytesseract.image_to_string(img) for img in images]
            full   = "\n\n".join(texts)
            if len(full.strip()) > 50:
                return full, "ocr"
        except Exception as e:
            logger.debug(f"OCR failed: {e}")

        return "", "failed"

    def extract_all(self, kb_path: str, out_path: str) -> List[dict]:
        """Extract text from all PDFs in knowledge base."""
        results = []
        os.makedirs(out_path, exist_ok=True)
        for pdf in Path(kb_path).rglob("*.pdf"):
            text, method = self.extract(str(pdf))
            if text:
                out_file = os.path.join(out_path, f"{pdf.stem}_raw.txt")
                with open(out_file, "w", encoding="utf-8", errors="ignore") as f:
                    f.write(text)
                results.append({
                    "source": str(pdf),
                    "output": out_file,
                    "method": method,
                    "chars":  len(text),
                })
                logger.info(f"[{method}] {pdf.name} ({len(text):,} chars)")
            else:
                logger.warning(f"[FAILED] {pdf.name}")
        return results


# ─────────────────────────────────────────────────────────────────────────────
# 2. TEXT CLEANER
# ─────────────────────────────────────────────────────────────────────────────
class TextCleaner:
    """Clean raw extracted text from EV manuals."""

    UNICODE_REPLACEMENTS = [
        ('\u2018', "'"), ('\u2019', "'"), ('\u201c', '"'), ('\u201d', '"'),
        ('\u2013', '-'), ('\u2014', '--'), ('\u00a0', ' '), ('\u00ad', ''),
        ('\u2022', '-'), ('\u2026', '...'),
    ]

    def clean(self, text: str) -> str:
        text = unicodedata.normalize("NFC", text)
        for old, new in self.UNICODE_REPLACEMENTS:
            text = text.replace(old, new)
        text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)           # fix hyphenation
        text = re.sub(r'^\s*\d{1,4}\s*$', '', text, flags=re.MULTILINE)  # remove page numbers
        text = re.sub(r'^(chapter|section|page)\s*\d+\s*$', '',  # remove headers
                      text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[^\x20-\x7E\n]', ' ', text)              # remove non-printable
        text = re.sub(r'\s+\.', '.', text)
        return text.strip()

    def clean_directory(self, in_dir: str, out_dir: str) -> List[dict]:
        os.makedirs(out_dir, exist_ok=True)
        results = []
        for fname in sorted(os.listdir(in_dir)):
            if not fname.endswith("_raw.txt"):
                continue
            in_path  = os.path.join(in_dir,  fname)
            out_path = os.path.join(out_dir, fname.replace("_raw.txt", "_clean.txt"))
            with open(in_path, encoding="utf-8", errors="ignore") as f:
                raw = f.read()
            clean = self.clean(raw)
            with open(out_path, "w") as f:
                f.write(clean)
            pct = (1 - len(clean) / max(1, len(raw))) * 100
            results.append({"file": fname, "before": len(raw),
                            "after": len(clean), "reduction_pct": round(pct, 1)})
            logger.info(f"{fname}: {len(raw):,} → {len(clean):,} ({pct:.1f}% reduced)")
        return results


# ─────────────────────────────────────────────────────────────────────────────
# 3. CHUNKER
# ─────────────────────────────────────────────────────────────────────────────
class DocumentChunker:
    """Split cleaned text into overlapping chunks for embedding."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self.chunk_size    = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split(self, text: str) -> List[str]:
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            splitter = RecursiveCharacterTextSplitter(
                chunk_size    = self.chunk_size,
                chunk_overlap = self.chunk_overlap,
                separators    = ["\n\n\n", "\n\n", "\n", ". ", " ", ""],
            )
            return splitter.split_text(text)
        except ImportError:
            # Fallback: simple sliding window
            chunks, start = [], 0
            while start < len(text):
                end = start + self.chunk_size
                chunks.append(text[start:end])
                start += self.chunk_size - self.chunk_overlap
            return chunks

    def chunk_text(self, text: str, doc_id: str) -> List[dict]:
        raw    = self._split(text)
        chunks = []
        for i, chunk in enumerate(raw):
            chunk = chunk.strip()
            if len(chunk) < 50:
                continue
            chunks.append({
                "chunk_id":    f"{doc_id}_c{i:04d}",
                "text":        chunk,
                "doc_id":      doc_id,
                "char_count":  len(chunk),
                "chunk_index": i,
            })
        return chunks

    def chunk_directory(self, in_dir: str) -> List[dict]:
        all_chunks = []
        for fname in sorted(os.listdir(in_dir)):
            if not fname.endswith("_clean.txt"):
                continue
            doc_id = fname.replace("_clean.txt", "")
            with open(os.path.join(in_dir, fname)) as f:
                text = f.read()
            chunks = self.chunk_text(text, doc_id)
            all_chunks.extend(chunks)
            logger.info(f"{fname}: {len(chunks)} chunks")
        return all_chunks


# ─────────────────────────────────────────────────────────────────────────────
# 4. AUTO TAGGER
# ─────────────────────────────────────────────────────────────────────────────
class AutoTagger:
    """Auto-tag chunks with brand, system, document type, and year."""

    BRAND_KW = {
        "tesla":     ["tesla", "model 3", "model s", "model x", "model y"],
        "nissan":    ["nissan", "leaf", "ariya"],
        "hyundai":   ["hyundai", "ioniq", "kona ev"],
        "bmw":       ["bmw", "i3", "i4", "ix3"],
        "kia":       ["kia", "ev6", "ev9"],
        "volkswagen":["volkswagen", "vw", "id.4", "id.3"],
        "ather":     ["ather", "450x", "rizta"],
        "ola":       ["ola", "s1 pro", "s1 air"],
        "tata":      ["tata", "nexon", "tiago ev"],
        "nrel":      ["nrel", "national renewable"],
        "doe":       ["department of energy", "doe", "afdc"],
        "iea":       ["iea", "international energy agency"],
    }

    SYSTEM_KW = {
        "battery":  ["battery", "bms", "cell voltage", "soc", "soh",
                     "lithium", "overvoltage", "capacity", "kalman"],
        "motor":    ["motor", "inverter", "torque", "rpm", "stator",
                     "rotor", "magnets", "winding"],
        "charging": ["charging", "charger", "ccs", "dc fast", "ac charge",
                     "chademo", "plug", "connector", "kwh"],
        "brakes":   ["brake", "abs", "regen", "caliper", "brake fluid",
                     "regenerative"],
        "hvac":     ["hvac", "climate", "air conditioning", "heater",
                     "coolant", "thermal management"],
        "safety":   ["high voltage", "hv system", "orange cable",
                     "service disconnect", "warning", "ppe"],
        "software": ["firmware", "ota", "software update", "ecu", "adas",
                     "autopilot", "can bus"],
    }

    DOCTYPE_KW = {
        "owner_manual":   ["owner's manual", "user manual", "owner manual"],
        "service_manual": ["service manual", "workshop manual", "repair guide"],
        "dtc_database":   ["fault code", "dtc", "diagnostic trouble code"],
        "research":       ["research", "study", "analysis", "report", "journal"],
        "standard":       ["standard", "iec", "sae", "iso", "regulation"],
    }

    def tag(self, chunk: dict) -> dict:
        t = chunk["text"].lower()
        brand = next(
            (b for b, kws in self.BRAND_KW.items() if any(k in t for k in kws)),
            "general"
        )
        system = max(self.SYSTEM_KW,
                     key=lambda s: sum(t.count(k) for k in self.SYSTEM_KW[s]))
        doc_type = next(
            (d for d, kws in self.DOCTYPE_KW.items() if any(k in t for k in kws)),
            "general"
        )
        years  = re.findall(r'\b(20[12][0-9])\b', chunk["text"])
        year   = int(Counter(years).most_common(1)[0][0]) if years else None
        return {**chunk, "brand": brand, "system": system,
                "doc_type": doc_type, "year": year}

    def tag_all(self, chunks: List[dict]) -> List[dict]:
        tagged = [self.tag(c) for c in chunks]
        brand_c  = Counter(c["brand"]  for c in tagged)
        system_c = Counter(c["system"] for c in tagged)
        logger.info(f"Tagged {len(tagged)} chunks | brands={dict(brand_c)} | systems={dict(system_c)}")
        return tagged


# ─────────────────────────────────────────────────────────────────────────────
# CONVENIENCE: run the full pipeline
# ─────────────────────────────────────────────────────────────────────────────
def run_full_pipeline(
    kb_path:  str,
    out_path: str,
) -> List[dict]:
    """Extract → Clean → Chunk → Tag all documents."""
    raw_dir   = os.path.join(out_path, "raw_text")
    clean_dir = os.path.join(out_path, "clean_text")

    extractor = PDFExtractor()
    cleaner   = TextCleaner()
    chunker   = DocumentChunker()
    tagger    = AutoTagger()

    logger.info("Step 1: Extracting PDFs...")
    extractor.extract_all(kb_path, raw_dir)

    logger.info("Step 2: Cleaning text...")
    cleaner.clean_directory(raw_dir, clean_dir)

    logger.info("Step 3: Chunking...")
    chunks = chunker.chunk_directory(clean_dir)

    logger.info("Step 4: Tagging...")
    tagged = tagger.tag_all(chunks)

    chunks_file = os.path.join(out_path, "all_chunks.json")
    with open(chunks_file, "w") as f:
        json.dump(tagged, f, indent=2)
    logger.info(f"Saved {len(tagged)} chunks → {chunks_file}")
    return tagged


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    base = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ev_platform"
    chunks = run_full_pipeline(
        kb_path  = os.path.join(base, "ev_knowledge_base"),
        out_path = os.path.join(base, "outputs"),
    )
    print(f"Pipeline complete: {len(chunks)} chunks ready")
