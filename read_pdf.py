from langchain_core.tools import tool
import io
import PyPDF2
import requests

@tool
def read_pdf(url: str) -> str:
    """Read and extract text from a PDF file given its URL.

    Args:
        url: The URL of the PDF file to read

    Returns:
        The extracted text content from the PDF
    """
    try:
        # step 1: Access the PDF via url
        response=requests.get(url)
        # step2: convert to bytes
        pdf_file=io.BytesIO(response.content)
        # print(pdf_file)
        # step3: Retrieve text from PDF
        pdf_reader=PyPDF2.PdfReader(pdf_file)
        # print(pdf_reader)
        # print(len(pdf_reader.pages))
        num_pages = len(pdf_reader.pages)
        text = ""
        for i, page in enumerate(pdf_reader.pages, 1):
                print(f"Extracting text from page {i}/{num_pages}")
                text += page.extract_text() + "\n"

        print(f"Successfully extracted {len(text)} characters of text from PDF")
        return text.strip()
    except Exception as e:
        print(f"An error occurred while reading the PDF: {e}")
        raise
print(read_pdf("https://arxiv.org/pdf/2601.23281v1"))