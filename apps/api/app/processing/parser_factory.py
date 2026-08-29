from typing import Dict, Type
from ..parsers.base import BaseParser
from ..parsers.pdf_parser import PDFParser
from ..parsers.docx_parser import DOCXParser
from ..parsers.pptx_parser import PPTXParser
from ..parsers.xlsx_parser import XLSXParser
from ..parsers.markdown_parser import MarkdownParser
from ..parsers.html_parser import HTMLParser
from ..parsers.csv_parser import CSVParser
from ..parsers.txt_parser import TXTParser
from ..parsers.image_parser import ImageParser
from ..parsers.code_parser import CodeParser
from ..parsers.dst_parser import DSTParser

class ParserFactory:
    _parsers: Dict[str, Type[BaseParser]] = {
        "pdf": PDFParser,
        "docx": DOCXParser,
        "doc": DOCXParser,
        "odt": DOCXParser,
        "rtf": TXTParser,
        "pptx": PPTXParser,
        "ppt": PPTXParser,
        "xlsx": XLSXParser,
        "xls": XLSXParser,
        "md": MarkdownParser,
        "html": HTMLParser,
        "htm": HTMLParser,
        "csv": CSVParser,
        "txt": TXTParser,
        "png": ImageParser,
        "jpg": ImageParser,
        "jpeg": ImageParser,
        "gif": ImageParser,
        "webp": ImageParser,
        "tiff": ImageParser,
        # Specialized embroidery formats
        "dst": DSTParser,
        "pes": DSTParser,
        "jef": DSTParser,
        # Code formats
        "java": CodeParser,
        "py": CodeParser,
        "js": CodeParser,
        "ts": CodeParser,
        "c": CodeParser,
        "cpp": CodeParser,
        "css": CodeParser,
        "json": CodeParser,
        "xml": CodeParser,
        "yaml": CodeParser,
        "yml": CodeParser,
        "sql": CodeParser,
        # Archives & binary fallbacks
        "zip": TXTParser,
        "tar": TXTParser,
        "gz": TXTParser
    }

    @classmethod
    def get_parser(cls, extension: str, mime_type: str) -> BaseParser:
        ext = extension.strip().lower().replace(".", "")
        parser_cls = cls._parsers.get(ext)
        
        if not parser_cls:
            if "text/" in mime_type or "json" in mime_type or "xml" in mime_type or "javascript" in mime_type:
                parser_cls = CodeParser
            else:
                parser_cls = TXTParser
        
        return parser_cls()

