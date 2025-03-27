import bs4
from bs4 import BeautifulSoup, Tag, NavigableString
import re

def is_single_row_or_column_table(table):
    """
    Checks if an HTML table has only one row or one column.
    
    :param table: BeautifulSoup Tag object (table)
    :return: True if the table has only 1 row or 1 column, otherwise False
    """
    if not table or table.name != "table":
        return False  # Ensure it's a valid table

    rows = table.find_all("tr")
    
    # Check if there's only one row
    if len(rows) == 1:
        return True
    
    # Check if every row has only one column
    first_row_columns = rows[0].find_all("td")
    if len(first_row_columns) == 1:
        return all(len(row.find_all("td")) == 1 for row in rows)
    
    return False

def get_element(node):
    """Get the CSS selector for a node by determining its position among siblings."""
    length = 1
    for previous_node in list(node.previous_siblings):
        if isinstance(previous_node, bs4.element.Tag):
            length += 1
    return f'{node.name}:nth-child({length})' if length > 1 else node.name

def isSingleTextNode(node):
    """Check if a node contains only one direct text child."""
    if not isinstance(node, Tag):
        return None
    text_nodes = [child.strip() for child in node.stripped_strings]
    return len(text_nodes) == 1 and len(text_nodes[0]) > 2

def cleanText(input_string):
    """Clean up text by removing excessive newlines and tabs."""
    cleaned_string = re.sub(r'\n+', '\n', input_string)
    cleaned_string = re.sub(r'\t+', '\t', cleaned_string)
    return cleaned_string

def find_smallest_parent_with_extra_text(node):
    """Find the first parent of a node that contains extra text beyond the node itself."""
    return node.find_parent(lambda x: x.name and x.find(text=True) and x.get_text(strip=True) != node.get_text(strip=True))

def find_smallest_parent_with_before_extra_text(node):
    """
    Find the closest parent of the given node that contains at least one direct text node *before* the given node.
    
    :param node: BeautifulSoup Tag object
    :return: The closest parent tag with direct text before the node, or None if not found.
    """
    current = node.parent
    while current and isinstance(current, Tag):
        for child in current.children:
            if child == node:
                break
            if isSingleTextNode(child):
                return current
        current = current.parent
    return None

def get_css_path(target_node):
    """Get the full CSS path for a given node in the HTML document."""
    css_path = []
    if isinstance(target_node, bs4.Tag):
        css_path = [get_element(target_node)]
    for parent in target_node.parents:
        if parent.name == "[document]":
            break
        css_path.insert(0, get_element(parent))
    return ' > '.join(css_path)

def getHeaderNode(html_node):
    """
    Finds the first tag that contains exactly one direct text node.
    
    :param html_node: BeautifulSoup Tag object
    :return: First tag that contains only one direct text node, or None if not found.
    """
    if not isinstance(html_node, Tag):
        return None
    
    for child in html_node.children:
        if isinstance(child, Tag):
            text_nodes = [sub_child.strip() for sub_child in child.stripped_strings]
            if len(text_nodes) == 1:
                return child
            elif len(text_nodes) > 1:
                return getHeaderNode(child)
    return None
