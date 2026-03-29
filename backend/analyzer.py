def analyze_lab_results(lab_results):
    analysis = {}
    risk_score = 0
    audit = []
    timeline = []

    NORMAL_RANGES = {
        "bilirubin, total": (0.2, 1.3),
        "ast": (0, 40),
        "alt": (0, 41),
        "alp": (35, 104),
        "glucose": (70, 140),
        "hba1c": (4, 5.7),
        "creatinine": (0.6, 1.2),

        # ✅ ADDED (IMPORTANT FIX)
        "hemoglobin": (12, 17),
        "packed cell volume": (36, 50),
        "mean corpuscular volume": (80, 100),
        "monocytes": (2, 8),
        "white blood cells": (4000, 11000),
        "red blood cells": (4, 6),
        "oncology_flag": (0,0),
        "cea": (0,5),
        "afp": (0,8),
        "ca 19-9": (0,37),
        "ldh": (100,250),
        "platelets": (150000, 450000)
    }

    for item in lab_results:
        parts = item.split(":")
        if len(parts) != 2:
            continue

        item_lower = item.lower()
        test_name = parts[0].strip()

        VALID_TESTS = [

    # CBC
                    "hemoglobin",
                    "white blood cells",
                    "wbc",
                    "red blood cells",
                    "rbc",
                    "platelet",
                    "platelets",
                    "packed cell volume",
                    "pcv",
                    "mean corpuscular volume",
                    "mcv",
                    "monocytes",

                    # liver / kidney / metabolic
                    "bilirubin",
                    "ast",
                    "alt",
                    "alp",
                    "glucose",
                    "creatinine",
                    "urea",
                    "protein",

                    # oncology markers
                    "ldh",
                    "cea",
                    "afp",
                    "ca 19-9",
                    "ca19-9",
                    "tumor",
                    "oncology",
                    "ki-67",
                    "her2",
                    "er",
                    "pr"
                ]

        # ❌ Reject non-medical noise
        if not any(valid in test_name.lower() for valid in VALID_TESTS):
            audit.append(f"{test_name} → Rejected (not medical test)")
            continue

        if len(test_name) < 3 or any(char.isdigit() for char in test_name):
            audit.append(f"{test_name} → Invalid test name")
            continue

        # ✅ FIXED VALUE PARSING
        try:
            value = float(parts[1].strip().split()[0])
        except:
            audit.append(f"Skipped invalid: {item}")
            continue

        # 🚨 VALIDATION (kept same position)
        if value > 1000000 or value < 0:
            audit.append(f"{test_name}: {value} → Invalid value detected")
            continue

        # ✅ timeline
        timeline.append({
            "test": test_name,
            "value": value
        })

        matched = False

        # ✅ IMPROVED MATCHING
        for key, (low, high) in NORMAL_RANGES.items():
            if key in item_lower or key in test_name.lower():
                matched = True

                if value < low:
                    analysis[test_name] = "Low"
                    risk_score += 1
                    audit.append(f"{test_name}: {value} < {low} → Low")

                elif value > high:
                    analysis[test_name] = "High"
                    risk_score += 2
                    audit.append(f"{test_name}: {value} > {high} → High")

                else:
                    analysis[test_name] = "Normal"
                    audit.append(f"{test_name}: {value} within range → Normal")

                # -------- Cancer severity boost --------
                if any(marker in test_name.lower() for marker in [
                    "ldh",
                    "cea",
                    "afp",
                    "ca 19-9",
                    "ki-67"
                ]):
                    risk_score += 2
                    audit.append(f"{test_name} flagged as oncology marker → risk increased")
                    # cancer keyword boost
                if "oncology_flag" in test_name.lower():

                    analysis[test_name] = "High"

                    risk_score += 4

                    audit.append("Oncology keyword detected → High risk")
                break

        # ✅ fallback
        if not matched:
            analysis[test_name] = "Normal"
            audit.append(f"{test_name}: {value} → No rule applied")

    # ✅ risk summary
    if risk_score >= 5:
        risk_level = "High"
        disease = "Serious Condition"
    elif risk_score >= 2:
        risk_level = "Medium"
        disease = "Possible Health Issue"
    else:
        risk_level = "Low"
        disease = "Healthy"

    audit.append(f"Total risk score: {risk_score} → {risk_level}")

    return {
        "analysis": analysis,
        "disease_prediction": disease,
        "risk_level": risk_level,
        "audit": audit,
        "timeline": timeline
    }