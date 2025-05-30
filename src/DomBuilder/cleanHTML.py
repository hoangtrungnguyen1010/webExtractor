from bs4 import BeautifulSoup, NavigableString, Tag
import re
import copy
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
def wrap_header_and_siblings(soup, header_tags=("h1", "h2", "h3", "h4", "h5", "h6")):
    """
    Wrap headers and their subsequent siblings in a <div>,
    until encountering another header.
    
    Args:
        soup (BeautifulSoup): The soup object containing the HTML structure.
        header_tags (tuple): A tuple of header tags to consider.
    
    Returns:
        None: The function modifies the soup in place.
    """
    # First, convert the HTML to string and then parse it again
    # This ensures we have a clean starting point
    html_str = str(soup)
    new_soup = BeautifulSoup(html_str, 'html.parser')
    
    # Find all headers in the new soup
    headers = new_soup.find_all(header_tags)
    
    # Keep track of which elements we've processed
    processed = set()
    
    # Create sections for each header
    for header in headers:
        # Skip if already processed
        if header in processed:
            continue
        
        # Create a container div
        container = new_soup.new_tag("div")
        
        # Insert the container right before the header
        header.insert_before(container)
        
        # Move header into container
        container.append(header)
        processed.add(header)
        
        # Get next siblings until another header
        next_elem = container.next_sibling
        while next_elem:
            next_next = next_elem.next_sibling  # Store before we modify
            
            # If it's a header, stop
            if isinstance(next_elem, Tag) and next_elem.name in header_tags:
                break
            
            # Move this element into the container
            container.append(next_elem)
            
            # Update next element
            next_elem = next_next
    
    # Replace the original soup's contents with the new soup's contents
    soup.clear()
    for element in new_soup.contents:
        soup.append(copy.copy(element))

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

def unwrap_siblings_of_text(node):
    """
    Unwraps other sibling elements when a node contains both direct text
    and other HTML elements, so that the direct parent of text only contains text.
         
    Args:
        node: A Beautiful Soup node to modify.
             
    Returns:
        None: The function modifies the node in place.
    """
    if not node or not hasattr(node, 'contents'):
        return
         
    # Check if we have both text nodes and HTML elements
    has_text = any(isinstance(child, NavigableString) and child.strip() for child in node.contents)
    has_elements = any( isinstance(child, Tag) and child.get_text().strip() for child in node.contents)
         
    if not (has_text and has_elements):
        # No need to process if there's not a mix of content types
        return
         
    # Collect all non-text elements first, then unwrap them
    # This avoids modifying the list while iterating
    elements_to_unwrap = []
    print("------------------------")
    print(node)
    print("++++++++++++++++++++++++++")

    for child in node.contents:
        if isinstance(child, Tag):
            print(child.get_text())
            elements_to_unwrap.append(child)
    
    # Now unwrap all collected elements
    for element in elements_to_unwrap:
        element.unwrap()
    print(node)
    print("------------------")
def getNumberTextNode(node):
    """Check if a node contains only one direct text child (not wrapped inside another tag)."""
    if not isinstance(node, Tag):
        return None
    text_nodes = [child.strip() for child in node.stripped_strings]
    return len(text_nodes)

def process_tags_with_mixed_content(soup):
    """
    Searches through an HTML soup to find all tags that directly contain both
    text nodes and other HTML elements, then processes them using the 
    unwrap_siblings_of_text function.
    
    Args:
        soup: A BeautifulSoup object representing the HTML document.
        
    Returns:
        int: The number of tags that were processed.
    """
    processed_count = 0
    
    # Find all tags in the document
    all_tags = soup.find_all(True)
    
    list_node_to_modify = []
    for tag in all_tags:
        # Check if the tag has contents
        if hasattr(tag, 'contents') and tag.contents and getNumberTextNode(tag) < 50:
            # Check for direct text nodes (non-empty after stripping)
            has_text = any(
                isinstance(child, NavigableString) and child.strip() 
                for child in tag.contents
            )
            
            # Check for direct HTML element children
            has_elements = any(
                isinstance(child, Tag) and child.get_text().strip() 
                for child in tag.contents
            )
            
            # If the tag has both direct text and HTML elements, process it
            if has_text and has_elements:
                # print(tag.get_text())
                list_node_to_modify.append(tag)
    list_node_to_modify.sort(key=lambda tag: len(tag.get_text()))
    for node in list_node_to_modify:
        while True:
            unwrap_siblings_of_text(node)
            has_text = any(
                isinstance(child, NavigableString) and child.strip() 
                for child in node.contents
            )
            
            # Check for direct HTML element children
            has_elements = any(
                isinstance(child, Tag) and child.get_text().strip() 
                for child in node.contents
            )
            
            # If the tag has both direct text and HTML elements, process it
            if not (has_text and has_elements):
                break

    return processed_count
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
    
    wrap_header_and_siblings(soup)
    # print(soup)
    for script in soup.find_all('script'):
        result = convert_script_to_html_node(script)
        if result:
            # Remove the <script> tag and insert the new content in its place
            script.insert_before(result)  # Insert the new content before the <script> tag
        script.decompose()  # Remove the <script> tag completely

    if tags_to_remove:
        soup = remove_tags(soup, tags_to_remove)

    process_tags_with_mixed_content(soup)
    html_string = str(soup)

    cleaned_html = clean_empty_lines(html_string)


    # Parse the cleaned HTML with BeautifulSoup
    soup = BeautifulSoup(cleaned_html, 'html.parser')

    return soup
