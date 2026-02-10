"""
Law Comparison Service
Utilities for detecting law sections and providing comparisons between old and new criminal codes
"""

import re
import json
import os
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# Regex patterns for detecting law sections
PATTERNS = {
    'IPC': [
        r'\bIPC\s+(?:Section\s+)?(\d+[A-Z]?)\b',
        r'\bSection\s+(\d+[A-Z]?)\s+(?:of\s+)?(?:the\s+)?IPC\b',
        r'\b(\d+[A-Z]?)\s+IPC\b',
        r'\bIndian\s+Penal\s+Code\s+(?:Section\s+)?(\d+[A-Z]?)\b'
    ],
    'CRPC': [
        r'\bCrPC\s+(?:Section\s+)?(\d+[A-Z]?)\b',
        r'\bSection\s+(\d+[A-Z]?)\s+(?:of\s+)?(?:the\s+)?CrPC\b',
        r'\b(\d+[A-Z]?)\s+CrPC\b',
        r'\bCriminal\s+Procedure\s+Code\s+(?:Section\s+)?(\d+[A-Z]?)\b',
        r'\bCode\s+of\s+Criminal\s+Procedure\s+(?:Section\s+)?(\d+[A-Z]?)\b'
    ],
    'IEA': [
        r'\bIEA\s+(?:Section\s+)?(\d+[A-Z]?)\b',
        r'\bSection\s+(\d+[A-Z]?)\s+(?:of\s+)?(?:the\s+)?IEA\b',
        r'\b(\d+[A-Z]?)\s+IEA\b',
        r'\bIndian\s+Evidence\s+Act\s+(?:Section\s+)?(\d+[A-Z]?)\b',
        r'\bEvidence\s+Act\s+(?:Section\s+)?(\d+[A-Z]?)\b'
    ]
}

# Law type mappings
LAW_MAPPING = {
    'IPC': 'IPC_TO_BNS',
    'CRPC': 'CRPC_TO_BNSS',
    'IEA': 'IEA_TO_BEA'
}

NEW_LAW_NAMES = {
    'IPC': 'BNS',
    'CRPC': 'BNSS',
    'IEA': 'BEA'
}

LAW_FULL_NAMES = {
    'IPC': 'Indian Penal Code',
    'CRPC': 'Code of Criminal Procedure',
    'IEA': 'Indian Evidence Act',
    'BNS': 'Bharatiya Nyaya Sanhita',
    'BNSS': 'Bharatiya Nagarik Suraksha Sanhita',
    'BEA': 'Bharatiya Sakshya Adhiniyam'
}


class LawComparisonService:
    """Service for law section detection and comparison"""
    
    def __init__(self, mapping_file_path: Optional[str] = None):
        """
        Initialize the service with law mapping data
        
        Args:
            mapping_file_path: Path to law_mapping_data.json file
        """
        if mapping_file_path is None:
            # Default to the file in the same directory
            current_dir = Path(__file__).parent
            mapping_file_path = current_dir / 'law_mapping_data.json'
        
        self.mapping_data = self._load_mapping_data(mapping_file_path)
    
    def _load_mapping_data(self, file_path: Path) -> Dict:
        """Load law mapping data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Mapping file not found at {file_path}")
            return {"IPC_TO_BNS": {}, "CRPC_TO_BNSS": {}, "IEA_TO_BEA": {}}
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {file_path}: {e}")
            return {"IPC_TO_BNS": {}, "CRPC_TO_BNSS": {}, "IEA_TO_BEA": {}}
    
    def detect_law_sections(self, text: str) -> List[Dict[str, str]]:
        """
        Detect all law section references in the given text
        
        Args:
            text: Text to search for law sections
            
        Returns:
            List of dicts with 'law_type' and 'section' keys
        """
        detected_sections = []
        seen = set()  # To avoid duplicates
        
        for law_type, patterns in PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    section = match.group(1).upper()
                    key = f"{law_type}:{section}"
                    
                    if key not in seen:
                        seen.add(key)
                        detected_sections.append({
                            'law_type': law_type,
                            'section': section,
                            'original_text': match.group(0)
                        })
        
        return detected_sections
    
    def get_comparison_data(self, law_type: str, section: str) -> Optional[Dict]:
        """
        Get comparison data for a specific section
        
        Args:
            law_type: Type of law (IPC, CRPC, IEA)
            section: Section number (e.g., "302", "304A")
            
        Returns:
            Dictionary with comparison data or None if not found
        """
        mapping_key = LAW_MAPPING.get(law_type.upper())
        if not mapping_key:
            return None
        
        section_data = self.mapping_data.get(mapping_key, {}).get(section.upper())
        if not section_data:
            return None
        
        # Enrich with law names
        return {
            'old_law': law_type.upper(),
            'old_law_full_name': LAW_FULL_NAMES.get(law_type.upper(), law_type.upper()),
            'new_law': NEW_LAW_NAMES.get(law_type.upper()),
            'new_law_full_name': LAW_FULL_NAMES.get(NEW_LAW_NAMES.get(law_type.upper(), ''), ''),
            **section_data
        }
    
    def get_all_comparisons(self, detected_sections: List[Dict[str, str]]) -> List[Dict]:
        """
        Get comparison data for multiple detected sections
        
        Args:
            detected_sections: List of detected section dicts
            
        Returns:
            List of comparison data dicts
        """
        comparisons = []
        
        for section_info in detected_sections:
            comparison = self.get_comparison_data(
                section_info['law_type'],
                section_info['section']
            )
            if comparison:
                comparison['original_text'] = section_info.get('original_text', '')
                comparisons.append(comparison)
        
        return comparisons
    
    def format_comparison_text(self, comparison: Dict) -> str:
        """
        Format a single comparison as human-readable text
        
        Args:
            comparison: Comparison data dict
            
        Returns:
            Formatted string
        """
        old_law = comparison.get('old_law', '')
        old_section = comparison.get('old_section', '')
        old_title = comparison.get('old_title', '')
        new_law = comparison.get('new_law', '')
        new_section = comparison.get('new_section', '')
        new_title = comparison.get('new_title', '')
        changes = comparison.get('changes', 'No information available')
        
        if new_section == "OMITTED":
            return f"""
