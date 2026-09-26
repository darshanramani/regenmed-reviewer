def validate_discard_form(data):

    issues = []

    # =====================================================
    # TOP SECTION
    # =====================================================

    donor_number = data.get(
        "donor_number",
        ""
    ).strip()

    authorized_by = data.get(
        "discard_authorized_by",
        ""
    ).strip()

    authorized_date = data.get(
        "discard_authorized_date",
        ""
    ).strip()

    reason = data.get(
        "reason_for_discard",
        ""
    ).strip()


    if not donor_number:
        issues.append(
            "Top Section: Donor # is missing."
        )

    if not authorized_by:
        issues.append(
            "Top Section: Discard Authorized By is missing."
        )

    if not authorized_date:
        issues.append(
            "Top Section: Discard Authorized Date is missing."
        )

    if not reason:
        issues.append(
            "Top Section: Reason for Discard is missing."
        )


    # =====================================================
    # TISSUE STATUS
    # =====================================================

    tissue_status = data.get(
        "tissue_status",
        {}
    )

    selected_statuses = []

    status_fields = {
        "unprocessed_tissue": "Unprocessed Tissue",
        "in_processing_tissue": "In Processing Tissue",
        "unreleased_packaged_tissue": "Unreleased Packaged Tissue",
        "released_packaged_tissue": "Released Packaged Tissue"
    }

    for key, label in status_fields.items():

        if tissue_status.get(
            key,
            False
        ):
            selected_statuses.append(
                label
            )


    if len(selected_statuses) == 0:

        issues.append(
            "Tissue Status: No status box is selected."
        )

    elif len(selected_statuses) > 1:

        issues.append(
            "Tissue Status: More than one status box appears selected."
        )


    selected_status = (
        selected_statuses[0]
        if len(selected_statuses) == 1
        else ""
    )


    # =====================================================
    # TISSUE ROWS
    # =====================================================

    tissue_rows = data.get(
        "tissue_rows",
        []
    )

    actual_graft_id_found = False
    na_graft_id_found = False


    for index, row in enumerate(
        tissue_rows,
        start=1
    ):

        graft_id = row.get(
            "graft_id",
            ""
        ).strip()

        tissue_description = row.get(
            "tissue_description",
            ""
        ).strip()

        storage_location = row.get(
            "storage_location",
            ""
        ).strip()

        confirmed_x = row.get(
            "confirmed_x",
            False
        )


        # Ignore fully blank unused table rows
        if (
            not graft_id
            and not tissue_description
            and not storage_location
        ):
            continue


        normalized_graft_id = (
            graft_id
            .replace(" ", "")
            .upper()
        )


        if normalized_graft_id in [
            "N/A",
            "NA"
        ]:

            na_graft_id_found = True

        elif graft_id:

            actual_graft_id_found = True


        if not confirmed_x:

            issues.append(
                f"Tissue Row {index}: Confirmation X is missing."
            )


    # =====================================================
    # STATUS / GRAFT ID CONSISTENCY
    # =====================================================

    packaged_statuses = [
        "Unreleased Packaged Tissue",
        "Released Packaged Tissue"
    ]

    non_packaged_statuses = [
        "Unprocessed Tissue",
        "In Processing Tissue"
    ]


    if actual_graft_id_found:

        if (
            selected_status
            and selected_status not in packaged_statuses
        ):

            issues.append(
                "Tissue Status is inconsistent with the listed Graft ID(s). "
                "A listed Graft ID requires Unreleased Packaged Tissue "
                "or Released Packaged Tissue."
            )


    elif na_graft_id_found:

        if (
            selected_status
            and selected_status not in non_packaged_statuses
        ):

            issues.append(
                "Tissue Status is inconsistent with Graft ID N/A. "
                "N/A requires Unprocessed Tissue or In Processing Tissue."
            )


    # =====================================================
    # BOTTOM SECTION
    # =====================================================

    bottom_fields = data.get(
        "bottom_fields",
        {}
    )

    bottom_labels = {
        "tissue_discarded_by": "Tissue Discarded By",
        "confirmed_by": "Confirmed By",
        "discard_date": "Discard Date",
        "freezerpro_updated_by": "FreezerPro Updated By",
        "freezerpro_updated_date": "FreezerPro Updated Date",
        "donor_chart_updated_by": "Donor Chart / Log / FreezerPro Updated By",
        "donor_chart_updated_date": "Donor Chart / Log / FreezerPro Updated Date"
    }


    for key, label in bottom_labels.items():

        value = bottom_fields.get(
            key,
            ""
        )

        if value is None:
            value = ""

        value = str(
            value
        ).strip()

        if not value:

            issues.append(
                f"Bottom Section: {label} is missing."
            )


    return issues