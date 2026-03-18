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
        "creatinine": (0.6, 1.2)
    }

    for item in lab_results:
        item_lower = item.lower()
        test_name = item.split(":")[0].strip()

        try:
            value = float(item.split(":")[1])
        except:
            audit.append(f"Skipped invalid: {item}")
            continue

        # ✅ timeline inside loop
        timeline.append({
            "test": test_name,
            "value": value
        })

        matched = False

        # ✅ match correct test
        for key, (low, high) in NORMAL_RANGES.items():
            if key in item_lower:
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

                break

        # ✅ if no rule matched
        if not matched:
            analysis[test_name] = "Normal"
            audit.append(f"{test_name}: {value} → No rule applied")

    # ✅ risk summary
    high_risk_tests = [k for k, v in analysis.items() if v == "High"]

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