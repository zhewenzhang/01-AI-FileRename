import os
import glob
import time
import json
import io
from pathlib import Path
import fitz  # PyMuPDF
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure API Key
# You can set this in a .env file or rely on system environment variables
API_KEY = os.getenv("GEMINI_API_KEY")

class PDFRenamer:
    def __init__(self, directory, dry_run=True, output_directory=None):
        self.directory = Path(directory)
        self.output_directory = Path(output_directory) if output_directory else self.directory
        self.dry_run = dry_run
        
        if not API_KEY:
            raise ValueError("API Key not found. Please set GEMINI_API_KEY in .env file or environment variables.")
        
        genai.configure(api_key=API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def get_pdf_cover_image(self, pdf_path):
        """Render the first page of the PDF to an image stream."""
        try:
            doc = fitz.open(pdf_path)
            if len(doc) < 1:
                return None
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better resolution
            img_data = pix.tobytes("png")
            return img_data
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
            return None
        finally:
            if 'doc' in locals():
                doc.close()

    def analyze_cover(self, image_data):
        """Send image to Gemini to extract metadata."""
        prompt = """
        Analyze this research report cover page. Extract the following information to rename the file.
        Return ONLY a raw JSON object (no markdown formatting) with these keys:
        - "Application": The main industry application (e.g., AI, ADAS, Semi, DRAM, Auto, EV). keep it short.
        - "MarketScope": "WW" for Worldwide/Global, "CN" for China. Default to "WW" if unclear but looks global.
        - "FileName": Comprehend the report content and generate a concise, impactful title in Traditional Chinese (繁體中文). Ensure it is NOT URL-encoded.
        - "Source": The research institution or bank name (short abbreviation if possible, e.g. MS for Morgan Stanley, GS for Goldman Sachs, CICC).
        - "Date": Date of the report in YYMMDD format (e.g., 220625 for June 25, 2022).

        Example JSON:
        {
            "Application": "ADAS",
            "MarketScope": "WW",
            "FileName": "車載傳感器市場分析",
            "Source": "MS",
            "Date": "220625"
        }
        """
        
        try:
            image_part = {"mime_type": "image/png", "data": image_data}
            response = self.model.generate_content([prompt, image_part])
            
            # Clean up response text to ensure it's valid JSON
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            return json.loads(text.strip())
        except Exception as e:
            print(f"Error calling AI API: {e}")
            return None

    def sanitize_filename(self, name):
        """Remove invalid characters for Windows filenames."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, "")
        return name.strip()

    def generate_new_name(self, metadata, original_ext):
        app = self.sanitize_filename(metadata.get("Application", "Unknown"))
        scope = self.sanitize_filename(metadata.get("MarketScope", "WW"))
        title = self.sanitize_filename(metadata.get("FileName", "Untitled"))
        source = self.sanitize_filename(metadata.get("Source", "Unknown"))
        date = self.sanitize_filename(metadata.get("Date", "000000"))
        
        new_name = f"{app}-{scope}-{title}-{source}-{date}{original_ext}"
        return new_name

    def process_files(self):
        print(f"Scanning directory: {self.directory}")
        pdf_files = list(self.directory.glob("*.pdf"))
        
        if not pdf_files:
            print("No PDF files found.")
            return

        print(f"Found {len(pdf_files)} PDFs.")
        print("-" * 50)

        for pdf_path in pdf_files:
            # Skip files that might already be renamed (simple heuristic: contains strict pattern)
            # For now, we process all, or user can assume we verify first.
            if pdf_path.stem.count("-") >= 4:
                 # Optional: Skip likely already processed files
                 # print(f"Skipping potential existing file: {pdf_path.name}")
                 # continue
                 pass

            print(f"Processing: {pdf_path.name}")
            
            img_data = self.get_pdf_cover_image(pdf_path)
            if not img_data:
                print(" -> Failed to extract cover image.")
                continue

            metadata = self.analyze_cover(img_data)
            if not metadata:
                print(" -> AI analysis failed.")
                continue

            new_filename = self.generate_new_name(metadata, pdf_path.suffix)
            # Target path is now in the output directory
            new_path = self.output_directory / new_filename

            # Handle Duplicates
            counter = 1
            while new_path.exists():
                stem = new_path.stem
                if f"_{counter-1}" in stem and counter > 1:
                     stem = stem.rsplit("_", 1)[0]
                new_path = self.output_directory / f"{stem}_{counter}{new_path.suffix}"
                counter += 1

            if self.dry_run:
                print(f" [DRY RUN] Rename & Move: '{pdf_path.name}' \n        -> TO -> '{new_path}'")
            else:
                try:
                    # Rename/Move
                    pdf_path.rename(new_path)
                    print(f" [SUCCESS] Moved to: {new_path.name}")
                except Exception as e:
                    print(f" [ERROR] Could not rename: {e}")
            
            print("-" * 50)
            time.sleep(1) # Rate limit politeness

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-rename PDFs using AI.")
    parser.add_argument("--execute", action="store_true", help="Execute rename operations (default is Dry Run)")
    args = parser.parse_args()

    # Use current working directory
    BASE_DIR = Path(os.getcwd())
    INPUT_DIR = BASE_DIR / "未整理"
    OUTPUT_DIR = BASE_DIR / "已整理"

    # Ensure folders exist
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Check for API Key
    if not API_KEY:
        print("Error: GEMINI_API_KEY not found in environment or .env file.")
        exit(1)

    is_dry_run = not args.execute
    print(f"Running in {'DRY RUN' if is_dry_run else 'EXECUTION'} mode...")
    print(f"Input Directory: {INPUT_DIR}")
    print(f"Output Directory: {OUTPUT_DIR}")

    # Pass Processed folder as destination to the class
    renamer = PDFRenamer(INPUT_DIR, dry_run=is_dry_run, output_directory=OUTPUT_DIR)
    renamer.process_files()
