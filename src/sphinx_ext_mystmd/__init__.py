from sphinx.builders import Builder
import json
import os.path
import pathlib
import hashlib

from .transform import MySTNodeVisitor


class MySTBuilder(Builder):
    name = "myst"

    def slugify(self, path):
        return path.replace("/", "-")

    def _get_xref_path(self, doc_name):
        target_stem = self.slugify(doc_name)
        return os.path.join(self.outdir, f"{target_stem}.json")

    def _get_outdated_docs(self):
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

    def get_outdated_docs(self):
        it = self._get_outdated_docs()

        for item in it:
            yield item
            break
        else:
            return

        yield from it

    def prepare_writing(self, docnames):
        print(f"About to write {docnames}")

    def write_doc(self, docname, doctree):
        visitor = MySTNodeVisitor(doctree)
        doctree.walkabout(visitor)

        slug = self.slugify(docname)
        xref_path = self._get_xref_path(docname)

        json_xref_dst = pathlib.Path(xref_path)
        json_xref_dst.parent.mkdir(exist_ok=True)

        md_frag_dst = json_xref_dst.with_suffix(".md")
        json_frag_dst = json_xref_dst.with_suffix(".frag.json")

        with open(self.env.doc2path(docname), "rb") as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()

        with open(json_xref_dst, "w") as f:
            json.dump(
                {
                    "kind": "Article",
                    "sha256": sha256,
                    "slug": slug,
                    "location": f"/{docname}",
                    "dependencies": [],
                    "frontmatter": {},
                    "mdast": visitor.result,
                    "references": {"cite": {"order": [], "data": {}}},
                },
                f,
                indent=2,
            )

        with open(json_frag_dst, "w") as f:
            assert visitor.result["type"] == "root"
            first_root_child = visitor.result["children"][0]
            fragment = {"mdast": first_root_child}
            json.dump(fragment, f, indent=2)

        with open(md_frag_dst, "w") as f:
            f.write(
                f"""
:::{{mdast}} {json_frag_dst.name}#mdast

"""
            )

    # xref impl is done at build time ... we need to embed and then use non-xref links to refer to _that_ AST

    def finish(self):
        references = [
            {"kind": "page", "url": f"/{slug}", "data": f"/{slug}.json"}
            for slug in (self.slugify(n) for n in self.env.found_docs)
        ]
        xref = {"version": "1", "myst": "1.2.9", "references": references}
        with open(os.path.join(self.outdir, "myst.xref.json"), "w") as f:
            json.dump(xref, f, indent=2)

    def get_target_uri(self, docname, typ=None):
        return self.slugify(docname)


def setup(app):
    app.add_builder(MySTBuilder)
