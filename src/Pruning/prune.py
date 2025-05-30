import copy
import requests
import time

class Pruner:
    def __init__(self, HTMLTree, config, api_token):
        """
        Initializes the Pruner with an HTMLTree, configuration, and HuggingFace API token.
        """
        self.tree = HTMLTree
        self.config = config
        self.api_url = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
        self.headers = {"Authorization": f"Bearer {api_token}"}
        
    def _query_api(self, payload, max_retries=3, retry_delay=1):
        """
        Query the HuggingFace API with retry logic for rate limiting.
        """
        for attempt in range(max_retries):
            try:
                response = requests.post(self.api_url, headers=self.headers, json=payload)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 503:
                    # Model is loading, wait and retry
                    print(f"Model loading, waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"API Error: {response.status_code} - {response.text}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return None
        
        return None

    def getBaseScore(self, node_id, query_text):
        """
        Compute the base similarity score between the query and the node text.
        """
        node_text = self.tree.tree[node_id].text
        
        # Prepare payload for similarity comparison
        payload = {
            "inputs": {
                "source_sentence": query_text,
                "sentences": [node_text]
            }
        }
        
        result = self._query_api(payload)
        
        if result is None:
            print(f"Failed to get similarity for node {node_id}")
            return 0.0
        
        # Extract similarity score
        similarity_score = result[0] if len(result) > 0 else 0.0
        return similarity_score

    def calculateAllScores(self, query):
        """
        Calculate base scores for all nodes and then compute final scores with parent averaging.
        """
        all_nodes = list(self.tree.tree.all_nodes())
        base_scores = {}
        
        print(f"Computing base similarity scores for {len(all_nodes)} nodes...")
        
        # Step 1: Calculate base scores for all nodes
        for i, node in enumerate(all_nodes):
            if i % 10 == 0:  # Progress indicator
                print(f"Processing node {i+1}/{len(all_nodes)}")
                
            base_score = self.getBaseScore(node.identifier, query)
            base_scores[node.identifier] = base_score
            
            # Add small delay to avoid hitting rate limits
            time.sleep(0.1)
        
        print("Calculating final scores with parent node averaging...")
        
        # Step 2: Calculate parent averages and final scores
        final_scores = {}
        
        for node in all_nodes:
            node_id = node.identifier
            base_score = base_scores[node_id]
            
            # Get parent node
            parent_node = self.tree.tree.parent(node_id)
            
            if parent_node:
                parent_id = parent_node.identifier
                
                # Get all children of the parent (siblings + current node)
                children = self.tree.tree.children(parent_id)
                
                # Calculate average score of all children under this parent
                if children:
                    children_scores = [base_scores[child.identifier] for child in children]
                    avg_children_score = sum(children_scores) / len(children_scores)
                else:
                    avg_children_score = 0.0
                
                # Final score = base score + average score of siblings
                final_score = base_score + avg_children_score
            else:
                # Root node or orphaned node - just use base score
                final_score = base_score
            
            final_scores[node_id] = final_score
        
        return base_scores, final_scores

    def estimate_tokens(self, text):
        """
        Rough estimation of token count for a given text.
        Using approximate rule: 1 token ≈ 4 characters for English text.
        """
        if not text:
            return 0
        return max(1, len(text) // 4)

    def calculate_tree_tokens(self, tree_nodes):
        """
        Calculate total tokens for a list of tree nodes.
        """
        total_tokens = 0
        for node in tree_nodes:
            node_text = self.tree.tree[node.identifier].text if hasattr(self.tree.tree[node.identifier], 'text') else str(node.tag)
            total_tokens += self.estimate_tokens(node_text)
        return total_tokens

    def prune_with_fallback(self, query, max_tokens=None, min_score_threshold=0.1, remove_proportion=0.3, fallback_strategy="iterative"):
        """
        Enhanced pruning with fallback strategies to handle potentially important removed nodes.
        
        Args:
            query: The query text for similarity scoring
            max_tokens: Maximum tokens allowed
            min_score_threshold: Minimum score threshold
            remove_proportion: Fallback proportion if max_tokens is None
            fallback_strategy: "iterative", "backup_query", or "hybrid"
        
        Returns:
            dict with primary_tree, removed_nodes_tree, and strategy info
        """
        # Calculate all scores first
        base_scores, final_scores = self.calculateAllScores(query)
        
        # Get only leaf nodes for pruning
        leaf_nodes = [node for node in self.tree.tree.all_nodes() if len(self.tree.tree.children(node.identifier)) == 0]
        
        # Create detailed node information
        leaf_scores = []
        for node in leaf_nodes:
            final_score = final_scores[node.identifier]
            node_text = self.tree.tree[node.identifier].text if hasattr(self.tree.tree[node.identifier], 'text') else str(node.tag)
            token_count = self.estimate_tokens(node_text)
            leaf_scores.append({
                'tag': node.tag,
                'node_id': node.identifier, 
                'score': final_score,
                'tokens': token_count,
                'text': node_text
            })

        # Sort by score (lowest first for removal)
        sorted_nodes = sorted(leaf_scores, key=lambda x: x['score'], reverse=False)
        
        # Determine nodes to remove
        nodes_to_remove, pruning_info = self._determine_nodes_to_remove(
            sorted_nodes, max_tokens, min_score_threshold, remove_proportion
        )
        
        # Create primary tree and removed nodes info
        primary_tree = copy.deepcopy(self.tree)
        removed_nodes_info = []
        
        for node_info in sorted_nodes:
            if node_info['node_id'] in nodes_to_remove:
                removed_nodes_info.append(node_info)
                if primary_tree.tree.contains(node_info['node_id']):
                    primary_tree.tree.remove_node(node_info['node_id'])
        
        # Create fallback strategy based on removed nodes
        fallback_result = self._create_fallback_strategy(
            removed_nodes_info, fallback_strategy, max_tokens
        )
        
        result = {
            'primary_tree': primary_tree,
            'removed_nodes': removed_nodes_info,
            'fallback_trees': fallback_result['trees'],
            'strategy_info': {
                **pruning_info,
                'fallback_strategy': fallback_strategy,
                'total_removed_nodes': len(removed_nodes_info),
                'fallback_trees_count': len(fallback_result['trees'])
            },
            'query_suggestions': fallback_result['query_suggestions']
        }
        
        return result
    
    def _determine_nodes_to_remove(self, sorted_nodes, max_tokens, min_score_threshold, remove_proportion):
        """Helper method to determine which nodes should be removed."""
        nodes_to_remove = set()
        
        if max_tokens is not None:
            current_tokens = sum(node['tokens'] for node in sorted_nodes)
            print(f"Current total tokens: {current_tokens}, Target max tokens: {max_tokens}")
            
            if current_tokens > max_tokens:
                tokens_to_remove = current_tokens - max_tokens
                removed_tokens = 0
                
                for node_info in sorted_nodes:
                    if removed_tokens >= tokens_to_remove:
                        break
                    
                    if node_info['score'] < min_score_threshold or removed_tokens < tokens_to_remove:
                        nodes_to_remove.add(node_info['node_id'])
                        removed_tokens += node_info['tokens']
                        print(f"Removing node {node_info['node_id']} (score: {node_info['score']:.3f}, tokens: {node_info['tokens']})")
            
            # Always remove nodes below threshold
            for node_info in sorted_nodes:
                if node_info['score'] < min_score_threshold:
                    nodes_to_remove.add(node_info['node_id'])
        else:
            # Proportion-based fallback
            num_to_remove = int(len(sorted_nodes) * remove_proportion)
            for i, node_info in enumerate(sorted_nodes):
                if i < num_to_remove or node_info['score'] < min_score_threshold:
                    nodes_to_remove.add(node_info['node_id'])
        
        pruning_info = {
            'strategy': 'token_based' if max_tokens else 'proportion_based',
            'nodes_removed_count': len(nodes_to_remove)
        }
        
        return nodes_to_remove, pruning_info
    
    def _create_fallback_strategy(self, removed_nodes, strategy, max_tokens):
        """Create fallback strategies for handling removed nodes."""
        if not removed_nodes:
            return {'trees': [], 'query_suggestions': []}
        
        fallback_trees = []
        query_suggestions = []
        
        if strategy == "iterative":
            # Create multiple smaller trees from removed nodes
            fallback_trees = self._create_iterative_trees(removed_nodes, max_tokens)
            query_suggestions = [
                "Query the primary tree first, then query fallback trees if no answer found",
                "Consider combining results from multiple tree queries"
            ]
            
        elif strategy == "backup_query":
            # Create a single backup tree with highest scoring removed nodes
            backup_tree = self._create_backup_tree(removed_nodes, max_tokens)
            if backup_tree:
                fallback_trees = [backup_tree]
            query_suggestions = [
                "If primary query yields no results, query the backup tree",
                "Look for complementary information between primary and backup results"
            ]
            
        elif strategy == "hybrid":
            # Combine both approaches
            backup_tree = self._create_backup_tree(removed_nodes, max_tokens // 2 if max_tokens else None)
            iterative_trees = self._create_iterative_trees(removed_nodes, max_tokens // 4 if max_tokens else None)
            
            fallback_trees = ([backup_tree] if backup_tree else []) + iterative_trees
            query_suggestions = [
                "Use tiered querying: primary → backup → iterative trees",
                "Stop when satisfactory answer is found to save tokens/cost"
            ]
        
        return {
            'trees': fallback_trees,
            'query_suggestions': query_suggestions
        }
    
    def _create_iterative_trees(self, removed_nodes, max_tokens_per_tree):
        """Create multiple small trees for iterative querying."""
        if not removed_nodes:
            return []
        
        # Group by score ranges for more systematic querying
        score_ranges = [
            (0.4, 1.0, "high_relevance"),
            (0.2, 0.4, "medium_relevance"), 
            (0.0, 0.2, "low_relevance")
        ]
        
        iterative_trees = []
        
        for min_score, max_score, range_name in score_ranges:
            range_nodes = [
                node for node in removed_nodes 
                if min_score <= node['score'] < max_score
            ]
            
            if not range_nodes:
                continue
                
            # Sort by score (highest first for this range)
            range_nodes.sort(key=lambda x: x['score'], reverse=True)
            
            if max_tokens_per_tree:
                # Create trees that fit within token limit
                current_tokens = 0
                tree_nodes = []
                
                for node in range_nodes:
                    if current_tokens + node['tokens'] <= max_tokens_per_tree:
                        tree_nodes.append(node)
                        current_tokens += node['tokens']
                    else:
                        # Start new tree if we have nodes
                        if tree_nodes:
                            iterative_trees.append({
                                'nodes': tree_nodes.copy(),
                                'category': range_name,
                                'token_count': current_tokens
                            })
                            tree_nodes = [node]
                            current_tokens = node['tokens']
                
                # Add remaining nodes
                if tree_nodes:
                    iterative_trees.append({
                        'nodes': tree_nodes,
                        'category': range_name,
                        'token_count': current_tokens
                    })
            else:
                # No token limit, group all nodes in this range
                iterative_trees.append({
                    'nodes': range_nodes,
                    'category': range_name,
                    'token_count': sum(node['tokens'] for node in range_nodes)
                })
        
        return iterative_trees
    
    def _create_backup_tree(self, removed_nodes, max_tokens):
        """Create a single backup tree with highest scoring removed nodes."""
        if not removed_nodes:
            return None
        
        # Sort by score (highest first)
        sorted_removed = sorted(removed_nodes, key=lambda x: x['score'], reverse=True)
        
        if max_tokens:
            # Select highest scoring nodes that fit within token limit
            selected_nodes = []
            current_tokens = 0
            
            for node in sorted_removed:
                if current_tokens + node['tokens'] <= max_tokens:
                    selected_nodes.append(node)
                    current_tokens += node['tokens']
                else:
                    break
        else:
            # Take top 50% of removed nodes by score
            selected_nodes = sorted_removed[:len(sorted_removed)//2]
        
        if selected_nodes:
            return {
                'nodes': selected_nodes,
                'category': 'backup_high_score',
                'token_count': sum(node['tokens'] for node in selected_nodes)
            }
        
        return None
        """
        Prune the tree based on token limits and score thresholds for LLM input optimization.
        
        Args:
            query: The query text for similarity scoring
            max_tokens: Maximum tokens allowed (if None, uses remove_proportion)
            min_score_threshold: Minimum score threshold (nodes below this are candidates for removal)
            remove_proportion: Fallback proportion if max_tokens is None
        """
        # Calculate all scores first
        base_scores, final_scores = self.calculateAllScores(query)
        
        # Get only leaf nodes for pruning (nodes that don't have children)
        leaf_nodes = [node for node in self.tree.tree.all_nodes() if len(self.tree.tree.children(node.identifier)) == 0]
        
        # Create list of (tag, node_id, final_score, token_count) for leaf nodes
        leaf_scores = []
        for node in leaf_nodes:
            final_score = final_scores[node.identifier]
            node_text = self.tree.tree[node.identifier].text if hasattr(self.tree.tree[node.identifier], 'text') else str(node.tag)
            token_count = self.estimate_tokens(node_text)
            leaf_scores.append((node.tag, node.identifier, final_score, token_count))

        # Sort nodes by final similarity score (ascending, lower means less relevant)
        sorted_scores = sorted(leaf_scores, key=lambda x: x[2], reverse=False)
        
        # Determine nodes to remove based on strategy
        nodes_to_remove = set()
        
        if max_tokens is not None:
            # Token-based pruning strategy
            current_tokens = sum(item[3] for item in sorted_scores)  # Total tokens from all leaf nodes
            print(f"Current total tokens: {current_tokens}, Target max tokens: {max_tokens}")
            
            if current_tokens > max_tokens:
                # Remove lowest scoring nodes until we're under token limit
                tokens_to_remove = current_tokens - max_tokens
                removed_tokens = 0
                
                for tag, node_id, score, token_count in sorted_scores:
                    if removed_tokens >= tokens_to_remove:
                        break
                    
                    # Also check score threshold - prioritize low score nodes
                    if score < min_score_threshold or removed_tokens < tokens_to_remove:
                        nodes_to_remove.add(node_id)
                        removed_tokens += token_count
                        print(f"Removing node {node_id} (score: {score:.3f}, tokens: {token_count})")
                
                print(f"Removed {removed_tokens} tokens to meet limit")
            else:
                # Even if under token limit, remove nodes below threshold
                for tag, node_id, score, token_count in sorted_scores:
                    if score < min_score_threshold:
                        nodes_to_remove.add(node_id)
                        print(f"Removing low-score node {node_id} (score: {score:.3f})")
        else:
            # Fallback to proportion-based pruning
            num_nodes_to_remove = int(len(sorted_scores) * remove_proportion)
            
            # But still respect score threshold
            for i, (tag, node_id, score, token_count) in enumerate(sorted_scores):
                if i < num_nodes_to_remove or score < min_score_threshold:
                    nodes_to_remove.add(node_id)

        print(f"Total nodes to remove: {len(nodes_to_remove)}")

        # Create a deep copy of the tree before pruning
        relevantTree = copy.deepcopy(self.tree)

        # Remove the selected nodes
        removed_nodes_info = []
        for node_id in nodes_to_remove:
            if relevantTree.tree.contains(node_id):
                node_info = next((item for item in sorted_scores if item[1] == node_id), None)
                if node_info:
                    removed_nodes_info.append(node_info)
                relevantTree.tree.remove_node(node_id)

        # Calculate final token count
        remaining_leaf_nodes = [node for node in relevantTree.tree.all_nodes() if len(relevantTree.tree.children(node.identifier)) == 0]
        final_token_count = self.calculate_tree_tokens(remaining_leaf_nodes)
        
        print(f"Final token count after pruning: {final_token_count}")

        # Return detailed information for debugging
        pruning_info = {
            'removed_nodes': removed_nodes_info,
            'base_scores': base_scores,
            'final_scores': final_scores,
            'final_token_count': final_token_count,
            'nodes_removed_count': len(nodes_to_remove),
            'pruning_strategy': 'token_based' if max_tokens else 'proportion_based'
        }

        return relevantTree, pruning_info

    def getTheLeftOverAndExtend(self, pruned_tree, removed_leaves, extra_leaves):
        """
        Returns a tree where all leaves in pruned_tree are replaced with removed_leaves,
        and additional extra_leaves are added.
        """
        modified_tree = copy.deepcopy(pruned_tree)

        # Remove all existing leaves (nodes without children)
        leaves_to_remove = []
        for node in pruned_tree.tree.all_nodes():
            if len(pruned_tree.tree.children(node.identifier)) == 0:
                leaves_to_remove.append(node.identifier)
        
        for node_id in leaves_to_remove:
            if modified_tree.tree.contains(node_id):
                modified_tree.tree.remove_node(node_id)

        # Add removed leaves back
        for node_id, node_text in removed_leaves:
            parent_id = pruned_tree.tree.root  # Default to root if parent_id is unknown
            modified_tree.tree.create_node(node_text, node_id, parent=parent_id)

        # Add extra leaves if provided
        if extra_leaves:
            for node_id, node_data in extra_leaves.items():
                parent_id = node_data.get("parent_id", modified_tree.tree.root)
                data = node_data.get("data", "")
                modified_tree.tree.create_node(data, node_id, parent=parent_id)

        return modified_tree