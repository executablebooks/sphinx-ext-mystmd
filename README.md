# sphinx-ext-mystmd

A Sphinx extension to build MyST-MD AST from a Sphinx project.

Add this extension to your `conf.py` e.g.
```python
extensions = ["sphinx_ext_mystmd"]
```
in order to be able to use the `myst` builder, e.g.

```shell
sphinx-build -b myst . _build/myst
```
