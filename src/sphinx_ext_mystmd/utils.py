import re
import collections


def title_to_name(title):
    return input_to_name(title.replace("&", "¶and¶"), re.compile(r"[a-z0-9-]"), "-")[:50]


def input_to_name(input_, allowed, join):
    escaped = ''.join([c if allowed.search(c) else '¶' for c in f"¶{input_}".lower()])
    unique = re.sub(r"¶+", "¶", escaped)
    name = re.sub("¶", join, unique[1:])
    if join:
        name = re.sub(f"{join}+", join, name)
    if name[0] == join:
        name = name[1:]
    if name[-1] == join:
        name = name[:-1]
    return name


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


def to_text(node):
    if "value" in node:
        return node["value"]
    elif "children" in node:
        return "".join([to_text(n) for n in node["children"]])
    else:
        return ""


def depth_first_walk(node):
    queue = [node]
    while queue:
        this = queue.pop()
        if "children" in this:
            queue.extend(this['children'])
        yield this


def breadth_first_walk(node):
    queue = collections.deque([node])
    while queue:
        this = queue.popleft()
        if "children" in this:
            queue.extend(this['children'])
        yield this



def find_by_type(type_, node):
    for node in breadth_first_walk(node):
        if node["type"] == type_:
            yield node
