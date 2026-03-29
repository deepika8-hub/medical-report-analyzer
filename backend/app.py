from fastapi import FastAPI, UploadFile, File
import pdfplumber
from extractor import extract_medical_info
from analyzer import analyze_lab_results
from coder import coding_agent

app = FastAPI()

# ---------------- PDF READER ---------------- #
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from PIL import Image
import pdf2image
import os
import tempfile

def read_pdf(file_path):
    text = ""

    try:
        # Try normal text extraction first
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted

        # ✅ If no text found → use OCR
        if not text.strip():
            images = pdf2image.convert_from_path(
                file_path,
                poppler_path=r"C:\poppler\Library\bin",
                # Removed page limit to process all pages
            )

            for img in images:
                try:
                    import cv2
                    import numpy as np

                    img = np.array(img)
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

                    text += pytesseract.image_to_string(thresh, config='--psm 6')

                except:
                    continue
    except Exception as e:
        return ""

    return text

def autocorrect_text(text):
    corrections = {
        "cemm": "hemoglobin",
        "heamoglobin": "hemoglobin",
        "hb": "hemoglobin",
        "sgpt": "alt",
        "sgot": "ast",
        "alk": "alp",
        "bilirbn": "bilirubin",
        "glocose": "glucose",
        "creatnine": "creatinine",
        "monocyte": "monocytes",
        "pcv": "packed cell volume",
        "mcv": "mean corpuscular volume",
        "wbc": "white blood cells",
        "rbc": "red blood cells"
    }
    corrections.update({
        "ca19": "ca 19-9",
        "ca19-9": "ca 19-9",
        "ldh": "ldh",
        "cea": "cea",
        "afp": "afp"
    })

    text_lower = text.lower()

    for wrong, correct in corrections.items():
        text_lower = text_lower.replace(wrong, correct)

    return text_lower

# ---------------- AGENT 1: EXTRACTION ---------------- #
def extraction_agent(text):
    return extract_medical_info(text)

# ---------------- AGENT 2: VALIDATION ---------------- #
def validation_agent(text, extracted):

    if len(extracted["lab_results"]) >= 1:

        return True, "Valid medical report"


    medical_words = [

        "report",
        "patient",
        "diagnosis",
        "test",
        "level",
        "biopsy",
        "tumor",
        "carcinoma",
        "malignant",
        "histopathology",
        "hemoglobin",
        "glucose",
        "creatinine"
    ]


    if any(word in text.lower() for word in medical_words):

        return True, "Medical keywords detected"


    return False, "Not medical"
# ---------------- AGENT 3: CLINICAL ANALYZER ---------------- #
def clinical_agent(lab_results):
    return analyze_lab_results(lab_results)

# ---------------- AGENT 4: DECISION AGENT ---------------- #
def decision_agent(analysis):
    return analysis["risk_level"], analysis["disease_prediction"]

# ---------------- AGENT 5: EXPLANATION AGENT ---------------- #
def explanation_agent(analysis):
    explanation = []

    for test, status in analysis["analysis"].items():
        if status == "High":
            explanation.append(f"{test} is higher than normal range.")
        elif status == "Low":
            explanation.append(f"{test} is lower than normal range.")
        else:
            explanation.append(f"{test} is within normal range.")

    return explanation

# ---------------- CONFIDENCE SCORE ---------------- #
def confidence_agent(analysis):
    total = len(analysis["analysis"])
    normal = len([v for v in analysis["analysis"].values() if v == "Normal"])

    if total == 0:
        return 0

    return round((normal / total) * 100, 2)

