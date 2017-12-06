setup(
    ...
    entry_points = {
        'sphinx.html_themes': [
            'name_of_theme = conduce_theme',
        ]
    },
    ...
)
# 'your_package.py'
from os import path

def setup(app):
    app.add_html_theme('conduce_theme', path.abspath(path.dirname(__file__)))
