"""
Unit tests for the HTML converter
"""

import os
import tempfile
import unittest
from pathlib import Path

import pytest
from bs4 import BeautifulSoup, Comment

from textcleaner.converters.html_converter import HTMLConverter


@pytest.mark.unit
class TestHTMLConverter(unittest.TestCase):
    """Test suite for the HTML converter"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Create a simple HTML file for testing
        self.html_file = self.test_dir / "test.html"
        with open(self.html_file, "w") as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Test HTML Document</title>
    <meta name="description" content="A test HTML document for unit testing">
    <meta name="keywords" content="test, html, converter">
    <meta name="author" content="Test Author">
    <style>
        body { font-family: Arial, sans-serif; }
    </style>
    <script>
        console.log("This should be removed");
    </script>
</head>
<body>
    <header>
        <h1>Test HTML Document</h1>
        <nav>
            <ul>
                <li><a href="#">Home</a></li>
                <li><a href="#">About</a></li>
                <li><a href="#">Contact</a></li>
            </ul>
        </nav>
    </header>
    <main>
        <article>
            <h2>Article Title</h2>
            <p>This is a paragraph of text for testing the HTML converter.</p>
            <p>It includes <strong>formatting</strong> and <em>styling</em>.</p>
            
            <h3>Section 1</h3>
            <p>This is the content of section 1.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
                <li>Item 3</li>
            </ul>
            
            <h3>Section 2</h3>
            <p>This is the content of section 2.</p>
            <table>
                <tr>
                    <th>Header 1</th>
                    <th>Header 2</th>
                </tr>
                <tr>
                    <td>Cell 1</td>
                    <td>Cell 2</td>
                </tr>
                <tr>
                    <td>Cell 3</td>
                    <td>Cell 4</td>
                </tr>
            </table>
        </article>
    </main>
    <footer>
        <p>&copy; 2025 Test Company</p>
        <ul>
            <li><a href="#">Privacy Policy</a></li>
            <li><a href="#">Terms of Service</a></li>
        </ul>
    </footer>
    <!-- This is a comment that should be removed -->
</body>
</html>""")
        
        # Create an XML file for testing
        self.xml_file = self.test_dir / "test.xml"
        with open(self.xml_file, "w") as f:
            f.write("""<?xml version="1.0" encoding="UTF-8"?>
<root>
    <metadata>
        <title>Test XML Document</title>
        <author>Test Author</author>
        <date>2025-04-08</date>
    </metadata>
    <content>
        <section>
            <heading>Section 1</heading>
            <paragraph>This is the content of section 1.</paragraph>
            <list>
                <item>Item 1</item>
                <item>Item 2</item>
                <item>Item 3</item>
            </list>
        </section>
        <section>
            <heading>Section 2</heading>
            <paragraph>This is the content of section 2.</paragraph>
            <table>
                <row>
                    <cell>Header 1</cell>
                    <cell>Header 2</cell>
                </row>
                <row>
                    <cell>Cell 1</cell>
                    <cell>Cell 2</cell>
                </row>
            </table>
        </section>
    </content>
</root>""")
        
        # Initialize the converter
        self.converter = HTMLConverter()
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.temp_dir.cleanup()
    
    def test_can_handle_html(self):
        """Test that the converter can handle HTML files"""
        self.assertTrue(self.converter.can_handle(self.html_file))
        
        # Test with URL-like paths
        self.assertTrue(self.converter.can_handle("http://example.com/page.html"))
        self.assertTrue(self.converter.can_handle("https://example.com/page.htm"))
        
        # Test with non-HTML file
        txt_file = self.test_dir / "test.txt"
        txt_file.touch()
        self.assertFalse(self.converter.can_handle(txt_file))
    
    def test_can_handle_xml(self):
        """Test that the converter can handle XML files"""
        self.assertTrue(self.converter.can_handle(self.xml_file))
        
        # Test with URL-like paths
        self.assertTrue(self.converter.can_handle("http://example.com/data.xml"))
    
    def test_convert_html(self):
        """Test converting an HTML file"""
        content, metadata = self.converter.convert(self.html_file)
        
        # Check metadata
        self.assertEqual(metadata["title"], "Climate Change: The Scientific Consensus")
        self.assertEqual(metadata["description"], "An overview of the scientific consensus on climate change and its impacts")
        self.assertEqual(metadata["keywords"], "climate change, global warming, science, environment, greenhouse gases")
        self.assertEqual(metadata["author"], "Environmental Science Institute")
        
        # Check content includes main sections
        self.assertIn("# Climate Change: The Scientific Consensus", content)
        self.assertIn("## Understanding the Science", content)
        self.assertIn("### Key Evidence", content)
        self.assertIn("### Impact on Ecosystems", content)
        
        # Check that lists were preserved
        self.assertIn("* Global temperature has increased", content)
        self.assertIn("* Arctic sea ice and glaciers", content)
        
        # Check that tables were converted
        self.assertIn("| Ecosystem | Primary Impacts | Vulnerability Level |", content)
        self.assertIn("| Coral Reefs | Bleaching, acidification | Very High |", content)
        
        # Check that scripts and comments were removed
        self.assertNotIn("This script will be removed by our converter", content)
        self.assertNotIn("trackAnalytics", content)
        
        # Check that navigation was removed (likely navigation content)
        self.assertNotIn("Home | Articles | Research", content)
    
    def test_convert_xml(self):
        """Test converting an XML file"""
        content, metadata = self.converter.convert(self.xml_file)
        
        # Check content includes the text content from the XML
        self.assertIn("Section 1", content)
        self.assertIn("This is the content of section 1", content)
        self.assertIn("Section 2", content)
        
        # Check that lists are included
        self.assertIn("Item 1", content)
        self.assertIn("Item 2", content)
        
        # XML doesn't have typical metadata tags, so it should use the filename
        self.assertEqual(metadata["file_name"], "test.xml")
    
    def test_clean_document(self):
        """Test cleaning an HTML document"""
        # Create a simple BeautifulSoup document
        html = """
        <html>
            <body>
                <div>Main content</div>
                <script>alert('hello');</script>
                <style>.class { color: red; }</style>
                <!-- Comment -->
                <nav><ul><li>Link 1</li><li>Link 2</li></ul></nav>
                <footer>Copyright 2025</footer>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        
        # Clean the document
        self.converter._clean_document(soup)
        
        # Check that unwanted elements were removed
        self.assertIsNone(soup.find("script"))
        self.assertIsNone(soup.find("style"))
        self.assertIsNone(soup.find(text=lambda t: isinstance(t, Comment)))
        self.assertIsNone(soup.find("nav"))
        self.assertIsNone(soup.find("footer"))
        
        # Check that main content was preserved
        self.assertIsNotNone(soup.find("div"))
        self.assertIn("Main content", soup.text)


if __name__ == "__main__":
    unittest.main()
