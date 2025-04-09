"""Replacement dictionaries for text simplification."""

from typing import Dict, List, Tuple, Optional, Set
import re
import os
import json
from pathlib import Path
import logging

# Common verbose phrases and their simpler alternatives
COMMON_PHRASES = {
    # Transitional phrases
    "in order to": "to",
    "for the purpose of": "for",
    "in the event that": "if",
    "in the case that": "if",
    "due to the fact that": "because",
    "in spite of the fact that": "although",
    "with regard to": "about",
    "with reference to": "about",
    "in relation to": "about",
    "in connection with": "about",
    "concerning the matter of": "about",
    "in the vicinity of": "near",
    "for the reason that": "because",
    "as a consequence of": "because",
    "on the occasion of": "when",
    "in the near future": "soon",
    "at this point in time": "now",
    "at the present time": "now",
    "it is often the case that": "often",
    "it is important to note that": "",  # Often completely removable
    "the reason why is that": "because",
    "despite the fact that": "although",
    "during the course of": "during",
    "until such time as": "until",
    "along the lines of": "like",
    "a considerable amount of": "much",
    "a majority of": "most",
    "a number of": "many",
    "an adequate amount of": "enough",
    "an appreciable number of": "many",
    "a sufficient amount of": "enough",
    "a substantial amount of": "much",
    "a significant number of": "many",
    "based on the fact that": "because",
    "by means of": "by",
    "by virtue of": "by",
    "by way of": "by",
    "come to the conclusion that": "conclude",
    "give an indication of": "indicate",
    "give rise to": "cause",
    "has the capability to": "can",
    "has the capacity to": "can",
    "has the potential to": "can",
    "have the ability to": "can",
    "in a situation in which": "when",
    "in close proximity to": "near",
    "in lieu of": "instead of",
    "in the absence of": "without",
    "in the neighborhood of": "about",
    "it is clear that": "",  # Often completely removable
    "it is evident that": "",  # Often completely removable
    "it is obvious that": "",  # Often completely removable
    "it should be noted that": "",  # Often completely removable
    "make reference to": "refer to",
    "on a regular basis": "regularly",
    "on account of": "because",
    "on behalf of": "for",
    "on the grounds that": "because",
    "on the part of": "by",
    "take into consideration": "consider",
    "take steps to": "act",
    "through the use of": "by",
    "with a view to": "to",
    "with the exception of": "except",
    
    # Common business/academic jargon
    "leverage": "use",
    "utilize": "use",
    "functionality": "features",
    "implementation": "use",
    "additionally": "also",
    "furthermore": "also",
    "consequently": "so",
    "subsequently": "later",
    "nevertheless": "still",
    "as a matter of fact": "in fact",
    "at the end of the day": "ultimately",
    "paradigm shift": "change",
    "synergy": "cooperation",
    "holistic approach": "complete approach",
    "strategic initiative": "plan",
    "core competency": "strength",
    "best practice": "method",
    "actionable insight": "useful information",
    "low-hanging fruit": "easy win",
    "touch base": "talk",
    "think outside the box": "be creative",
    "going forward": "in future",
    "circle back": "follow up",
}


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
            r'\b(approximately|roughly|around|about)\b': '~',
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
            
            # Numbers
            r'\b(thousand|one thousand)\b': '1K',
            r'\b(million|one million)\b': '1M',
            r'\b(billion|one billion)\b': '1B',
            r'\bone hundred\b': '100',
            r'\bone thousand\b': '1000',
            
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


class DomainTextOptimizer:
    """Optimizes text for specific domains using domain-specific terminology.
    
    This class provides domain-specific optimizations by replacing common
    domain terminology with more concise versions.
    """
    
    def __init__(self, domains: Optional[List[str]] = None):
        """Initialize the domain text optimizer.
        
        Args:
            domains: List of domain names to enable (legal, technical, etc.)
        """
        self.logger = logging.getLogger(__name__)
        self.domains = domains or []
        
        # Domain-specific replacement dictionaries
        self.domain_replacements: Dict[str, Dict[str, str]] = {
            'legal': {
                r'\b(plaintiff)\b': 'PL',
                r'\b(defendant)\b': 'DEF',
                r'\b(attorney)\b': 'ATTY',
                r'\b(judgment|judgement)\b': 'JDGMT',
                r'\b(in the matter of)\b': 're',
                r'\b(jurisdiction)\b': 'JDX',
                r'\b(settlement agreement)\b': 'SA',
                r'\b(memorandum of understanding)\b': 'MOU',
                r'\b(non-disclosure agreement)\b': 'NDA',
            },
            'technical': {
                r'\b(application programming interface)\b': 'API',
                r'\b(graphical user interface)\b': 'GUI',
                r'\b(operating system)\b': 'OS',
                r'\b(information technology)\b': 'IT',
                r'\b(artificial intelligence)\b': 'AI',
                r'\b(machine learning)\b': 'ML',
                r'\b(natural language processing)\b': 'NLP',
                r'\b(version control system)\b': 'VCS',
                r'\b(object-oriented programming)\b': 'OOP',
            },
            'academic': {
                r'\b(et alia|and others)\b': 'et al.',
                r'\b(ibid|ibidem)\b': 'ibid.',
                r'\b(exempli gratia|for example)\b': 'e.g.',
                r'\b(id est|that is)\b': 'i.e.',
                r'\b(nota bene)\b': 'N.B.',
                r'\b(post scriptum)\b': 'P.S.',
                r'\b(curriculum vitae)\b': 'CV',
                r'\b(circa|around|approximately)\b': 'c.',
                r'\b(conference proceedings)\b': 'Proc.',
            },
            'business': {
                r'\b(return on investment)\b': 'ROI',
                r'\b(key performance indicator)\b': 'KPI',
                r'\b(business-to-business)\b': 'B2B',
                r'\b(business-to-consumer)\b': 'B2C',
                r'\b(chief executive officer)\b': 'CEO',
                r'\b(chief financial officer)\b': 'CFO',
                r'\b(chief technology officer)\b': 'CTO',
                r'\b(with regards to)\b': 're:',
                r'\b(year-over-year)\b': 'YoY',
            },
            'medical': {
                r'\b(history of present illness)\b': 'HPI',
                r'\b(past medical history)\b': 'PMH',
                r'\b(review of systems)\b': 'ROS',
                r'\b(blood pressure)\b': 'BP',
                r'\b(heart rate)\b': 'HR',
                r'\b(respiratory rate)\b': 'RR',
                r'\b(emergency department)\b': 'ED',
                r'\b(intensive care unit)\b': 'ICU',
                r'\b(twice a day)\b': 'BID',
                r'\b(three times a day)\b': 'TID',
            },
        }
    
    def optimize(self, text: str) -> str:
        """Optimize text using domain-specific replacements.
        
        Args:
            text: Text to optimize
            
        Returns:
            Optimized text
        """
        if not text or not self.domains:
            return text
        
        optimized_text = text
        
        # Apply domain-specific replacements
        for domain in self.domains:
            if domain not in self.domain_replacements:
                self.logger.warning(f"Unknown domain: {domain}")
                continue
                
            for pattern, replacement in self.domain_replacements[domain].items():
                optimized_text = re.sub(pattern, replacement, optimized_text, flags=re.IGNORECASE)
        
        return optimized_text


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