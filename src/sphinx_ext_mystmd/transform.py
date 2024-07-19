import contextlib
from docutils.nodes import NodeVisitor, SkipChildren, SkipSiblings
from weakref import WeakKeyDictionary
import inspect


from .utils import normalize_label


def is_context_manager(obj):
    return hasattr(obj, "__enter__")


class Visitor(NodeVisitor):

    def __init__(self, document):
        super().__init__(document)

        self._visited = WeakKeyDictionary()
        self._stack = []

    def dispatch_visit(self, node):
        visitor_name = f"visit_{node.__class__.__name__}"
        impl = getattr(self, visitor_name)

        # Invoke visitor
        instruction_or_ctx_like = impl(node)
        if is_context_manager(instruction_or_ctx_like):
            maybe_instruction = instruction_or_ctx_like.__enter__()
        elif inspect.isgenerator(instruction_or_ctx_like):
            maybe_instruction = next(instruction_or_ctx_like)
        else:
            maybe_instruction = instruction_or_ctx_like

        # Allow context managers to use control flow without preventing cleanup
        self._visited[node] = instruction_or_ctx_like
        self._stack.append(node)

        if maybe_instruction in (SkipChildren, SkipSiblings):
            raise maybe_instruction

    def dispatch_departure(self, node):
        try:
            gen_or_ctx_like = self._visited.pop(node)
        except KeyError:
            return

        self._stack.pop()

        # Exit result generator
        if is_context_manager(gen_or_ctx_like):
            gen_or_ctx_like.__exit__(None, None, None)
        elif inspect.isgenerator(gen_or_ctx_like):
            next(gen_or_ctx_like, None)

    @property
    def parent_node(self):
        return self._stack[-1] if self._stack else None


