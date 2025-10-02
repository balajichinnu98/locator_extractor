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
    Generate relative XPath using tag and attributes (id, name, class)
    e.g. //div[@id='company'], //input[@name='username']
    Falls back to tag only if no attributes.
    """
    if element is None or element.name == '[document]':
        return ''

    tag = element.name

    # Priority attributes for XPath
    if element.get('id'):
        return f"//{tag}[@id='{element.get('id')}']"
    if element.get('name'):
        return f"//{tag}[@name='{element.get('name')}']"
    if element.get('class'):
        # use first class only for xpath
        class_name = element.get('class')[0]
        return f"//{tag}[contains(@class, '{class_name}')]"

    # fallback: just tag name
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

def extract_locators_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    locators_list = []

    # List of interactive tags to keep
    interactive_tags = ['input', 'button', 'select', 'textarea', 'a', 'label']

    for element in soup.find_all(True):
        tag = element.name

        # Filter: only interactive tags OR elements with tabindex attribute
        if tag not in interactive_tags and not element.has_attr('tabindex'):
            continue

        # For <a> tags, ensure it has href attribute to be interactive
        if tag == 'a' and not element.get('href'):
            continue

        locator = {}

        # id
        if element.get('id'):
            locator['id'] = element.get('id')

        # name
        if element.get('name'):
            locator['name'] = element.get('name')

        # class name (first class only)
        classes = element.get('class')
        if classes:
            locator['class_name'] = classes[0]

        # css selector
        locator['css_selector'] = get_css_selector(element)

        # xpath (relative with attributes)
        locator['xpath'] = get_relative_xpath(element)

        # tag name
        locator['tag_name'] = tag

        # link text & partial link text - only for <a> tags with text
        if tag == 'a' and element.string and element.string.strip():
            text = element.string.strip()
            locator['link_text'] = text
            locator['partial_link_text'] = text[:max(1, len(text)//2)]  # half text as partial

        locators_list.append(locator)

    return locators_list

if __name__ == '__main__':
    app.run(debug=True)