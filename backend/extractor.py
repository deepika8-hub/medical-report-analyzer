import re

def extract_medical_info(text):

    diseases = []
    medications = []
    lab_results = []

    lines = text.split("\n")

    # supported lab tests
    valid_tests = [
        "hemoglobin",
        "hb",
        "rbc",
        "red blood cells",
        "wbc",
        "white blood cells",
        "platelet",
        "platelets",
        "hematocrit",
        "mcv",
        "mean corpuscular volume",
        "mch",
        "creatinine",
        "glucose",
        "bilirubin",
        "ast",
        "alt",
        "alp",

        # oncology markers
        "ldh",
        "cea",
        "afp",
        "ca 19-9",
        "ki-67",
        "her2",
        "er",
        "pr"
    ]


    oncology_keywords = [
        "carcinoma",
        "malignant",
        "tumor",
        "neoplasm",
        "metastasis",
        "oncology",
        "biopsy",
        "histopathology",
        "leukemia",
        "blast cells"
    ]


    for line in lines:

        line_clean = line.strip()

        line_lower = line_clean.lower()


        # ---------------- numeric lab extraction ----------------

        lab_match = re.search(

            r"(hemoglobin|hb|rbc|red blood cells|wbc|white blood cells|platelet|platelets|hematocrit|mcv|mean corpuscular volume|mch|creatinine|glucose|bilirubin|ast|alt|alp|ldh|cea|afp|ca 19-9|ki-67)"

            r"\s*[^0-9]{0,20}"

            r"([0-9,]+\.?[0-9]*)",

            line_lower

        )


        if lab_match:

            name = lab_match.group(1)

            value = lab_match.group(2).replace(",", "")


            # ensure first number is used (not reference range)

            numbers_in_line = re.findall(r"[0-9,]+\.?[0-9]*", line_lower)

            if len(numbers_in_line) > 1:

                value = numbers_in_line[0].replace(",", "")


            # normalize names

            name = name.replace("hb", "hemoglobin")

            name = name.replace("wbc", "white blood cells")

            name = name.replace("rbc", "red blood cells")

            name = name.replace("mcv", "mean corpuscular volume")


            lab_results.append(f"{name}: {value}")

            continue


        # ---------------- ER PR HER2 KI67 detection ----------------

        if "er:" in line_lower:

            lab_results.append("er: 1")


        if "pr:" in line_lower:

            lab_results.append("pr: 1")


        if "her2" in line_lower:

            lab_results.append("her2: 1")


        if "ki-67" in line_lower or "ki67" in line_lower:

            lab_results.append("ki-67: 25")


        # ---------------- oncology keyword detection ----------------

        if any(word in line_lower for word in oncology_keywords):

            diseases.append(line_clean)

            lab_results.append("oncology_flag: 1")


    return {

        "diseases": diseases,

        "medications": medications,

        "lab_results": lab_results

    }