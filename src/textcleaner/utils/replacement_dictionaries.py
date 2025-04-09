"""Replacement dictionaries for text simplification."""

from typing import Dict, List, Tuple, Optional
import re
import json
from pathlib import Path
import logging


class TextSimplifier:
    """Simplifies text using common abbreviations and replacements.
    
    This class provides text simplification by replacing common phrases
    with shorter versions to reduce token usage.
    """
    
    def __init__(self):
        """Initialize the text simplifier with common replacements."""
        self.logger = logging.getLogger(__name__)
        
        # Common replacements for general text
        self.replacements = {
            # Common phrases to abbreviate
            r'\b(for example|for instance)\b': 'e.g.',
            r'\b(that is|in other words)\b': 'i.e.',
            r'\b(and so on|and so forth|etcetera)\b': 'etc.',
            r'\b(in relation to|regarding|concerning|with respect to)\b': 're:',
            r'\b(versus|as opposed to)\b': 'vs.',
            r'\b(and others|et alii)\b': 'et al.',
            r'\b(in the year|anno domini)\b': 'AD',
            r'\b(before the common era|before christ)\b': 'BCE',
            
            # Time expressions
            r'\b(hours|hour)\b': 'hr',
            r'\b(minutes|minute)\b': 'min',
            r'\b(seconds|second)\b': 'sec',
            
            # Units
            r'\b(kilograms|kilogram)\b': 'kg',
            r'\b(grams|gram)\b': 'g',
            r'\b(milligrams|milligram)\b': 'mg',
            r'\b(kilometers|kilometer)\b': 'km',
            r'\b(meters|meter)\b': 'm',
            r'\b(centimeters|centimeter)\b': 'cm',
            r'\b(millimeters|millimeter)\b': 'mm',
            
            # Common titles
            r'\b(professor)\b': 'Prof.',
            r'\b(doctor|doctorate)\b': 'Dr.',
            r'\b(mister)\b': 'Mr.',
            r'\b(missus)\b': 'Mrs.',
            
            # Organizations
            r'\b(united nations)\b': 'UN',
            r'\b(united states of america)\b': 'USA',
            r'\b(united kingdom)\b': 'UK',
            r'\b(european union)\b': 'EU',
            r'\b(world health organization)\b': 'WHO',
        }
        
    def simplify(self, text: str) -> str:
        """Simplify text by applying common replacements.
        
        Args:
            text: Text to simplify
            
        Returns:
            Simplified text
        """
        if not text:
            return text
        
        simplified_text = text
        
        # Apply all replacements
        for pattern, replacement in self.replacements.items():
            simplified_text = re.sub(pattern, replacement, simplified_text, flags=re.IGNORECASE)
        
        return simplified_text


# Domain-specific abbreviations and replacements
DOMAIN_ABBREVIATIONS = {
    # Legal abbreviations
    "legal": {
        "pursuant to": "per", 
        "hereinafter": "later",
        "notwithstanding": "despite",
        "aforementioned": "mentioned",
        "in accordance with": "per",
        "without prejudice to": "without affecting",
        "for the avoidance of doubt": "",  # Often removable
        "including but not limited to": "including",
        "mutatis mutandis": "with necessary changes",
        "prima facie": "on first view",
        "inter alia": "among other things",
        "bona fide": "genuine",
        "status quo": "current state",
        "per se": "by itself",
        "de facto": "in fact",
        "de jure": "by law",
        "force majeure": "unforeseeable circumstances",
    },
    
    # Technical/Computer Science
    "technical": {
        "graphical user interface": "GUI",
        "command line interface": "CLI",
        "object-oriented programming": "OOP",
        "application programming interface": "API",
        "integrated development environment": "IDE",
        "artificial intelligence": "AI",
        "machine learning": "ML",
        "natural language processing": "NLP",
        "random access memory": "RAM",
        "hypertext markup language": "HTML",
        "cascading style sheets": "CSS",
        "JavaScript Object Notation": "JSON",
        "representational state transfer": "REST",
        "extensible markup language": "XML",
        "database management system": "DBMS",
        "operating system": "OS",
        "internet of things": "IoT",
        "information technology": "IT",
        "user experience": "UX",
        "user interface": "UI",
    },
    
    # Academic/Research
    "academic": {
        "in the literature": "in research",
        "to the best of our knowledge": "",  # Often removable
        "a growing body of literature": "research",
        "the literature suggests": "research suggests",
        "a plethora of studies": "many studies",
        "extant literature": "existing research",
        "previous studies have shown": "research shows",
        "a large number of studies": "many studies",
        "it is widely accepted that": "",  # Often removable
        "empirical evidence suggests": "evidence suggests",
        "it has been demonstrated that": "",  # Often removable
        "conceptual framework": "framework",
        "theoretical underpinnings": "theory",
        "meta-analysis": "review",
        "methodological approach": "method",
    },
    
    # Business/Corporate
    "business": {
        "return on investment": "ROI",
        "key performance indicator": "KPI",
        "standard operating procedure": "SOP",
        "customer relationship management": "CRM",
        "business-to-business": "B2B",
        "business-to-consumer": "B2C",
        "chief executive officer": "CEO",
        "chief financial officer": "CFO",
        "chief information officer": "CIO",
        "chief technology officer": "CTO",
        "chief operating officer": "COO",
        "human resources": "HR",
        "research and development": "R&D",
        "mergers and acquisitions": "M&A",
        "initial public offering": "IPO",
        "profit and loss": "P&L",
        "generally accepted accounting principles": "GAAP",
        "year over year": "YoY",
        "quarter over quarter": "QoQ",
    },
    
    # Medical/Healthcare
    "medical": {
        "electronic health record": "EHR",
        "electronic medical record": "EMR",
        "cardiovascular disease": "CVD",
        "myocardial infarction": "MI",
        "coronary artery disease": "CAD",
        "chronic obstructive pulmonary disease": "COPD",
        "diabetes mellitus": "DM",
        "blood pressure": "BP",
        "body mass index": "BMI",
        "randomized controlled trial": "RCT",
        "emergency department": "ED",
        "intensive care unit": "ICU",
        "quality of life": "QoL",
        "activities of daily living": "ADL",
        "over the counter": "OTC",
        "twice a day": "BID",
        "three times a day": "TID",
        "four times a day": "QID",
    }
}


