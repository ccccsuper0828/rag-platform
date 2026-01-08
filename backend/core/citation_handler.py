"""
Citation Handler for RAG responses.
Provides citation formatting, parsing, and evidence extraction.
Inspired by Open Paper's citation system.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ResponseMode(str, Enum):
    CONCISE = "concise"
    NORMAL = "normal"
    DETAILED = "detailed"


@dataclass
class Citation:
    key: int
    reference: str
    page: Optional[int] = None
    position: Optional[Dict[str, float]] = None
    source_file: Optional[str] = None


@dataclass
class CitationResponse:
    content: str
    citations: List[Citation]
    mode: ResponseMode


class CitationHandler:
    """Handles citation formatting and parsing for RAG responses."""
    
    # System prompt for citation-aware responses
    CITATION_SYSTEM_PROMPT = """
You are a research assistant that provides precise, evidence-based answers. Your responses must always include specific text evidence from the documents.

Follow these strict formatting rules:
1. Structure your answer with numbered citations [^1], [^2], etc., where each number corresponds to a specific piece of evidence.
2. At the end of your response, include an evidence section with the following format:

---EVIDENCE---
@cite[1]
"First piece of evidence from the document"
@cite[2]
"Second piece of evidence from the document"
---END-EVIDENCE---

3. Each citation must:
   - Start with @cite[n] on its own line
   - Have the quoted text on the next line (exact text from the document)
   - Use sequential numbers starting from 1
   
4. Only cite actual text that appears in the provided documents.
5. If you're uncertain, indicate your uncertainty but still provide your best answer with evidence.
"""

    MODE_INSTRUCTIONS = {
        ResponseMode.CONCISE: """
You are in CONCISE mode. Provide brief, direct answers.
- Maximum 2-3 paragraphs
- Focus on the most critical evidence
- 2-4 citations maximum
""",
        ResponseMode.NORMAL: """
You are in NORMAL mode. Provide balanced responses.
- 3-5 paragraphs as needed
- Include key supporting evidence
- 3-6 citations as appropriate
""",
        ResponseMode.DETAILED: """
