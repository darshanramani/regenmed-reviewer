def validate_mp_f_023(data):

    issues = []


    # --------------------------
    # Top section
    # --------------------------

    for field in data.get(
        "top_fields",
        []
    ):

        name = field.get(
            "field",
            "Unknown field"
        )

        value = field.get(
            "value",
            ""
        ).strip()

        if not value:

            issues.append(
                f"Top Section - {name} is missing."
            )


    # --------------------------
    # By / Date fields
    # --------------------------

    for field in data.get(
        "by_date_fields",
        []
    ):

        name = field.get(
            "field",
            "By/Date"
        )

        initials = field.get(
            "initials",
            ""
        ).strip()

        date = field.get(
            "date",
            ""
        ).strip()


        if not initials:

            issues.append(
                f"{name}: Initials are missing."
            )

        if not date:

            issues.append(
                f"{name}: Date is missing."
            )


    # --------------------------
    # Operations Manager Review
    # --------------------------

    manager = data.get(
        "operations_manager_review",
        {}
    )

    manager_initials = manager.get(
        "initials",
        ""
    ).strip()

    manager_date = manager.get(
        "date",
        ""
    ).strip()


    if not manager_initials:

        issues.append(
            "Operations Manager Review: "
            "Initials are missing."
        )

    if not manager_date:

        issues.append(
            "Operations Manager Review: "
            "Date is missing."
        )


    # --------------------------
    # Produced / Packaged
    # --------------------------

    for row in data.get(
        "production_rows",
        []
    ):

        item = row.get(
            "item",
            "Unknown Item"
        )

        required_field = row.get(
            "required_field",
            ""
        ).lower()

        produced = row.get(
            "produced",
            ""
        ).strip()

        packaged = row.get(
            "packaged",
            ""
        ).strip()


        if (
            required_field == "produced"
            and not produced
        ):

            issues.append(
                f"{item}: # Produced is missing."
            )


        elif (
            required_field == "packaged"
            and not packaged
        ):

            issues.append(
                f"{item}: # Packaged is missing."
            )


    return issues