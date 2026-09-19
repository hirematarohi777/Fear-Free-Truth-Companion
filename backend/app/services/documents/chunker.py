from typing import List, Dict, Any
from app.services.documents.extractor import ExtractedUnit


class DocumentChunk:
    def __init__(self, chunk_index: int, text: str, source_references: str, extraction_method: str, warnings: List[str] = None):
        self.chunk_index = chunk_index
        self.text = text
        self.source_references = source_references
        self.extraction_method = extraction_method
        self.warnings = warnings or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunkIndex": self.chunk_index,
            "text": self.text,
            "sourceReferences": self.source_references,
            "extractionMethod": self.extraction_method,
            "extractionWarnings": self.warnings
        }


def chunk_extracted_units(units: List[ExtractedUnit], max_chars_per_chunk: int = 2500, overlap_chars: int = 400) -> List[DocumentChunk]:
    """
    Combine extracted units into structured, overlapping chunks with stable source IDs.
    """
    if not units:
        return []

    chunks: List[DocumentChunk] = []
    current_text_parts: List[str] = []
    current_refs: List[str] = []
    current_char_count = 0
    chunk_idx = 0
    methods_used = set()
    warnings = []

    for u in units:
        methods_used.add("OCR" if u.is_ocr else "DirectText")
        if u.warning:
            warnings.append(u.warning)

        unit_str = f"[{u.source_ref}]\n{u.text}\n"
        unit_len = len(unit_str)

        if current_char_count + unit_len > max_chars_per_chunk and current_text_parts:
            # Create a chunk
            chunk_text = "\n".join(current_text_parts)
            ref_summary = ", ".join(dict.fromkeys(current_refs))
            method_str = " + ".join(sorted(methods_used))
            chunks.append(DocumentChunk(
                chunk_index=chunk_idx,
                text=chunk_text,
                source_references=ref_summary,
                extraction_method=method_str,
                warnings=list(dict.fromkeys(warnings))
            ))
            chunk_idx += 1

            # Keep overlap: take the last part if feasible
            overlap_part = current_text_parts[-1] if len(current_text_parts[-1]) <= overlap_chars else current_text_parts[-1][-overlap_chars:]
            current_text_parts = [overlap_part, unit_str]
            current_refs = [current_refs[-1], u.source_ref] if current_refs else [u.source_ref]
            current_char_count = len(overlap_part) + unit_len
        else:
            current_text_parts.append(unit_str)
            current_refs.append(u.source_ref)
            current_char_count += unit_len

    if current_text_parts:
        chunk_text = "\n".join(current_text_parts)
        ref_summary = ", ".join(dict.fromkeys(current_refs))
        method_str = " + ".join(sorted(methods_used)) if methods_used else "DirectText"
        chunks.append(DocumentChunk(
            chunk_index=chunk_idx,
            text=chunk_text,
            source_references=ref_summary,
            extraction_method=method_str,
            warnings=list(dict.fromkeys(warnings))
        ))

    return chunks
