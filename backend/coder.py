def coding_agent(analysis, extracted):
    icd_codes = []
    cpt_codes = []
    reasoning = []
    clarification_needed = False

    ICD_MAP = {
        "glucose": ("E11", "Type 2 Diabetes Mellitus"),
        "hba1c": ("E11", "Type 2 Diabetes Mellitus"),
        "creatinine": ("N18", "Chronic Kidney Disease"),
        "bilirubin": ("K76", "Liver Disease"),
        "ast": ("K76", "Liver Disorder"),
        "alt": ("K76", "Liver Disorder"),
    }

    # ✅ extend ICD
    ICD_MAP.update({
        "alp": ("K76", "Liver Disorder"),
        "protein": ("E88", "Metabolic Disorder"),
        "globulin": ("E88", "Protein Disorder")
    })

    CPT_MAP = {
        "glucose": ("82947", "Glucose Test"),
        "hba1c": ("83036", "HbA1c Test"),
        "creatinine": ("82565", "Creatinine Test"),
        "bilirubin": ("82247", "Bilirubin Test"),
        "ast": ("84450", "AST Test"),
        "alt": ("84460", "ALT Test"),
        "alp": ("84075", "ALP Test"),
        "protein": ("84155", "Total Protein Test"),
        "globulin": ("84165", "Protein Electrophoresis")
    }

    # ✅ MAIN LOOP (fixed)
    for test, status in analysis["analysis"].items():
        test_lower = test.lower()
        matched = False

        # ❗ special handling (kept your logic)
        if "globulin" in test_lower:
            reasoning.append(f"{test} is Normal → part of protein panel, no separate CPT code")
            continue

        for key in ICD_MAP:
            if key in test_lower:
                matched = True

                # ✅ CPT ALWAYS
                cpt_code, cpt_desc = CPT_MAP[key]
                cpt_codes.append({
                    "code": cpt_code,
                    "description": cpt_desc
                })

                # ✅ ICD ONLY IF ABNORMAL
                if status in ["High", "Low"]:
                    icd_code, icd_desc = ICD_MAP[key]
                    icd_codes.append({
                        "code": icd_code,
                        "description": icd_desc
                    })

                    reasoning.append(
                        f"{test} is {status} → indicates {icd_desc} ({icd_code})"
                    )
                else:
                    reasoning.append(
                        f"{test} is Normal → no disease code assigned"
                    )

                break

        # ❗ Ambiguous
        if not matched:
            clarification_needed = True
            reasoning.append(
                f"{test} not clearly mapped → requires clarification"
            )

    # ✅ Remove duplicates
    icd_codes = [dict(t) for t in {tuple(d.items()) for d in icd_codes}]
    cpt_codes = [dict(t) for t in {tuple(d.items()) for d in cpt_codes}]

    return {
        "icd_codes": icd_codes,
        "cpt_codes": cpt_codes,
        "coding_reasoning": reasoning,
        "clarification_needed": clarification_needed
    }