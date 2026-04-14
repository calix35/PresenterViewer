from __future__ import annotations
from typing import List
import fitz


class AnnotationExtractor:
    def __init__(self, doc: fitz.Document) -> None:
        self.doc = doc

    def get_pnotes_for_page(self, page_index: int) -> List[str]:
        if page_index < 0 or page_index >= len(self.doc):
            return []

        page = self.doc[page_index]
        results: List[str] = []

        annot = page.first_annot

        while annot:
            info = annot.info or {}        

            author = (info.get('title') or '').strip().lower()
            subject = (info.get('subject') or '').strip().lower()
            content = (info.get('content') or '').strip()

            if author == "presenter" and subject == "note":
                if content:
                    results.append(content)

            annot = annot.next

        return results