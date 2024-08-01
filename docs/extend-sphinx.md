---
title: Extend Sphinx Projects to Declare MyST References
subtitle: Add richer integration between existing Sphinx projects and the MyST ecosystem
short_title: Reference from MyST
description: Add richer integration between existing Sphinx projects and the MyST ecosystem by declaring MyST xref information
---

## Configure Your Project

The Sphinx `conf.py` for your project should include `sphinx-ext-mystmd`. If your Sphinx project lives in the working directory, then your `conf.py` might look like.
:::{code} python
:filename: conf.py

extensions = [
    "sphinx_ext_mystmd"
]
html_extra_path = ["./myst-build"]
:::

## Build the MyST Metadata

```shell
sphinx-build -b myst . ./myst-build
```

## Build the HTML Deployment

```shell
sphinx-build -b html . ./html
```

The published project now includes the xref information in the public directory.
