# sphinx-ext-mystmd

A Sphinx extension to build MyST-MD AST from a Sphinx project. This can be used for:

1. Embedding API documentation in a MyST project
2. Providing MyST xref support for a deployed Sphinx project (gradual transition)

Add this extension to your `conf.py` e.g.
```python
extensions = ["sphinx_ext_mystmd"]
```
in order to be able to use the `myst` builder, e.g.

```shell
sphinx-build -b myst . <BUILDDIR>
```

The generated `.myst.json` files in `<BUILDDIR>/content` can be added to your TOC e.g. using a `pattern` entry, e.g.

```yaml
project:
  toc:
    - file: index.md
    - title: Sphinx Build
      children:
        - pattern: <BUILDDIR>/content/**.myst.json

```

You can also serve the `myst.xref.json` from your Sphinx deployment to enable MyST xrefs.

> [!WARNING]
> This extension is a literal work-in-progress; some things don't work.
> The intention is to get _something_ on the page before we finalize it.
