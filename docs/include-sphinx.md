---
title: Include Sphinx Projects in MyST
subtitle: Gradually Upgrade Sphinx-based Projects to MyST 
short_title: Include in MyST
description: Gradually upgrade Sphinx projects to the MyST engine through the MyST build engine
---

## Configure Your Project

The Sphinx `conf.py` for your project should include `sphinx-ext-mystmd`. If your Sphinx project lives under `sphinx`, then your `conf.py` might look like.
:::{code} python
:filename: sphinx/conf.py

extensions = [
    "sphinx_ext_mystmd"
]
:::

## Build the Sphinx Project

```shell
sphinx-build -b myst sphinx myst-asts
```

## Configure the MyST Project

:::{code} yaml
:filename: myst.yml

version: 1
project:
  toc:
    - file: index.md
    - pattern: myst-asts/**.myst.json
site:
  template: book-theme
:::

## Build the MyST Project
```shell
myst start
```




