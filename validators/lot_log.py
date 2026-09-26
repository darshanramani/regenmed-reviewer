def validate_lot_log(data):

    issues = []

    # --------------------------------
    # PAGE 1 - Item table
    # --------------------------------

    for row in data.get("page_1_items", []):

        item = row.get("item", "Unknown Item")

        if not row.get("lot_number", "").strip():
            issues.append(
                f"Page 1 - {item}: Lot Number is missing."
            )

        if not row.get("exp_date", "").strip():
            issues.append(
                f"Page 1 - {item}: Expiration Date is missing."
            )

        if not row.get("manufacturer", "").strip():
            issues.append(
                f"Page 1 - {item}: Manufacturer is missing."
            )


    # --------------------------------
    # PAGE 1 - RegenMed Item table
    # --------------------------------

    for row in data.get("regenmed_items", []):

        item = row.get("item", "Unknown Item")

        if not row.get("lot", "").strip():
            issues.append(
                f"Page 1 - RegenMed Item - {item}: Lot is missing."
            )

        if not row.get("qty_used", "").strip():
            issues.append(
                f"Page 1 - RegenMed Item - {item}: Qty Used is missing."
            )


    # --------------------------------
    # PAGE 2 - Item table
    # --------------------------------

    for row in data.get("page_2_items", []):

        item = row.get("item", "Unknown Item")

        if not row.get("load_number", "").strip():
            issues.append(
                f"Page 2 - {item}: Load Number is missing."
            )

        if not row.get("sterilization_date", "").strip():
            issues.append(
                f"Page 2 - {item}: Sterilization Date is missing."
            )


    # --------------------------------
    # PAGE 2 - Packaging table
    # --------------------------------

    for row in data.get("packaging", []):

        item = row.get("item", "Unknown Packaging Item")

        load_number = row.get("load_number", "").strip()
        sterilization_date = row.get("sterilization_date", "").strip()

        if not load_number and not sterilization_date:
            issues.append(
                f"Page 2 - {item}: Load Number or Sterilization Date is required."
            )


    return issues