from fastapi import FastAPI, UploadFile, File, HTTPException
from PIL import Image
import io
import re
import uvicorn
import easyocr
import pytesseract

app = FastAPI(title="Real InBody OCR Microservice")
reader = easyocr.Reader(['en'], gpu=False)
print("downloaded easyocr model")

# Set the path to the Tesseract executable if it's not in your system's PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def parse_inbody_text(full_text: str):
    """Regex Patterns"""
    #Weight
    weight_match = re.search(r'(?:Weight|WT|Weight\(kg\))\s*[:=]?\s*(\d{2,3}\.?\d?)', full_text, re.IGNORECASE)
    # muscle mass
    smm_match = re.search(r'(?:SMM|Skeletal Muscle Mass)\s*[:=]?\s*(\d{2,3}\.?\d?)', full_text, re.IGNORECASE)
    # body fat 
    pbf_match = re.search(r'(?:PBF|Percent Body Fat|Body Fat %)\s*[:=]?\s*(\d{1,2}\.?\d?)', full_text, re.IGNORECASE)
    #body mass index(BMI)
    bmi_match = re.search(r'(?:BMI|Body Mass Index)\s*[:=]?\s*(\d{2}\.?\d?)', full_text, re.IGNORECASE)
    # Total water
    tbw_match = re.search(r'(?:TBW|Total Body Water)\s*[:=]?\s*(\d{2,3}\.?\d?)', full_text, re.IGNORECASE)
    return {
        "weight_kg": float(weight_match.group(1)) if weight_match else None,
        "skeletal_muscle_mass_kg": float(smm_match.group(1)) if smm_match else None,
        "body_fat_percent": float(pbf_match.group(1)) if pbf_match else None,
        "bmi": float(bmi_match.group(1)) if bmi_match else None,
        "total_body_water_l": float(tbw_match.group(1)) if tbw_match else None
    }

@app.post("/scan-inbody")
async def scan_inbody(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        #extract text using EasyOCR
        easyocr_results = reader.readtext(image_bytes, detail=0)
        full_text = " ".join(easyocr_results)
        #extract text using Tesseract OCR
        tesseract_text = ""
        try:
            tesseract_text = pytesseract.image_to_string(image)
        except Exception as tss_err:
            print(f"⚠️ Tesseract warning (تنفيذ بدون Tesseract): {tss_err}")

        # combine both OCR results
        combined_text = full_text + " " + tesseract_text

        # Parse the combined text to extract relevant data
        extracted_data = parse_inbody_text(combined_text)
        extracted_data["raw_text_easyocr"] = full_text
        extracted_data["raw_text_tesseract"] = tesseract_text

        return {
            "status": "success",
            "data": extracted_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error:{str(e)}")

if __name__ == "__main__":
    uvicorn.run("ocr_service:app", host="127.0.0.1", port=8001, reload=True)