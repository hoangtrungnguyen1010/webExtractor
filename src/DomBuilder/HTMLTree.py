from .soupNode import SoupNode
from treelib import Tree
from . import helper
from .cleanHTML import clean_html

from bs4 import Tag
MEDIA_TAGS = ['img', 'audio', 'video', 'embed', 'source', 'svg']

class NodeIdentifier:
    def __init__(self):
        self.counter = 1  # Initialize the counter to start from 1
        self.number_csspath_mapping = {}
        
    def get_next_id(self, csspath):
        node_id = self.counter
        self.counter += 1
        self.number_csspath_mapping[node_id] = csspath
        return node_id
    
    def get_csspath(self, number):
        return self.number_csspath_mapping[number]
    
class HTMLTree:
    def __init__(self, soup):
        self.soup = clean_html(soup)
        self.tree = Tree()
        self.node_identifier = NodeIdentifier()
        self.build_tree()

    def mark_sections(self):
        """Identify and mark important sections like tables, lists, and media elements."""
        tables = self.soup.find_all('table')
        
        for table in tables:
            if helper.is_single_row_or_column_table(table):
                continue
            
            table['type_of_section'] = 'table'

                
        media_tags = ['img', 'audio', 'video', 'embed', 'source', 'svg']
        for tag in media_tags:
            media_elements = self.soup.find_all(tag)
            for media in media_elements:
                media_section = helper.find_smallest_parent_with_extra_text(media)
                if media_section:
                    media_section['type_of_section'] = 'media'

        lists = self.soup.find_all(['ul', 'ol'])
        
        for lst in lists:
            lst['type_of_section'] = 'list'
            lst['is_repetitive'] = True
            items = lst.find_all('li')
            for item in items:
                if isinstance(item, Tag) and not item.get('type_of_section') and not helper.isSingleTextNode(item):
                    item['type_of_section'] = 'list_item'


    def rank_nodes(self, node, rank=1):
        if not isinstance(node, Tag):
            return rank
        
        current_rank = rank
        
        if isinstance(node, Tag) and (helper.isHeaderText(node) or node.attrs.get('header')):
            node['rank'] = current_rank
            current_rank += 1
            return current_rank
        
        if isinstance(node, Tag) and not node.attrs.get('rank') and helper.isSingleTextNode(node):
            node['rank'] = current_rank
            return current_rank
        
        if node.attrs.get('type_of_section'):
            header_nodes = None
            
            if node.attrs.get('type_of_section') in ['media', 'list_item', 'script']:
                header_nodes = helper.getHeaderNode(node)
                if header_nodes:
                    header_nodes['rank'] = current_rank
                    current_rank += 1
            
            for child in node.children:
                if isinstance(child, Tag):
                    if header_nodes and child is header_nodes:
                        continue
                    if helper.isSingleTextNode(child):
                        child['rank'] = current_rank
                    else:
                        current_rank += 1

                        current_rank = self.rank_nodes(child, current_rank)
        else:
            for child in node.children:
                current_rank = self.rank_nodes(child, current_rank)
        
        return current_rank
    
    def top_down(self, node, current_node, current_rank=1):
        """Recursively traverse the tree top-down and build structure."""
        if not isinstance(node, Tag):  # ✅ Skip text nodes
            return None, None,None

        if not current_node:
            return None, None, None

        if node.attrs.get('rank') and helper.isSingleTextNode(node):
            level_distance = current_rank - int(node['rank'])
            new_node = SoupNode(bs_tag=node, node_identifier = self.node_identifier)
            parent = None
            if level_distance <= -1:
                parent = current_node

            if level_distance >= 0:
                parent = self.traverse_up(current_node.identifier, level_distance + 1)

            self.tree.add_node(new_node, parent=parent.identifier)

            current_node = new_node
            current_rank = int(node['rank'])
            return current_node, current_rank

        for child in node.children:
            if isinstance(child, Tag):
                tempt, rank= self.top_down(child, current_node, current_rank)
                if tempt:
                    current_node = tempt
                    current_rank = rank
                    
        return None, None
                
    def build_tree(self):
        """Construct the tree from the BeautifulSoup object."""
        self.mark_sections()
        self.rank_nodes(self.soup)
        title_node = self.soup.find('title')
        
        if title_node:
            root_node = SoupNode(bs_tag=title_node, is_title= True, node_identifier = self.node_identifier)
            self.tree.add_node(root_node)
            body_node = self.soup.find('body')
            if body_node:
                for child in body_node.children:
                    if isinstance(child, Tag):
                        self.top_down(child, root_node)

    def show_tree(self):
        """Display the tree structure with ASCII characters."""
        self.tree.show(line_type="ascii")

    def traverse_up(self, node_identifier, level_distance):
        """
        Traverse up the tree to find an ancestor at a given level distance.
        """
        current_node = self.tree.get_node(node_identifier)
        if not current_node:
            return None 
        
        while level_distance > 0:
            parent_node = self.tree.parent(current_node.identifier)
            if not parent_node:
                break
            current_node = parent_node
            level_distance -= 1
        return current_node
    
    def print_tree(self, node_id='root', prefix='', last=True):
        node = self.tree.get_node(node_id)
        
        if not node:
            return

        print(prefix + ("└── " if last else "├── ") + str(node.number) + ":" + node.text)

        children = list(self.tree.children(node.identifier))
        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            self.print_tree(child.identifier, prefix + ("    " if last else "│   "), is_last)
            
    def get_string_tree(self, node_id='root', prefix='', last=True, result=None):
        # Initialize the result string if it's the first call
        if result is None:
            result = ""

        node = self.tree.get_node(node_id)
        
        if not node:
            return result

        # Append the current node's representation to the result string
        result += prefix + ("└── " if last else "├── ") + str(node.number) + ":" + node.text + "\n"

        # Get the children of the current node
        children = list(self.tree.children(node.identifier))
        for i, child in enumerate(children):
            is_last = i == len(children) - 1
            # Recursively build the string for the children
            result = self.get_string_tree(child.identifier, prefix + ("    " if last else "│   "), is_last, result)

        return result
