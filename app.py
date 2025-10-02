from flask import Flask, request, jsonify, render_template
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/extract-locators', methods=['POST'])
def extract_locators():
    html_content = request.json.get('html', '')
    if not html_content:
        return jsonify({'error': 'No HTML content provided'}), 400

    locators = extract_locators_from_html(html_content)
    return jsonify(locators)

def get_relative_xpath(element):
    """
    Generate relative XPath using id, name, placeholder, aria-label, or visible text.
    Ignores class for better reliability.
    """
    if element is None or element.name == '[document]':
        return ''

    tag = element.name

    if element.get('id'):
        return f"//{tag}[@id='{element.get('id')}']"
    if element.get('name'):
        return f"//{tag}[@name='{element.get('name')}']"
    if element.get('placeholder'):
        return f"//{tag}[@placeholder='{element.get('placeholder')}']"
    if element.get('aria-label'):
        return f"//{tag}[@aria-label='{element.get('aria-label')}']"

    # fallback: use visible text if available
    text = element.get_text(strip=True)
    if text:
        return f"//{tag}[normalize-space()='{text}']"

    # final fallback: just tag name
    return f"//{tag}"

def get_css_selector(element):
    """
    Generate a CSS selector:
    - if id exists: #id
    - else tag.class1.class2
    - else tag only
    """
    if element is None or element.name == '[document]':
        return ''

    if element.get('id'):
        return f"#{element.get('id')}"

    selector = element.name
    classes = element.get('class')
    if classes:
        selector += '.' + '.'.join(classes)
    return selector

def get_element_label(element):
    """
    Generate a human-readable label for an element.
    Uses id, name, placeholder, aria-label, value, or visible text (including nested tags).
    """
    if element.get("id"):
        return element.get("id")
    if element.get("name"):
        return element.get("name")
    if element.get("placeholder"):
        return element.get("placeholder")
    if element.get("aria-label"):
        return element.get("aria-label")
    if element.get("value"):
        return element.get("value")

    text = element.get_text(strip=True)
    if text:
        return text

    if element.name == "input" and element.get("type"):
        return f"{element.get('type')}-input"
    if element.name == "select":
        return "select"
    if element.name == "textarea":
        return "textarea"

    return element.name

def extract_locators_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    locators_list = []

    interactive_tags = ['input', 'button', 'select', 'textarea', 'a', 'label', 'i', 'span']

    for element in soup.find_all(True):
        tag = element.name

        # Skip non-interactive elements without id/name/class/tabindex
        if tag not in interactive_tags and not element.has_attr('tabindex'):
            continue
        if tag == 'a' and not element.get('href'):
            continue

        locator = {}
        locator['label'] = get_element_label(element)
        locator['tag_name'] = tag

        if element.get('id'):
            locator['id'] = element.get('id')
        if element.get('name'):
            locator['name'] = element.get('name')
        if element.get('class'):
            locator['class_name'] = element.get('class')[0]  # first class only

        locator['css_selector'] = get_css_selector(element)
        locator['xpath'] = get_relative_xpath(element)

        locators_list.append(locator)

    return locators_list

if __name__ == '__main__':
    app.run(debug=True)