You are in DETAILED mode. Provide comprehensive, thorough analysis.
- Explore the topic in depth
- Include extensive supporting evidence
- Multiple citations to support each major point
- Consider different perspectives if present in documents
"""
    }

    @classmethod
    def get_system_prompt(cls, mode: ResponseMode = ResponseMode.NORMAL) -> str:
        """Get the full system prompt for a given response mode."""
        return cls.CITATION_SYSTEM_PROMPT + cls.MODE_INSTRUCTIONS.get(mode, cls.MODE_INSTRUCTIONS[ResponseMode.NORMAL])

    @classmethod
    def parse_response(cls, response_text: str) -> Tuple[str, List[Citation]]:
        """
        Parse a response to extract the main content and citations.
        
        Args:
            response_text: The full response text containing content and evidence block
            
        Returns:
            Tuple of (cleaned_content, list_of_citations)
        """
        citations = []
        
        # Find and extract the evidence block
        evidence_pattern = r'---EVIDENCE---\s*(.*?)\s*---END-EVIDENCE---'
        evidence_match = re.search(evidence_pattern, response_text, re.DOTALL)
        
        if evidence_match:
            evidence_block = evidence_match.group(1)
            # Remove evidence block from content
            content = response_text[:evidence_match.start()].strip()
            
            # Parse citations from evidence block
            citations = cls._parse_evidence_block(evidence_block)
        else:
            content = response_text.strip()
        
        return content, citations

    @classmethod
    def _parse_evidence_block(cls, evidence_text: str) -> List[Citation]:
        """
        Parse the evidence block into structured citations.
        
        Expected format:
        @cite[1]
        "First piece of evidence"
        @cite[2]
        "Second piece of evidence"
        """
        citations = []
        lines = evidence_text.strip().split('\n')
        current_citation = None
        current_text_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('@cite['):
                # Save previous citation if exists
                if current_citation is not None:
                    reference = ' '.join(current_text_lines).strip()
                    # Remove surrounding quotes if present
                    if reference.startswith('"') and reference.endswith('"'):
                        reference = reference[1:-1]
                    elif reference.startswith("'") and reference.endswith("'"):
                        reference = reference[1:-1]
                    
                    citations.append(Citation(
                        key=current_citation,
                        reference=reference
                    ))
                
                # Start new citation
                match = re.search(r'@cite\[(\d+)\]', line)
                if match:
                    current_citation = int(match.group(1))
                    current_text_lines = []
            elif current_citation is not None and line:
                current_text_lines.append(line)
        
        # Don't forget the last citation
        if current_citation is not None and current_text_lines:
            reference = ' '.join(current_text_lines).strip()
            if reference.startswith('"') and reference.endswith('"'):
                reference = reference[1:-1]
            elif reference.startswith("'") and reference.endswith("'"):
                reference = reference[1:-1]
            
            citations.append(Citation(
                key=current_citation,
                reference=reference
            ))
        
        return citations

    @classmethod
    def format_citations_for_display(cls, citations: List[Citation]) -> str:
        """Format citations for display in the UI."""
        if not citations:
            return ""
        
        formatted = "\n\n---\n**引用来源:**\n"
        for citation in citations:
            page_info = f" (p.{citation.page})" if citation.page else ""
            formatted += f"\n[^{citation.key}]: \"{citation.reference}\"{page_info}\n"
        
        return formatted

    @classmethod
    def find_citation_in_document(
        cls, 
        citation: Citation, 
        document_text: str,
        page_offset_map: Optional[Dict[int, Tuple[int, int]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find the position of a citation in the original document.
        
        Args:
            citation: The citation to find
            document_text: The full text of the document
            page_offset_map: Optional mapping of page numbers to character offsets
            
        Returns:
            Position info dict if found, None otherwise
        """
        reference = citation.reference
        
        # Try exact match first
        start_idx = document_text.find(reference)
        
        if start_idx == -1:
            # Try fuzzy match (first few words)
            words = reference.split()[:5]
            if words:
                search_pattern = r'\b' + r'\s+'.join(re.escape(w) for w in words)
                match = re.search(search_pattern, document_text, re.IGNORECASE)
                if match:
                    start_idx = match.start()
        
        if start_idx == -1:
            return None
        
        # Find page number if we have the offset map
        page_num = None
        if page_offset_map:
            for page, (page_start, page_end) in page_offset_map.items():
                if page_start <= start_idx < page_end:
                    page_num = page
                    break
        
        return {
            "start_offset": start_idx,
            "end_offset": start_idx + len(reference),
            "page": page_num,
            "position": {
                "x": 10,  # Default position, would need PDF coordinates for exact placement
                "y": 10,
                "width": 80,
                "height": 3
            }
        }

    @classmethod
    def enrich_citations_with_positions(
        cls,
        citations: List[Citation],
        document_text: str,
        page_offset_map: Optional[Dict[int, Tuple[int, int]]] = None
    ) -> List[Citation]:
        """
        Enrich citations with their positions in the document.
        """
        enriched = []
        for citation in citations:
            position_info = cls.find_citation_in_document(
                citation, document_text, page_offset_map
            )
            if position_info:
                citation.page = position_info.get("page")
                citation.position = position_info.get("position")
            enriched.append(citation)
        return enriched

    @classmethod
    def to_dict(cls, citation: Citation) -> Dict[str, Any]:
        """Convert Citation to dictionary for JSON serialization."""
        return {
            "key": citation.key,
            "reference": citation.reference,
            "page": citation.page,
            "position": citation.position,
            "source_file": citation.source_file
        }

    @classmethod
    def citations_to_json(cls, citations: List[Citation]) -> List[Dict[str, Any]]:
        """Convert list of Citations to JSON-serializable list."""
        return [cls.to_dict(c) for c in citations]

