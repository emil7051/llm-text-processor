"""File format converters for the text processor."""

from textcleaner.converters.base import ConverterRegistry, BaseConverter
from textcleaner.converters.pdf_converter import PDFConverter
from textcleaner.converters.office_converter import OfficeConverter
from textcleaner.converters.html_converter import HTMLConverter
from textcleaner.converters.text_converter import TextConverter
from textcleaner.converters.markdown_converter import MarkdownConverter

# Supported file types constants
PDF_EXTENSIONS = ['.pdf']
OFFICE_EXTENSIONS = ['.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt']
HTML_EXTENSIONS = ['.html', '.htm', '.xml']
TEXT_EXTENSIONS = ['.txt', '.log', '.csv', '.json']
MARKDOWN_EXTENSIONS = ['.md', '.markdown']

# All supported extensions
ALL_SUPPORTED_EXTENSIONS = (
    PDF_EXTENSIONS + 
    OFFICE_EXTENSIONS + 
    HTML_EXTENSIONS + 
    TEXT_EXTENSIONS + 
    MARKDOWN_EXTENSIONS
)

def register_converters():
    """Register all available converters with the registry.
    
    Returns:
        Configured converter registry with all available converters registered.
    """
    registry = ConverterRegistry()
    
    # Register the PDF converter
    registry.register(PDFConverter())
    
    # Register the Office document converter
    registry.register(OfficeConverter())
    
    # Register the HTML/XML converter
    registry.register(HTMLConverter())
    
    # Register the plain text converter
    registry.register(TextConverter())
    
    # Register the markdown converter
    registry.register(MarkdownConverter())
    
    return registry
