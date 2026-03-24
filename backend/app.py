from fastapi import FastAPI, UploadFile, File
import pdfplumber
from extractor import extract_medical_info
from analyzer import analyze_lab_results

app = FastAPI()

# ---------------- PDF READER ---------------- #
def read_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


# ---------------- AGENT 1: EXTRACTION ---------------- #
def extraction_agent(text):
    return extract_medical_info(text)


# ---------------- AGENT 2: VALIDATION ---------------- #
def validation_agent(text, extracted):
    text_lower = text.lower()

    medical_keywords = [
        "bilirubin", "ast", "alt", "alp",
        "glucose", "hemoglobin", "creatinine",
        "hba1c"
    ]

    # ✅ 1. Must contain at least 2 strong medical keywords
    keyword_matches = sum(1 for word in medical_keywords if word in text_lower)
    if keyword_matches < 2:
        return False, "Not a medical report (insufficient medical terms)"

    # ✅ 2. Strict lab format check → "Test: value"
    valid_lab_results = []
    for item in extracted["lab_results"]:
        if ":" in item:
            parts = item.split(":")
            if len(parts) == 2:
                try:
                    float(parts[1].strip().split()[0])
                    valid_lab_results.append(item)
                except:
                    continue

    if len(valid_lab_results) < 3:
        return False, "Invalid lab data format"

    # ✅ 3. Reject if too many unknown tests (noise detection)
    known_tests = ["bilirubin", "ast", "alt", "alp", "glucose", "hba1c", "creatinine"]
    unknown_count = 0

    for item in valid_lab_results:
        if not any(k in item.lower() for k in known_tests):
            unknown_count += 1

    if unknown_count > len(valid_lab_results) // 2:
        return False, "Too many unrecognized medical parameters"

    return True, "Valid medical report"


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

    # Step 1: Read file
    if file.filename.endswith(".pdf"):
        with open("temp.pdf", "wb") as f:
            f.write(content)
        text = read_pdf("temp.pdf")
    else:
        text = content.decode("utf-8")

    # Step 2: Extraction Agent
    extracted = extraction_agent(text)

    # Step 3: Validation Agent
    is_valid, message = validation_agent(text, extracted)
    if not is_valid:
        return {"error": message}

    # Step 4: Clinical Agent
    analysis = clinical_agent(extracted["lab_results"])
        # ---------------- EDGE CASE 1: INSUFFICIENT DATA ---------------- #
    if len(analysis["analysis"]) < 3:
        return {
            "error": "Insufficient data to perform reliable analysis"
        }

    # ---------------- EDGE CASE 2: CONFLICT DETECTION ---------------- #
    high_values = [k for k, v in analysis["analysis"].items() if v == "High"]
    normal_values = [k for k, v in analysis["analysis"].items() if v == "Normal"]

    conflict_flag = False
    if len(high_values) > 0 and len(normal_values) > 0:
        conflict_flag = True

    # ---------------- EDGE CASE 3: LOW CONFIDENCE ---------------- #
    total_tests = len(analysis["analysis"])
    abnormal_tests = len([v for v in analysis["analysis"].values() if v != "Normal"])

    confidence_score = 0
    if total_tests > 0:
        confidence_score = (1 - (abnormal_tests / total_tests)) * 100

    if confidence_score < 40:
        return {
            "error": "Low confidence in analysis. Please consult a medical professional."
        }
    # Step 5: Decision Agent
    risk, disease = decision_agent(analysis)

    # Step 6: Explanation Agent
    explanation = explanation_agent(analysis)

    # Step 7: Confidence Agent
    confidence = confidence_agent(analysis)

    # Workflow steps (for frontend display)
    workflow = [
        "Extraction Completed",
        "Validation Passed",
        "Clinical Analysis Done",
        "Risk Assessment Completed",
        "Explanation Generated"
    ]

    # Final response
    return {
        "summary": f"Patient classified as {risk} risk.",
        "risk": risk,
        "confidence": f"{round(confidence_score, 2)}%",
        "conflict_detected": conflict_flag,
        "insights": [f"{k}: {v}" for k, v in analysis["analysis"].items()],
        "explanation": explanation,
        "extracted": analysis["analysis"],
        "workflow": workflow,
        "audit": analysis["audit"],
        "timeline": analysis["timeline"]
    }