# ---------------- MAIN API ---------------- #
@app.post("/process")
async def process_file(file: UploadFile = File(...)):
    content = await file.read()

    # Step 1: Read file using tempfile to avoid leftover files
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
        tmp_file.write(content)
        file_path = tmp_file.name

    # If PDF, run OCR/Text extraction
    if file.filename.lower().endswith(".pdf"):
        text = read_pdf(file_path)
    else:
        try:
            text = content.decode("utf-8")  # attempt text decode for txt files
        except UnicodeDecodeError:
            # fallback: treat as binary and run OCR anyway
            text = read_pdf(file_path)

    # Delete temporary file
    os.remove(file_path)

    # Apply autocorrect after extraction
    text = autocorrect_text(text)

    # Step 2: Extraction Agent
    print("🔍 OCR TEXT:", text[:500])
    extracted = extraction_agent(text)

    # Step 3: Validation Agent
    is_valid, message = validation_agent(text, extracted)

    # 🚨 FORCE ACCEPT FOR OCR CASES
    if not is_valid:
        if len(text.strip()) > 50:
            is_valid = True
        else:
            return {"error": "Low confidence in analysis. Please consult a medical professional."}

    # Step 4: Clinical Agent
    analysis = clinical_agent(extracted["lab_results"])
    coding = coding_agent(analysis, extracted)

    # ---------------- EDGE CASE 1: INSUFFICIENT DATA ---------------- #
    clarification_flag = False
    clarification_msg = ""

    if len(analysis["analysis"]) < 2:
        clarification_flag = True
        clarification_msg = "Insufficient lab data detected. Please provide clearer report or confirm values."

    # ---------------- EDGE CASE 4: AMBIGUITY DETECTION ---------------- #
    ambiguous_tests = []

    for test in extracted["lab_results"]:
        if not any(k in test.lower() for k in [
            "bilirubin", "ast", "alt", "alp", "glucose",
            "creatinine", "hemoglobin", "wbc", "platelet"
        ]):
            ambiguous_tests.append(test)

    if len(ambiguous_tests) > 2:
        clarification_flag = True
        clarification_msg = "Multiple unclear medical parameters detected. Please verify test names."

    # ✅ Fallback: allow minimal analysis
    if len(analysis["analysis"]) == 2:
        audit_note = "Limited data detected — results may be less reliable"
    else:
        audit_note = ""

    # ---------------- EDGE CASE 2 ---------------- #
    high_values = [k for k, v in analysis["analysis"].items() if v == "High"]
    normal_values = [k for k, v in analysis["analysis"].items() if v == "Normal"]

    conflict_flag = False
    if len(high_values) > 0 and len(normal_values) > 0:
        conflict_flag = True

    # ---------------- EDGE CASE 3 ---------------- #
    # ---------------- IMPROVED CONFIDENCE LOGIC ---------------- #

    total_tests = len(analysis["analysis"])

# confidence based on amount of usable data
    if total_tests >= 5:
        confidence_score = 95

    elif total_tests >= 3:
        confidence_score = 85

    elif total_tests >= 1:
        confidence_score = 70

    else:
        return {
            "error": "Insufficient medical data detected."
    }

# NEVER reject if abnormal values detected
    abnormal_tests = len([
        v for v in analysis["analysis"].values()
        if v in ["High", "Low"]
])

    if abnormal_tests > 0:
        confidence_score = max(confidence_score, 85)

    # Step 5–7
    risk, disease = decision_agent(analysis)
    explanation = explanation_agent(analysis)
    confidence = confidence_agent(analysis)

    workflow = [
        "Extraction Completed",
        "Validation Passed",
        "Clinical Analysis Done",
        "Risk Assessment Completed",
        "Explanation Generated"
    ]

    # Ensure audit is always a list
    audit_list = analysis.get("audit", [])
    if audit_note:
        audit_list.append(audit_note)

    return {
        "summary": f"Patient classified as {risk} risk.",
        "risk": risk,
        "confidence": f"{round(confidence_score, 2)}%",
        "conflict_detected": conflict_flag,
        "insights": [f"{k}: {v}" for k, v in analysis["analysis"].items()],
        "explanation": explanation,
        "icd_codes": coding["icd_codes"],
        "cpt_codes": coding["cpt_codes"],
        "coding_reasoning": coding["coding_reasoning"],
        "extracted": analysis["analysis"],
        "workflow": workflow,
        "audit": audit_list,
        "clarification_needed": clarification_flag,
        "clarification_message": clarification_msg,
        "agent_decision": "Clarification Required" if clarification_flag else "Analysis Complete",
        "timeline": analysis["timeline"]
    }