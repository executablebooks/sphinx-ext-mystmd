from sphinx.builders import Builder
from sphinx.util import logging

import json
import os.path
import pathlib
import hashlib

from .transform import MySTNodeVisitor
from .utils import to_text, find_by_type, breadth_first_walk


logger = logging.getLogger(__name__)


class MySTBuilder(Builder):
    name = "myst"

    def _slugify(self, path):
        return path.replace("/", "-")

    def _get_xref_path(self, doc_name):
        target_stem = self._slugify(doc_name)
        return os.path.join(self.outdir, "content", f"{target_stem}.myst.json")

    def prepare_writing(self, docnames):
        logger.info(f"About to write {docnames}")

    def get_outdated_docs(self):
        for docname in self.env.found_docs:
            if docname not in self.env.all_docs:
                yield docname
                continue
            target_path = self._get_xref_path(docname)
            try:
                targetmtime = os.path.getmtime(target_path)
            except Exception:
                targetmtime = 0
            try:
                srcmtime = os.path.getmtime(self.env.doc2path(docname))
                if srcmtime > targetmtime:
                    yield docname
            except OSError:
                # source doesn't exist anymore
                pass

    def write_doc(self, docname, doctree):
        visitor = MySTNodeVisitor(doctree)
        doctree.walkabout(visitor)
        slug = self._slugify(docname)
        xref_path = self._get_xref_path(docname)

        json_xref_dst = pathlib.Path(xref_path)
        json_xref_dst.parent.mkdir(exist_ok=True)

        with open(self.env.doc2path(docname), "rb") as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()
        title = to_text(next(find_by_type("heading", visitor.result)))
        with open(json_xref_dst, "w") as f:
            json.dump(
                {
                    "kind": "Article",
                    "sha256": sha256,
                    "slug": slug,
                    "location": f"/{docname}",
                    "dependencies": [],
                    "frontmatter": {"title": title, "content_includes_title": True},
                    "mdast": visitor.result,
                    "references": {"cite": {"order": [], "data": {}}},
                },
                f,
                indent=2,
            )

    def _xref_kind_for_node(self, node):
        if node['type'] == 'container':
            return node.get('kind', 'figure')
        if "kind" in node:
            return f"{node['type']}:{node['kind']}"
        return node["type"]

    def _get_written_target_references(self, doc):
        path = self._get_xref_path(doc)
        slug = self._slugify(doc)

        with open(path, "r") as f:
            data = json.load(f)

        mdast = data["mdast"]
        for node in breadth_first_walk(mdast):
            if "identifier" in node:
                yield {
                    "identifier": node["identifier"],
                    "kind": self._xref_kind_for_node(node),
                    "data": f"/{slug}.json",
                    "url": f"/{slug}",
                }

    def finish(self):
        page_references = [
            {
                "kind": "page",
                "url": f"/{self._slugify(n)}",
                "data": self._get_xref_path(n),
            }
            for n in self.env.found_docs
        ]
        target_references = [
            ref
            for refs in (
                self._get_written_target_references(n) for n in self.env.found_docs
            )
            for ref in refs
        ]
        references = [*page_references, *target_references]

        xref = {"version": "1", "myst": "1.2.9", "references": references}
        with open(os.path.join(self.outdir, "myst.xref.json"), "w") as f:
            json.dump(xref, f, indent=2)

    def get_target_uri(self, docname, typ=None):
        return self._slugify(docname)