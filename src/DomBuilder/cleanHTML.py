from bs4 import BeautifulSoup
import re

# Define a dictionary of tags to remove based on class or tag name
tags_to_remove = {
    'style': 'name',
    # 'header': 'name',
    # 'footer': 'name',
    'nav': 'name',
    # 'script': 'name',
    'meta': 'name',
    # 'head': 'name',
    'nav': 'class',
    'footer': 'name',
    'select': 'name'
    # 'aside': 'class',
    # 'figure': 'name',
    # 'figcaption': 'name',
    # 'br': 'name',
    # 'hr': 'name',
}
def clean_html_comments(html_string):
    # Use regular expression to find and remove HTML comments
    cleaned_html = re.sub(r'<!--.*?-->', '', html_string, flags=re.DOTALL)
    
    return cleaned_html

def clean_empty_lines(input_string):
    # Split the input string into lines
    lines = input_string.splitlines()

    # Filter out empty lines
    non_empty_lines = [line for line in lines if line.strip()]

    # Join the non-empty lines back together with '\n' separator
    cleaned_string = '\n'.join(non_empty_lines)

    return cleaned_string


def remove_tags(soup, tags_to_remove = tags_to_remove):
    # Iterate through the tags in the dictionary and remove them
    for tag, identifier in tags_to_remove.items():
        if identifier == 'name':
            # Remove tags by tag name
            for matched_tag in soup.find_all(tag):
                matched_tag.decompose()
        elif identifier == 'class':
            # Remove tags by class attribute
            for matched_tag in soup.find_all(class_=tag):
                matched_tag.decompose()
    # # Find all tags with no content (i.e., empty tags)
    # empty_tags = [tag for tag in soup.find_all() if not tag.get_text(strip=True)]

    # # Remove the empty tags from the parsed HTML
    # for empty_tag in empty_tags:
    #     empty_tag.decompose()


    return soup
inline_elements = [
    "span",
    "a",
    "sup",
    "strong",
    "em",
    "i",
    "b",
    "code",
    "cite",
    "abbr",
    "time"
    # Add more inline elements as needed
]

def unwrap_tags(soup, tags=inline_elements):
    for tag in tags:
        for element in soup.find_all(tag):
            # Find the index of the element within its parent's contents
            index = element.parent.contents.index(element)
            # # Insert a space before the element
            # element.insert_after(", ")
            # Unwrap the element
            element.unwrap()
    return soup
def convert_script_to_html_node(script_tag):
    """
    Check if a <script> tag contains HTML content as a string in a JavaScript variable,
    wrap all the content (relevant and non-relevant) in a <div>, and return that as a BeautifulSoup node.
    :param script_tag: BeautifulSoup object representing a <script> tag.
    :return: BeautifulSoup node (wrapped HTML content) if HTML is found, False otherwise.
    """
    # Regular expression to extract all HTML-like content inside JavaScript variables
    html_pattern = r'"(<[a-z][\s\S]*?>)"'  # Matches HTML content inside quotes (non-greedy matching)

    # Check if the script tag has a string and contains HTML-like content
    if script_tag.string:
        # Find all matches of HTML content inside JavaScript variables
        matches = re.findall(html_pattern, script_tag.string)

        if matches:
            # Join all matched HTML strings and wrap them in a <div>
            combined_html = ''.join(matches)
            wrapped_html = f"<div>{combined_html}</div>"

            # Convert the combined HTML into a BeautifulSoup node
            html_node = BeautifulSoup(wrapped_html, 'html.parser')
            html_node.div['type_of_section'] = 'script'  # Add the attribute to the <div> tag
            return html_node
    return False

def clean_html(soup, tags_to_remove=tags_to_remove):
    # Remove HTML comments
    html_string = str(soup)
    cleaned_html = clean_html_comments(html_string)

    # Clean empty lines
    cleaned_html = clean_empty_lines(cleaned_html)
    cleaned_html = re.sub(r'::markup', '', cleaned_html, flags=re.DOTALL)


    # Parse the cleaned HTML with BeautifulSoup
    soup = BeautifulSoup(cleaned_html, 'html.parser')
    # for data in soup(['nav', 'footer', 'header']):
    #     # Remove tags
    #     data.decompose()
 

    soup =  unwrap_tags(soup, tags = ['font'])
    # for br_tag in soup.find_all('br'):
    #     br_tag.unwrap()
    # for br_tag in soup.find_all('hr'):
    #     br_tag.unwrap()
    # for text_node in soup.find_all(text=True):
    #     text_node.replace_with(text_node.replace("&lrm;", "").replace("&rlm;", ""))


    # subclasses = ['nav', 'dropdown', 'header','footer']
    # for subclass in subclasses:
    #     for matched_tag in soup.find_all(class_=lambda x: x and (subclass in x.split() or any(re.match(r'.*-' + subclass + r'\b', c) for c in x.split()) or any(re.match(subclass + r'.-*', c) for c in x.split()))):
    #         matched_tag.decompose()
    for script in soup.find_all('script'):
        result = convert_script_to_html_node(script)
        if result:
            # Remove the <script> tag and insert the new content in its place
            print(result)
            script.insert_before(result)  # Insert the new content before the <script> tag
        script.decompose()  # Remove the <script> tag completely

    if tags_to_remove:
        soup = remove_tags(soup, tags_to_remove)


    html_string = str(soup)

    cleaned_html = clean_empty_lines(html_string)


    # Parse the cleaned HTML with BeautifulSoup
    soup = BeautifulSoup(cleaned_html, 'html.parser')

    return soup
