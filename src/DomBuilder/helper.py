# import bs4
# from bs4 import BeautifulSoup, Tag, NavigableString
# import re

# def is_single_row_or_column_table(table):
#     """
#     Determine if an HTML table consists of only one row or one column.

#     Args:
#         table (bs4.element.Tag): A BeautifulSoup Tag object representing a table.

#     Returns:
#         bool: True if the table has only one row or one column; otherwise, False.
#     """
#     if not table or table.name != "table":
#         return False  # Ensure the provided element is a valid table.

#     # Retrieve all rows within the table.
#     rows = table.find_all("tr")

#     # Check if the table has exactly one row.
#     if len(rows) == 1:
#         return True

#     # Check if every row contains only one column (i.e., it's a single-column table).
#     first_row_columns = rows[0].find_all("td")
#     if len(first_row_columns) == 1:
#         return all(len(row.find_all("td")) == 1 for row in rows)

#     return False  # The table has multiple rows and columns.

# def get_element(node):
#     """
#     Generate a CSS-like selector for the given BeautifulSoup node.

#     Args:
#         node (bs4.element.Tag): The target node.

#     Returns:
#         str: A CSS selector representing the node's position.
#     """
#     # Initialize position counter for sibling elements of the same type.
#     position = 1
#     for previous_node in node.previous_siblings:
#         if isinstance(previous_node, bs4.element.Tag) and previous_node.name == node.name:
#             position += 1

#     # Return the node's name with its position if it's not the first child; otherwise, just the name.
#     return f'{node.name}:nth-of-type({position})' if position > 1 else node.name

# def is_single_text_node(node):
#     """
#     Check if a node contains exactly one direct text child.

#     Args:
#         node (bs4.element.Tag): The node to check.

#     Returns:
#         bool: True if the node has only one direct text child; otherwise, False.
#     """
#     if not isinstance(node, Tag):
#         return False
#     # Collect all direct text nodes within the node.
#     text_nodes = [child for child in node.children if isinstance(child, NavigableString)]
#     return len(text_nodes) == 1 and len(text_nodes[0].strip()) > 0

# def clean_text(input_string):
#     """
#     Normalize whitespace in the input string by collapsing multiple newlines and tabs.

#     Args:
#         input_string (str): The string to clean.

#     Returns:
#         str: The cleaned string with normalized whitespace.
#     """
#     # Replace multiple consecutive newline characters with a single newline.
#     cleaned_string = re.sub(r'\n+', '\n', input_string)
#     # Replace multiple consecutive tab characters with a single tab.
#     cleaned_string = re.sub(r'\t+', '\t', cleaned_string)
#     return cleaned_string.strip()

# def find_smallest_parent_with_extra_text(node):
#     """
#     Identify the nearest parent of the node that contains additional text beyond the node's own text.

#     Args:
#         node (bs4.element.Tag): The starting node.

#     Returns:
#         bs4.element.Tag or None: The closest parent tag with extra text, or None if not found.
#     """
#     # Traverse ancestors to find a parent with extra text content.
#     parent = node.find_parent(lambda x: x.name and x.get_text(strip=True) != node.get_text(strip=True))
#     return parent

# def find_smallest_parent_with_before_extra_text(node):
#     """
#     Locate the closest parent of the given node that contains at least one direct text node before the node.

#     Args:
#         node (bs4.element.Tag): The node to start from.

#     Returns:
#         bs4.element.Tag or None: The nearest parent tag with direct text before the node, or None if not found.
#     """
#     current = node.parent  # Begin with the immediate parent.

#     while current and isinstance(current, Tag):
#         # Iterate through direct children to find text nodes before the given node.
#         for child in current.children:
#             if child == node:
#                 break  # Stop if we've reached the original node.

#             if is_single_text_node(child):
#                 return current  # Found a parent with a valid text node before the original node.

#         current = current.parent  # Move up to the next ancestor.

#     return None  # No suitable parent found.

# def get_css_path(target_node):
#     """
#     Construct the CSS path of a specific node within a BeautifulSoup-parsed HTML document.

#     Args:
#         target_node (bs4.element.Tag): The node for which to determine the CSS path.

#     Returns:
#         str: The CSS path representing the node's position in the document.
#     """
#     if not isinstance(target_node, bs4.element.Tag):
#         return ''

#     path_elements = [get_element(target_node)]  # Start with the target node.
#     # Traverse ancestors to build the full path.
#     for parent in target_node.parents:
#         if parent.name == "[document]":
#             break
#         path_elements.insert(0, get_element(parent))

#     return ' > '.join(path_elements)

# def get_header_node(html_node):
#     """
#     Find the first header-like tag within the provided HTML node.

#     Args:
#         html_node (bs4.element.Tag): The HTML node to search within.

#     Returns:
#         bs4.element.Tag or None: The first header-like tag found, or None if not present.
#     """
#     if not isinstance(html_node, Tag):
#         return None

#     # Define a list of tags considered as headers.
#     header_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'b', 'strong']

#     # Search for the first occurrence of any header tag within the node.
#     header = html_node.find(header_tags)
#     if header:
#         return header

#     # If no header tags are found, recursively search through child tags.
#     for child in html_node.children:
#         if isinstance(child, Tag):
#             result = get_header_node(child)
#             if result:
#                 return result

