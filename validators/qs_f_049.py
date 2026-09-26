import re


DATE_PATTERN = r"^\d{2}/\d{2}/\d{2}$"


def valid_date(value):

    if not value:
        return False

    return bool(
        re.match(
            DATE_PATTERN,
            value.strip()
        )
    )


def validate_qs_f_049(data):

    issues = []

    rows = data.get(
        "review_rows",
        []
    )

    for row in rows:

        item = row.get(
            "item",
            "Unknown"
        )


        # --------------------------
        # Technical Review
        # --------------------------

        tech_initials = row.get(
            "technical_initials",
            ""
        ).strip()

        tech_date = row.get(
            "technical_date",
            ""
        ).strip()

        tech_na = row.get(
            "technical_na",
            False
        )


        if not tech_na:

            if not tech_initials:

                issues.append(
                    f"Item {item} - Technical Review: "
                    f"Initials are missing."
                )

            if not tech_date:

                issues.append(
                    f"Item {item} - Technical Review: "
                    f"Date is missing."
                )

            elif not valid_date(tech_date):

                issues.append(
                    f"Item {item} - Technical Review: "
                    f"Date must use MM/DD/YY format."
                )


        # --------------------------
        # Quality Review
        # --------------------------

        quality_initials = row.get(
            "quality_initials",
            ""
        ).strip()

        quality_date = row.get(
            "quality_date",
            ""
        ).strip()

        quality_na = row.get(
            "quality_na",
            False
        )


        if not quality_na:

            if not quality_initials:

                issues.append(
                    f"Item {item} - Quality Review: "
                    f"Initials are missing."
                )

            if not quality_date:

                issues.append(
                    f"Item {item} - Quality Review: "
                    f"Date is missing."
                )

            elif not valid_date(quality_date):

                issues.append(
                    f"Item {item} - Quality Review: "
                    f"Date must use MM/DD/YY format."
                )


    # --------------------------
    # Item 10 INC / Status
    # --------------------------

    item_10 = data.get(
        "item_10",
        {}
    )

    inc_number = item_10.get(
        "inc_number",
        ""
    ).strip()

    status = item_10.get(
        "status",
        ""
    ).strip()


    if inc_number and not status:

        issues.append(
            "Item 10: INC # is present "
            "but Status is missing."
        )


    return issues