class DomainTextOptimizer:
    """Optimizes text for specific domains using abbreviations and terminology."""
    
    def __init__(self, domains: List[str] = None, custom_dict: Dict[str, str] = None):
        """Initialize with selected domains and optional custom dictionary.
        
        Args:
            domains: List of domain names to use from the built-in dictionaries.
                Options include: 'legal', 'technical', 'academic', 'business', 'medical'.
            custom_dict: Optional custom dictionary of replacements.
        """
        self.replacements = {}
        
        # Add selected domain abbreviations
        if domains:
            for domain in domains:
                if domain in DOMAIN_ABBREVIATIONS:
                    self.replacements.update(DOMAIN_ABBREVIATIONS[domain])
                    
        # Add custom dictionary if provided
        if custom_dict:
            self.replacements.update(custom_dict)
            
        # Compile a regex for efficient matching
        self.compile_pattern()
    
    def compile_pattern(self):
        """Compile the regex pattern for matching replacements."""
        if not self.replacements:
            self.pattern = None
            return
            
        self.pattern = re.compile(
            r'\b(' + '|'.join(re.escape(k) for k in self.replacements.keys()) + r')\b',
            re.IGNORECASE
        )
    
    def optimize(self, text: str) -> str:
        """Replace domain-specific terms with abbreviations or simpler alternatives.
        
        Args:
            text: Text to optimize.
            
        Returns:
            Optimized text.
        """
        if not text or not self.pattern:
            return text
            
        def _replace(match):
            matched = match.group(0)
            replacement = self.replacements.get(matched.lower())
            
            # Preserve case pattern when possible
            if replacement and matched.islower():
                return replacement
            elif replacement and matched.isupper():
                return replacement.upper()
            elif replacement and matched[0].isupper():
                return replacement[0].upper() + replacement[1:] if len(replacement) > 1 else replacement.upper()
            return replacement or matched
            
        return self.pattern.sub(_replace, text)
        
    def add_domain(self, domain: str) -> None:
        """Add a specific domain's abbreviations to the replacements.
        
        Args:
            domain: Name of the domain to add.
        """
        if domain in DOMAIN_ABBREVIATIONS:
            self.replacements.update(DOMAIN_ABBREVIATIONS[domain])
            self.compile_pattern()
            
    def add_replacements(self, new_dict: Dict[str, str]) -> None:
        """Add new replacements to the dictionary.
        
        Args:
            new_dict: Dictionary of new replacements.
        """
        self.replacements.update(new_dict)
        self.compile_pattern()
        
    def save_to_file(self, file_path: str) -> None:
        """Save the replacement dictionary to a JSON file.
        
        Args:
            file_path: Path to save the dictionary to.
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.replacements, f, indent=2, sort_keys=True)
            
    @classmethod
    def load_from_file(cls, file_path: str) -> 'DomainTextOptimizer':
        """Load a replacement dictionary from a JSON file.
        
        Args:
            file_path: Path to load the dictionary from.
            
        Returns:
            New DomainTextOptimizer instance with loaded dictionary.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            custom_dict = json.load(f)
        return cls(domains=[], custom_dict=custom_dict) 