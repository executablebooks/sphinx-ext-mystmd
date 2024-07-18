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
sphinx-build -b myst . _build/myst
```

> [!WARNING]
> This extension is a literal work-in-progress; some things don't work.
> The intention is to get _something_ on the page before we finalize it.
