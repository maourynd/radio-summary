import os

import bleach
from jinja2 import Environment, FileSystemLoader
from premailer import transform

def render_html(summary_html):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env = Environment(loader=FileSystemLoader(current_dir))
    print(current_dir)
    template = env.get_template('template.html')
    html_content = template.render(summary=summary_html)
    return html_content

def sanitize_html(html_content):
    allowed_tags = ['h1', 'h2', 'h3', 'p', 'ul', 'li', 'strong', 'em', 'br']
    allowed_attrs = {}
    cleaned_html = bleach.clean(html_content, tags=allowed_tags, attributes=allowed_attrs, strip=True)
    return cleaned_html

def inline_css(html_content):
    return transform(html_content)