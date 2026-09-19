import io
import os
import re
from typing import List, Dict, Any, Tuple
import pdfplumber
import docx
from PIL import Image
import pytesseract
from app.core.logging_config import logger
from app.schemas.analyses import EvidenceQuality


class ExtractedUnit:
    def __init__(self, source_ref: str, text: str, is_ocr: bool = False, warning: str = None):
        self.source_ref = source_ref
        self.text = text.strip()
        self.is_ocr = is_ocr
        self.warning = warning

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sourceRef": self.source_ref,
            "text": self.text,
            "isOcr": self.is_ocr,
            "warning": self.warning
        }


def extract_from_pdf(file_path: str) -> Tuple[List[ExtractedUnit], EvidenceQuality, List[str]]:
    """Extract text page-by-page from PDF, falling back to OCR if page content is purely image-based."""
    units: List[ExtractedUnit] = []
    warnings: List[str] = []
    ocr_pages_count = 0
    total_pages = 0

    try:
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            for idx, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                page_text = page_text.strip()
                ref = f"Page {idx}"

                # If text is virtually empty, try OCR
                if len(page_text) < 40:
                    try:
                        # Render page image
                        img = page.to_image(resolution=200).original
                        ocr_text = pytesseract.image_to_string(img)
                        if len(ocr_text.strip()) > 30:
                            units.append(ExtractedUnit(
                                source_ref=ref,
                                text=ocr_text.strip(),
                                is_ocr=True,
                                warning="Text extracted via Optical Character Recognition (OCR)."
                            ))
                            ocr_pages_count += 1
                        else:
                            units.append(ExtractedUnit(
                                source_ref=ref,
                                text=page_text,
                                is_ocr=False,
                                warning="Page appears to contain low-resolution images or unreadable scans."
                            ))
                            warnings.append(f"{ref} has unreadable or low-contrast scan content.")
                    except Exception as ocr_err:
                        units.append(ExtractedUnit(
                            source_ref=ref,
                            text=page_text,
                            is_ocr=False,
                            warning="OCR conversion was unavailable or failed on this page."
                        ))
                        warnings.append(f"{ref} could not be OCR processed: {str(ocr_err)}")
                else:
                    units.append(ExtractedUnit(source_ref=ref, text=page_text, is_ocr=False))
    except Exception as e:
        logger.error(f"Error reading PDF {file_path}: {e}")
        warnings.append(f"PDF extraction error: {str(e)}")

    if total_pages == 0 or not any(u.text for u in units):
        return units, EvidenceQuality.INSUFFICIENT, warnings + ["No readable text could be extracted from document."]

    if ocr_pages_count > 0 or warnings:
        quality = EvidenceQuality.PARTIAL
    else:
        quality = EvidenceQuality.CLEAR

    return units, quality, warnings


def extract_from_docx(file_path: str) -> Tuple[List[ExtractedUnit], EvidenceQuality, List[str]]:
    """
    Extract text from DOCX using paragraph and table references.
    Does NOT invent page numbers!
    """
    units: List[ExtractedUnit] = []
    warnings: List[str] = []

    try:
        doc = docx.Document(file_path)
        p_index = 1
        current_section = "General Terms"

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            # Detect heading-like paragraphs to track sections
            if p.style.name.startswith("Heading") or (len(text) < 60 and text.isupper()):
                current_section = text
                ref = f"Section '{current_section}', Paragraph {p_index}"
            else:
                ref = f"Section '{current_section}', Paragraph {p_index}"

            units.append(ExtractedUnit(source_ref=ref, text=text, is_ocr=False))
            p_index += 1

        # Extract tables
        for t_idx, table in enumerate(doc.tables, start=1):
            table_rows = []
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells]
                table_rows.append(" | ".join(row_cells))
            t_text = "\n".join(table_rows).strip()
            if t_text:
                units.append(ExtractedUnit(
                    source_ref=f"Table {t_idx}",
                    text=t_text,
                    is_ocr=False
                ))

    except Exception as e:
        logger.error(f"Error reading DOCX {file_path}: {e}")
        warnings.append(f"DOCX extraction error: {str(e)}")

    if not any(u.text for u in units):
        return units, EvidenceQuality.INSUFFICIENT, warnings + ["No readable text found in DOCX paragraphs or tables."]

    return units, EvidenceQuality.CLEAR, warnings


def extract_from_image(file_path: str) -> Tuple[List[ExtractedUnit], EvidenceQuality, List[str]]:
    """Extract text from standalone JPG/PNG using Tesseract OCR."""
    units: List[ExtractedUnit] = []
    warnings: List[str] = []

    try:
        image = Image.open(file_path)
        # Limit image size to avoid decompression bombs
        image.thumbnail((3000, 3000))
        text = pytesseract.image_to_string(image).strip()
        ref = "Image Document (OCR)"
        
        if len(text) < 40:
            units.append(ExtractedUnit(source_ref=ref, text=text, is_ocr=True, warning="Low OCR text yield."))
            warnings.append("Image resolution or contrast resulted in very low character recognition yield.")
            return units, EvidenceQuality.INSUFFICIENT, warnings
        
        units.append(ExtractedUnit(source_ref=ref, text=text, is_ocr=True))
        return units, EvidenceQuality.PARTIAL, warnings
    except Exception as e:
        logger.error(f"OCR failure on {file_path}: {e}")
        warnings.append(f"Image OCR failed: {str(e)}")
        return units, EvidenceQuality.INSUFFICIENT, warnings


def extract_document_units(file_path: str, mime_type: str) -> Tuple[List[ExtractedUnit], EvidenceQuality, List[str]]:
    """Dispatch file extraction based on detected MIME type."""
    if mime_type == "application/pdf":
        return extract_from_pdf(file_path)
    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_from_docx(file_path)
    elif mime_type in ("image/png", "image/jpeg"):
        return extract_from_image(file_path)
    else:
        return [], EvidenceQuality.INSUFFICIENT, [f"Unsupported mime type: {mime_type}"]