class MySTNodeVisitor(Visitor):

    def __init__(self, document):
        super().__init__(document)

        self._heading_depth = 0
        self._next_sibling_id = None

        self._result = None
        self._result_stack = []

    @property
    def parent_result(self):
        return self._result_stack[-1] if self._result_stack else None

    @property
    def result(self):
        return self._result

    def inherit_node_info(self, node, docutils_node):
        ids = docutils_node.get("ids", [])
        if ids:
            if len(ids) > 1:
                print(f"Warning, found multiple ids: {ids}, using {ids[-1]}")

            identifier, label, _ = normalize_label(ids[-1])
            node["identifier"] = identifier
            node["label"] = label

    def push_myst_node(self, node, docutils_node=None):
        self.parent_result["children"].append(node)
        if docutils_node is not None:
            self.inherit_node_info(node, docutils_node)

    @contextlib.contextmanager
    def enter_myst_node(self, node, docutils_node=None):
        if self._result_stack:
            parent = self._result_stack[-1]
            parent["children"].append(node)

        self._result_stack.append(node)
        if docutils_node is not None:
            self.inherit_node_info(node, docutils_node)
        try:
            yield node
        finally:
            self._result_stack.pop()

    def visit_meta(self, node): ...  # TODO: parse this?

    def visit_comment(self, node):
        with self.enter_myst_node(
            {"type": "comment", "value": str(node.children[0])}, node  # TODO: totext
        ):
            yield SkipChildren

    def visit_raw(self, node):
        return self.enter_myst_node(
            {"type": "paragraph", "children": [{"type": "text", "value": str(node)}]}
        )

    def visit_compact_paragraph(self, node):
        return self.enter_myst_node({"type": "paragraph", "children": []}, node)

    def visit_inline(self, node):
        return self.enter_myst_node(
            {"type": "span", "class": node.get("classes"), "children": []}, node
        )

    def visit_reference(self, node):
        if node.get("refid"):
            return self.enter_myst_node(
                {"type": "link", "url": f"#{node['refid']}", "children": []}, node
            )
        elif node.get("refuri"):
            return self.enter_myst_node(
                {"type": "link", "url": node["refuri"], "children": []}, node
            )
        else:
            raise

    visit_number_reference = visit_reference

    def visit_topic(self, node):
        return self.enter_myst_node({"type": "admonition", "children": []}, node)

    def visit_problematic(self, node):
        return self.enter_myst_node(
            {"type": "span", "class": "problematic", "children": []}, node
        )

    def visit_target(self, node):
        # self.next_sibling_id = node["refid"]
        # TODO
        ...

    @contextlib.contextmanager
    def enter_heading(self):
        depth, self._heading_depth = self._heading_depth, self._heading_depth + 1
        try:
            yield
        finally:
            self._heading_depth = depth

    def visit_title(self, node):
        parent_type = self.parent_node.__class__.__name__
        if parent_type == "section":
            with self.enter_myst_node(
                {"type": "heading", "depth": self._heading_depth, "children": []}, node
            ):
                yield
        elif parent_type in {"topic", "admonition", "sidebar"}:
            with self.enter_myst_node(
                {
                    "type": "admonitionTitle",
                    "children": [],
                }
            ):
                yield
        else:
            raise NotImplementedError(parent_type)

    def visit_enumerated_list(self, node):
        return self.enter_myst_node(
            {"type": "list", "ordered": True, "children": []}, node
        )

    def visit_substition_definition(self, node):
        return SkipChildren

    def visit_subtitle(self, node):
        with self.enter_myst_node(
            {"type": "heading", "depth": self._heading_depth + 1, "children": []}, node
        ):
            with self.enter_heading():
                yield

    def visit_bullet_list(self, node):
        return self.enter_myst_node({"type": "list", "children": []}, node)

    def visit_rubric(self, node):
        return self.enter_myst_node({"type": "blockQuote", "children": []}, node)

    def visit_transition(self, node):
        return self.enter_myst_node({"type": "thematicBreak"})

    def visit_list_item(self, node):
        return self.enter_myst_node({"type": "listItem", "children": []}, node)

    def visit_emphasis(self, node):
        return self.enter_myst_node({"type": "emphasis", "children": []}, node)

    def visit_strong(self, node):
        return self.enter_myst_node({"type": "strong", "children": []}, node)

    def visit_subscript(self, node):
        self.push_myst_node({"type": "html", "value": "<sub>"})
        yield
        self.push_myst_node({"type": "html", "value": "</sub>"})

    def visit_superscript(self, node):
        self.push_myst_node({"type": "html", "value": "<sup>"})
        yield
        self.push_myst_node({"type": "html", "value": "</sup>"})

    def visit_literal(self, node):
        return self.enter_myst_node({"type": "inlineCode", "children": []}, node)

    def visit_literal_emphasis(self, node):
        with self.enter_myst_node({"type": "emphasis", "children": []}, node):
            with self.enter_myst_node({"type": "inlineCode", "children": []}):
                yield

    def visit_literal_strong(self, node):
        with self.enter_myst_node({"type": "strong", "children": []}, node):
            with self.enter_myst_node({"type": "inlineCode", "children": []}):
                yield

    def visit_footnote_reference(self, node):
        return self.enter_myst_node(
            {"type": "link", "url": f"#", "children": []}, node
        )  # TODO: fix url

    def visit_index(self, node):
        return

    def visit_title_reference(self, node):
        return self.enter_myst_node(  # TODO fix url
            {"type": "link", "url": f"#", "children": []}, node
        )

    def visit_sidebar(self, node):
        return self.enter_myst_node(
            {"type": "aside", "kind": "sidebar", "children": []}, node
        )

    def visit_image(self, node):
        return self.enter_myst_node({"type": "image", "url": node["uri"]})

    def visit_paragraph(self, node):
        return self.enter_myst_node({"type": "paragraph", "children": []}, node)

    def visit_Text(self, node):
        return self.enter_myst_node({"type": "text", "value": str(node)})

    # visit_XXX admonitions (see loop below)

    def visit_section(self, node):
        with self.enter_myst_node({"type": "block", "children": []}, node):
            with self.enter_heading():
                yield

    def visit_document(self, node):
        with self.enter_myst_node({"type": "root", "children": []}, node) as result:
            yield

        self._result = result

    def visit_generated(self, node):
        return

    def visit_field_list(self, node):
        return self.enter_myst_node({"type": "fieldList", "children": []}, node)

    def visit_field(self, node):
        return self.enter_myst_node({"type": "fieldListItem", "children": []}, node)

    def visit_field_name(self, node):
        return self.enter_myst_node({"type": "fieldName", "children": []}, node)

    def visit_field_body(self, node):
        return self.enter_myst_node({"type": "fieldDescription", "children": []}, node)

    def visit_classifier(self, node):
        return SkipChildren

    def visit_definition_list(self, node):
        return self.enter_myst_node({"type": "definitionList", "children": []}, node)

    def visit_definition(self, node):
        return self.enter_myst_node(
            {"type": "definitionDescription", "children": []}, node
        )

    def visit_term(self, node):
        return self.enter_myst_node({"type": "definitionTerm", "children": []}, node)

    def visit_definition_list_item(self, node):
        return

    def visit_option_list(self, node):
        return SkipChildren

    def visit_line_block(self, node):
        return SkipChildren

    def visit_doctest_block(self, node):
        return SkipChildren

    def visit_table(self, node):
        return self.enter_myst_node({"type": "table", "children": []}, node)

    def visit_tgroup(self, node): ...

    def visit_tbody(self, node): ...

    def visit_row(self, node):
        return self.enter_myst_node({"type": "tableRow", "children": []}, node)

    def visit_entry(self, node):
        return self.enter_myst_node({"type": "tableCell", "children": []}, node)

    def visit_footnote(self, node):
        return self.enter_myst_node(
            {"type": "footnoteDefinition", "children": []}, node
        )

    def visit_label(self, node):
        return SkipChildren

    def visit_citation(self, node):
        return SkipChildren

    def visit_legend(self, node):
        return SkipChildren

    def visit_caption(self, node):
        return self.enter_myst_node(
            {"type": "caption", "kind": "figure", "children": []}, node
        )

    def visit_figure(self, node):
        return self.enter_myst_node(
            {"type": "container", "kind": "figure", "children": []}, node
        )

    def visit_thead(self, node):
        table = self.parent_result
        children = table["children"]
        n_children = len(children)

        yield

        new_children = children[n_children:]

        for child in new_children:
            assert child["type"] == "tableRow"
            for row_child in child["children"]:
                row_child["header"] = True

    def visit_colspec(self, node): ...

    def visit_literal_block(self, node):
        return  # skip literal part!

    def visit_block_quote(self, node):
        return self.enter_myst_node({"type": "blockquote", "children": []}, node)

    def visit_attribution(self, node):
        return self.enter_myst_node({"type": "caption", "children": []}, node)

    def visit_admonition(self, node):
        return self.enter_myst_node({"type": "admonition", "children": []}, node)

    def visit_substitution_definition(self, node):
        # TODO: cache this?
        return SkipChildren

    def visit_compound(self, node):
        return self.enter_myst_node(
            {"type": "div", "children": []}, node
        )  # TODO: proper container?

    def visit_desc(self, node):
        return self.enter_myst_node({"type": "desc", "children": []}, node)

    def visit_desc_addname(self, node):
        return self.enter_myst_node({"type": "descAddname", "children": []}, node)

    def visit_desc_annotation(self, node):
        return self.enter_myst_node({"type": "descAnnotation", "children": []}, node)

    def visit_desc_classes_injector(self, node):
        return self.enter_myst_node(
            {"type": "descClassesInjector", "children": []}, node
        )

    def visit_desc_content(self, node):
        return self.enter_myst_node({"type": "descContent", "children": []}, node)

    def visit_desc_inline(self, node):
        return self.enter_myst_node({"type": "descInline", "children": []}, node)

    def visit_desc_name(self, node):
        return self.enter_myst_node({"type": "descName", "children": []}, node)

    def visit_desc_optional(self, node):
        return self.enter_myst_node({"type": "descOptional", "children": []}, node)

    def visit_desc_parameter(self, node):
        return self.enter_myst_node({"type": "descParameter", "children": []}, node)

    def visit_desc_parameterlist(self, node):
        return self.enter_myst_node({"type": "descParameterlist", "children": []}, node)

    def visit_desc_returns(self, node):
        return self.enter_myst_node({"type": "descReturns", "children": []}, node)

    def visit_desc_sig_element(self, node):
        return self.enter_myst_node({"type": "descSigElement", "children": []}, node)

    def visit_desc_sig_keyword(self, node):
        return self.enter_myst_node({"type": "descSigKeyword", "children": []}, node)

    def visit_desc_sig_keyword_type(self, node):
        return self.enter_myst_node(
            {"type": "descSigKeywordType", "children": []}, node
        )

    def visit_desc_sig_literal_char(self, node):
        return self.enter_myst_node(
            {"type": "descSigLiteralChar", "children": []}, node
        )

    def visit_desc_sig_literal_number(self, node):
        return self.enter_myst_node(
            {"type": "descSigLiteralNumber", "children": []}, node
        )

    def visit_desc_sig_literal_string(self, node):
        return self.enter_myst_node(
            {"type": "descSigLiteralString", "children": []}, node
        )

    def visit_desc_sig_name(self, node):
        return self.enter_myst_node({"type": "descSigName", "children": []}, node)

    def visit_desc_signature(self, node):
        return self.enter_myst_node({"type": "descSignature", "children": []}, node)

    def visit_desc_signature_line(self, node):
        return self.enter_myst_node({"type": "descSignatureLine", "children": []}, node)

    def visit_desc_sig_operator(self, node):
        return self.enter_myst_node({"type": "descSigOperator", "children": []}, node)

    def visit_desc_sig_punctuation(self, node):
        return self.enter_myst_node(
            {"type": "descSigPunctuation", "children": []}, node
        )

    def visit_desc_sig_space(self, node):
        return self.enter_myst_node({"type": "descSigSpace", "children": []}, node)

    def visit_desc_type(self, node):
        return self.enter_myst_node({"type": "descType", "children": []}, node)

    def visit_desc_type_parameter(self, node):
        return self.enter_myst_node({"type": "descTypeParameter", "children": []}, node)


for name in (
    "attention",
    "caution",
    "danger",
    "error",
    "hint",
    "important",
    "note",
    "tip",
    "warning",
):

    def visitor(self, node, name=name):
        return self.enter_myst_node(
            {"type": "admonition", "kind": name, "children": []}, node
        )

    setattr(MySTNodeVisitor, f"visit_{name}", visitor)