#     return None  # No header-like tag found.
import bs4
from bs4 import BeautifulSoup
import re
def is_single_row_or_column_table(table):
    """
    Checks if an HTML table has only one row or one column.

    :param table: BeautifulSoup Tag object (table)
    :return: True if the table has only 1 row or 1 column, otherwise False
    """
    if not table or table.name != "table":
        return False  # ✅ Ensure it's a valid table

    # ✅ Get all rows
    rows = table.find_all("tr")

    # ✅ Check if there's only **one row**
    if len(rows) == 1:
        return True

    # ✅ Check if every row has only **one column** (i.e., it's a single-column table)
    first_row_columns = rows[0].find_all("td")
    if len(first_row_columns) == 1:
        return all(len(row.find_all("td")) == 1 for row in rows)  # Ensure every row has 1 column

    return False  # ✅ If neither condition is met, return False

def get_element(node):
    # for XPATH we have to count only for nodes with same type!
    length = 1
    for previous_node in list(node.previous_siblings):
        if isinstance(previous_node, bs4.element.Tag):
            length += 1
    if length > 1:
        return '%s:nth-child(%s)' % (node.name, length)
    else:
        return node.name

from bs4 import NavigableString


def isSingleTextNode(node):
    """Check if a node contains only one direct text child (not wrapped inside another tag)."""
    if not isinstance(node, Tag):
        return None
    text_nodes = [child.strip() for child in node.stripped_strings]
    if len(text_nodes) == 1 and len(text_nodes[0]) > 2:
        return True

    # if not isinstance(node, Tag):
    #     return False  # Not a valid Tag
    # for child in node.contents:
    #     if isinstance(child, NavigableString) and child.strip():  # Direct text
    #         return True
    # return False

def cleanText(input_string):
    # Replace multiple consecutive newline characters with a single newline
    # input_string = input_string.strip()
    cleaned_string = re.sub(r'\n+', '\n', input_string)
    cleaned_string = re.sub(r'\t+', '\t', cleaned_string)
    # print(cleaned_string)

    return cleaned_string
def find_smallest_parent_with_extra_text(node):
    # Find the first parent of the node that contains at least one text node
    parent_with_text = node.find_parent(lambda x: x.name and x.find(text=True) and x.get_text(strip=True) != node.get_text(strip=True))

    return parent_with_text

def find_smallest_parent_with_before_extra_text(node):
    """
    Find the closest parent of the given node that contains at least one direct text node *before* the given node.

    :param node: BeautifulSoup Tag object
    :return: The closest parent tag with direct text before the node, or None if not found.
    """
    current = node.parent  # Start from the immediate parent
    while current and isinstance(current, Tag):  # ✅ Traverse only valid tags
        # ✅ Iterate through direct children to find text before node
        for child in current.children:
            if child == node:
                break  # ✅ Stop searching when we reach node

            if isSingleTextNode(child):
                return current # ✅ Found a parent with a valid text node before node

        current = current.parent  # Move up to the next parent

    return None # ✅ No valid parent found

def find_before_nearest_text_node(node):
    """
    """
    parent,_ = find_smallest_parent_with_before_extra_text(node)
    if parent is None:
        return None
    else:
        previous = None
        for child in parent.children:
            if child == node:
                return previous
            
            if isSingleTextNode(child): 
                previous = child
            else:
                previous = None
        return None
            
def get_css_path(target_node):
    """
    Get the CSS path of a specific node in a BeautifulSoup parsed HTML document.
    
    Args:
        target_node (Tag): The target node whose CSS path is to be determined.
    
    Returns:
        str: The CSS path of the target node.
    """
    css_path = []
    if isinstance(target_node, bs4.Tag):

        css_path = [get_element(target_node)]  # Initialize CSS path list with node name
    else:
        css_path = []
    for parent in target_node.parents:
        if parent.name == "[document]":
            break
        css_path.insert(0, get_element(parent))
    return ' > '.join(css_path)




from bs4 import Tag, NavigableString

def isHeaderText(html_node):
    """
    Check if the HTML node is a header tag or directly contains a single header tag
    with only text as its content.

    Args:
        html_node (Tag): The HTML node to check.

    Returns:
        bool: True if the node is a header tag or directly contains exactly one header tag
              with matching text content, False otherwise.
    """
    # If the node itself is a header tag with only text
    if html_node.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        if html_node.text and html_node.text.strip():  # Check for non-empty string
            return True

    # Count the number of header tags in the node
    header_tags = html_node.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

    if len(header_tags) != 1:  # Return False if there are 0 or more than 1 header tags
        return False

    # Check if the single header's text matches the node's text
    header_tag = header_tags[0]
    header_string = ''.join(header_tag.stripped_strings)
    node_string = ''.join(html_node.stripped_strings)
    # print(header_string)
    # print("++++++++++++++")
    # print(node_string)

    if header_string == node_string:
        return True

    return False

def getHeaderNode(html_node):
    """
    Finds the first tag that contains exactly one direct text node.

    :param html_node: BeautifulSoup Tag object
    :return: First tag that contains only one direct text node, or None if not found.
    """
    if not isinstance(html_node, Tag):
        return None
    header_text = html_node.fin
    for child in html_node.children:  # ✅ Only direct children (not all descendants)
        if isinstance(child, Tag):
            if isHeaderText(html_node):
                return html_node
            # ✅ Get all direct text nodes inside the child
            text_nodes = [sub_child.strip() for sub_child in child.stripped_strings]
            # ✅ Check if the tag has exactly ONE text node
            if len(text_nodes) == 1:
                return child  # ✅ Return this tag
            elif len(text_nodes) > 1:
                return getHeaderNode(child)

    return None