📋 **{old_law} Section {old_section}** - {old_title}
⚠️ **Status**: This section has been OMITTED in the new {new_law}
📝 **Changes**: {changes}
"""
        
        return f"""
📋 **{old_law} Section {old_section}** → **{new_law} Section {new_section}**
📖 Old: {old_title}
📖 New: {new_title}
📝 **Changes**: {changes}
"""
    
    def format_all_comparisons(self, comparisons: List[Dict]) -> str:
        """
        Format multiple comparisons as a single text block
        
        Args:
            comparisons: List of comparison data dicts
            
        Returns:
            Formatted string with all comparisons
        """
        if not comparisons:
            return ""
        
        header = "\n\n" + "="*60 + "\n"
        header += "⚖️ LAW COMPARISON: Old Codes vs New Codes (Effective July 1, 2024)\n"
        header += "="*60 + "\n"
        
        formatted = [header]
        for i, comp in enumerate(comparisons, 1):
            formatted.append(f"\n{i}. {self.format_comparison_text(comp)}")
        
        footer = "\n" + "="*60 + "\n"
        footer += "Note: The information above compares the old criminal codes with the new Bharatiya laws that replaced them on July 1, 2024.\n"
        footer += "="*60
        
        formatted.append(footer)
        return "\n".join(formatted)
    
    def augment_answer(self, original_answer: str, question: str = "") -> Tuple[str, List[Dict]]:
        """
        Augment an answer with law comparisons
        
        Args:
            original_answer: The original LLM answer
            question: The original question (optional)
            
        Returns:
            Tuple of (augmented_answer, list_of_comparisons)
        """
        # Detect sections in both question and answer
        all_text = question + " " + original_answer
        detected = self.detect_law_sections(all_text)
        
        if not detected:
            return original_answer, []
        
        # Get comparison data
        comparisons = self.get_all_comparisons(detected)
        
        if not comparisons:
            return original_answer, []
        
        # Format and append comparisons
        comparison_text = self.format_all_comparisons(comparisons)
        augmented = original_answer + comparison_text
        
        return augmented, comparisons


# Convenience functions for direct usage
_service_instance = None

def get_service() -> LawComparisonService:
    """Get singleton instance of LawComparisonService"""
    global _service_instance
    if _service_instance is None:
        _service_instance = LawComparisonService()
    return _service_instance


def detect_law_sections(text: str) -> List[Dict[str, str]]:
    """Detect law sections in text"""
    return get_service().detect_law_sections(text)


def get_comparison(law_type: str, section: str) -> Optional[Dict]:
    """Get comparison for a specific section"""
    return get_service().get_comparison_data(law_type, section)


def augment_with_comparisons(answer: str, question: str = "") -> Tuple[str, List[Dict]]:
    """Augment an answer with law comparisons"""
    return get_service().augment_answer(answer, question)
