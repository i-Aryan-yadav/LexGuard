import io
import docx
import pypdf
import pytesseract
from PIL import Image
from app.core.logging import logger

class TextExtractor:
    def __init__(self):
        # Ensure tesseract is in PATH or configure it here if needed
        pass

    def extract(self, file_content: bytes, filename: str) -> str:
        ext = filename.split('.')[-1].lower()
        
        if ext == 'docx':
            return self._extract_docx(file_content)
        elif ext == 'pdf':
            return self._extract_pdf(file_content)
        elif ext in ['jpg', 'png', 'jpeg']:
            return self._extract_image(file_content)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _extract_docx(self, content: bytes) -> str:
        try:
            doc = docx.Document(io.BytesIO(content))
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            return '\n'.join(full_text)
        except Exception as e:
            logger.error(f"Error extracting DOCX: {e}")
            raise

    def _extract_pdf(self, content: bytes) -> str:
        try:
            reader = pypdf.PdfReader(io.BytesIO(content))
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                else:
                    # Fallback to OCR for scanned pages
                     # Requires pdf2image or similar to convert page to image first
                     # For simplicity in this implementation, we just log warning
                    logger.warning("Empty text in PDF page, might be scanned image.")
            return text
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            raise

    def _extract_image(self, content: bytes) -> str:
        try:
            image = Image.open(io.BytesIO(content))
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            logger.error(f"Error extracting Image: {e}")
            raise

text_extractor = TextExtractor()
