from .builder import MySTBuilder


def setup(app):
    app.add_builder(MySTBuilder)
