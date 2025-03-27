from treelib import Tree, Node
from bs4 import BeautifulSoup, Tag
from . import helper


class SoupNode(Node):
    def __init__(self, number = 0, text = None, bs_tag=None, node_identifier=None, css_path=None, is_repetitive_node=False, is_title = False):
        """
        Custom node that extends treelib's Node with additional attributes.
        Can be initialized directly from a BeautifulSoup tag.
        """
        identifier = 'root'
        self.hrefs = []  # Initialize an empty list to store hrefs

        if bs_tag:
            css_path = helper.get_css_path(bs_tag)
            tag = bs_tag.name
            if node_identifier:
                self.number = node_identifier.get_next_id(css_path)
            if not is_title:
                identifier = css_path
                
            text = helper.cleanText(bs_tag.get_text(strip=True)) if bs_tag.text else ''
            # Collect all href attributes from the tag and its descendants
            for element in bs_tag.find_all(href=True):
                self.hrefs.append(element['href'])

        else:
            tag = None
            text = ''

        super().__init__(identifier=identifier)
        self.tag = tag
        self.text = text
        self.is_repetitive_node = is_repetitive_node
    def traverse_up(self, level_distance):
        """
        Traverse up the tree to find an ancestor at a given level distance.
        """
        target_node = self
        while level_distance and target_node.parent:
            target_node = target_node.parent
            level_distance -= 1
        return target_node
    def __repr__(self):
        return f"<SoupNode tag={self.tag}, id={self.identifier}, text={self.text[:30]}...>"
