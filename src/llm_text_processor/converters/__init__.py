"""File format converters for the text processor."""

from llm_text_processor.converters.base import ConverterRegistry
from llm_text_processor.converters.pdf_converter import PDFConverter
from llm_text_processor.converters.office_converter import OfficeConverter
from llm_text_processor.converters.html_converter import HTMLConverter

# Register the converters
def register_converters():
    """Register all available converters with the registry."""
    registry = ConverterRegistry()
    
    # Register the PDF converter
    registry.register(PDFConverter())
    
    # Register the Office document converter
    registry.register(OfficeConverter())
    
    # Register the HTML/XML converter
    registry.register(HTMLConverter())
    
    return registry
