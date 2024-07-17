import re


def normalize_label(
    label,
):
    if not label:
        return None
    identifier = (
        re.sub(r'[\'‘’"“”]+', "", re.sub(r"[\t\n\r ]+", " ", label)).strip().lower()
    )
    html_id = create_html_id(identifier)
    return [identifier, label, html_id]


def create_html_id(identifier):
    if not identifier:
        return None
    return re.sub(
        "(?:^[-]+)|(?:[-]+$)",  # Remove repeated '-'s at the start or end
        "",
        re.sub(
            "-[-]+",  # Replace repeated '-'s
            "-",
            re.sub(
                r"^([0-9-])",  # Ensure that the ID starts with a letter
                "id-\1",
                re.sub(
                    "[^a-z0-9-]", "-", identifier.lower()  # Remove any fancy characters
                ),
            ),
        ),
    )
