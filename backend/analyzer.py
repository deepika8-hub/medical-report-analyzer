def analyze_lab_results(lab_results):
    analysis = {}
    risk_score = 0

    NORMAL_RANGES = {
        "bilirubin, total": (0.2, 1.3),
        "ast": (0, 40),
        "alt": (0, 41),
        "alp": (35, 104),
        "glucose": (70, 140),
        "hba1c": (4, 5.7),
        "creatinine": (0.6, 1.2)
    }

    for item in lab_results:
        item_lower = item.lower()

        try:
            value = float(item.split(":")[1])
        except:
            continue

        for test_name, (low, high) in NORMAL_RANGES.items():
            if test_name in item_lower:

                if value < low:
                    analysis[test_name] = "Low"
                    risk_score += 1

                elif value > high:
                    analysis[test_name] = "High"
                    risk_score += 2

                else:
                    analysis[test_name] = "Normal"

    # Risk logic
    if risk_score >= 5:
        risk_level = "High"
        disease = "Serious Condition"
    elif risk_score >= 2:
        risk_level = "Medium"
        disease = "Possible Health Issue"
    else:
        risk_level = "Low"
        disease = "Healthy"

    return {
        "analysis": analysis,
        "disease_prediction": disease,
        "risk_level": risk_level
    }