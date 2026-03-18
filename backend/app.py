from fastapi import FastAPI, UploadFile, File
import pdfplumber
from extractor import extract_medical_info
from analyzer import analyze_lab_results

app = FastAPI()

def read_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

@app.post("/process")
async def process_file(file: UploadFile = File(...)):
    content = await file.read()

    if file.filename.endswith(".pdf"):
        with open("temp.pdf", "wb") as f:
            f.write(content)
        text = read_pdf("temp.pdf")
    else:
        text = content.decode("utf-8")

    extracted = extract_medical_info(text)
    analysis = analyze_lab_results(extracted["lab_results"])

    # Prepare clean response
    data = {
        "summary": "Patient summary generated",
        "risk": analysis["risk_level"],
        "insights": [f"{k}: {v}" for k, v in analysis["analysis"].items()],
        "extracted": {
            k: v.strip() for k, v in zip(
                [item.split(":")[0] for item in extracted["lab_results"]],
                [item.split(":")[1] for item in extracted["lab_results"]]
            )
        },
        "explanation": f"Disease prediction: {analysis['disease_prediction']}",
        "audit": analysis["audit"],          
        "timeline": analysis["timeline"]     
    }
    return data