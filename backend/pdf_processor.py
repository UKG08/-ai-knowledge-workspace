"""
PDF Processor Module
Extracts text from PDF files
"""

import os
from typing import Dict
from PyPDF2 import PdfReader


class PDFProcessor:
    """
    Handles all PDF-related operations.
    """
    
    def __init__(self, upload_folder: str = "data/uploads"):
        """
        Setup: Create the upload folder if it doesn't exist
        """
        self.upload_folder = upload_folder
        
        # Create folder if missing
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            print(f"✅ Created upload folder: {upload_folder}")
    
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract all text from a PDF file
        """
        try:
            # Step 1: Open the PDF
            reader = PdfReader(pdf_path)
            
            # Step 2: Count pages
            total_pages = len(reader.pages)
            print(f"📄 Processing: {os.path.basename(pdf_path)}")
            print(f"📊 Total pages: {total_pages}")
            
            # Step 3: Extract text from each page
            all_text = []
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                all_text.append(text)
                print(f"   ✓ Page {page_num}/{total_pages}")
            
            # Step 4: Combine all pages
            full_text = "\n\n".join(all_text)
            
            # Step 5: Clean the text (remove extra spaces)
            full_text = " ".join(full_text.split())
            
            print(f"✅ Done! {len(full_text)} characters extracted")
            return full_text
            
        except FileNotFoundError:
            print(f"❌ Error: File not found: {pdf_path}")
            return ""
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return ""
    
    
    def process_multiple_pdfs(self, pdf_folder: str = None) -> Dict[str, str]:
        """
        Extract text from ALL PDFs in a folder
        """
        if pdf_folder is None:
            pdf_folder = self.upload_folder
        
        results = {}
        
        # Find all PDF files
        pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
        
        if not pdf_files:
            print(f"⚠️ No PDFs found in {pdf_folder}")
            return results
        
        print(f"\n🔍 Found {len(pdf_files)} PDF(s)")
        print("=" * 50)
        
        # Process each PDF
        for pdf_file in pdf_files:
            pdf_path = os.path.join(pdf_folder, pdf_file)
            text = self.extract_text_from_pdf(pdf_path)
            results[pdf_file] = text
            print("=" * 50)
        
        print(f"\n✅ Processed {len(results)} PDF(s)")
        return results


# ============================================================================
# TESTING CODE
# ============================================================================
if __name__ == "__main__":
    print("🧪 Testing PDF Processor...")
    print("=" * 50)
    
    # Create processor
    processor = PDFProcessor()
    
    # Process all PDFs in uploads folder
    results = processor.process_multiple_pdfs()
    
    # Show results
    if results:
        print("\n📊 RESULTS:")
        print("=" * 50)
        for filename, text in results.items():
            preview = text[:200] + "..." if len(text) > 200 else text
            print(f"\n📄 {filename}")
            print(f"   Length: {len(text)} characters")
            print(f"   Preview: {preview}")
    else:
        print("\n⚠️ No PDFs found")
        print(f"   Add PDFs to: {processor.upload_folder}")
    
    print("\n" + "=" * 50)
    print("✅ Test complete!")