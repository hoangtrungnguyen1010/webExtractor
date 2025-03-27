from sentence_transformers import SentenceTransformer, util
import copy

class Pruner:
    def __init__(self, HTMLTree, model, config):
        """
        Initializes the Pruner with an HTMLTree, a SentenceTransformer model, and a configuration.
        """
        self.tree = HTMLTree
        self.model = model
        self.config = config
    
    def getScore(self, node_id, embedding_query):
        """
        Compute the similarity score between the query and the node (including its parent for context).
        """
        text = self.tree[node_id].tag
        embedding_node = self.model.encode(text, convert_to_tensor=True)
        similarity_leaf = util.pytorch_cos_sim(embedding_query, embedding_node)

        # Get parent node similarity
        parent_id = self.tree.parent(node_id).identifier if self.tree.parent(node_id) else None
        similarity_parent = 0
        
        if parent_id:
            parent_text = self.tree[parent_id].tag
            embedding_parent = self.model.encode(parent_text, convert_to_tensor=True)
            similarity_parent = util.pytorch_cos_sim(embedding_query, embedding_parent)
        
        return similarity_leaf + similarity_parent / 2  # Weighted combination
    
    def prune(self, query, remove_proportion=0.3):
        """
        Prune the tree by removing the least relevant leaf nodes based on semantic similarity to the query.
        """
        embedding_query = self.model.encode(query, convert_to_tensor=True)
        
        # Compute similarity scores for all leaf nodes
        scores = []
        for node in self.tree.all_nodes():
            if node.is_leaf():
                similarity = self.getScore(node.identifier, embedding_query)
                scores.append((node.tag, node.identifier, similarity))
        
        # Sort nodes by similarity (ascending, lower means less relevant)
        sorted_scores = sorted(scores, key=lambda x: x[2], reverse=False)
        
        # Determine the number of nodes to remove
        num_nodes_to_remove = int(len(sorted_scores) * remove_proportion)
        nodes_to_remove = set([sorted_scores[i][1] for i in range(num_nodes_to_remove)])
        
        # Create a deep copy of the tree before pruning
        relevantTree = copy.deepcopy(self.tree)
        
        # Remove the least relevant nodes
        for node_id in nodes_to_remove:
            if relevantTree.contains(node_id):
                relevantTree.remove_node(node_id)
        
        return relevantTree
    def getTheLeftOverAndExtend(self, pruned_tree, removed_leaves, extra_leaves):
            """
            Returns a tree where all leaves in pruned_tree are replaced with removed_leaves,
            and additional extra_leaves are added.
            """
            modified_tree = copy.deepcopy(pruned_tree)
            
            # Remove all existing leaves
            for node in pruned_tree.all_nodes():
                if node.is_leaf():
                    modified_tree.remove_node(node.identifier)
            
            # Add removed leaves back
            for node_id, node_text in removed_leaves:
                parent_id = pruned_tree.root  # Default to root if parent_id is unknown
                modified_tree.add_node(node_id, parent=parent_id, data=node_text)
            
            # Add extra leaves if provided
            if extra_leaves:
                for node_id, node_data in extra_leaves.items():
                    parent_id = node_data.get("parent_id", modified_tree.root)
                    modified_tree.add_node(node_id, parent=parent_id, data=node_data.get("data", ""))
            
            return modified_tree