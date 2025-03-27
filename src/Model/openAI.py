import openai
import json
from openai import OpenAI

class OpenAIExtractor:
    def __init__(self, api_key, model="gpt-3.5-turbo"):
        """
        Initializes the OpenAIExtractor with the provided API key and model.

        Args:
            api_key (str): Your OpenAI API key.
            model (str): The OpenAI model to use for extraction (default is "gpt-3.5-turbo").
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
    def _create_prompt(self, text, info_types):
        """
        Creates a prompt to instruct the OpenAI model to extract specified information from the provided text,
        including the node number for each piece of information, and return it in JSON format.

        Args:
            text (str): The input text.
            info_types (list of str): A list of information types to extract.

        Returns:
            str: The formatted prompt string.
        """
        # Start the prompt with a clear instruction
        prompt = (
            "You are an information extraction assistant. Your task is to analyze the following hierarchical text structure:\n\n"
            "Text Structure:\n" + text + "\n\n"
            "Please extract the following information types: " + ", ".join(info_types) + ".\n"
            "For each information type, identify the node(s) containing relevant information, extract the data, "
            "and include the node number where the information was found. Return the extracted information in JSON format, "
            "with each information type as a key and its corresponding value being another JSON object containing 'info' and 'node_number'. "
            "If an information type is not found, its value should be null.\n\n"
            "Example JSON format:\n"
            "{\n"
            "    \"Price\": {\n"
            "        \"info\": \"$18.8\",\n"
            "        \"node_number\": \"16\"\n"
            "    },\n"
            "}\n\n"
            "Only JSON is allowed as an answer. No explanation or other text is allowed."
        )
        return prompt
    def extract(self, text, info_type):
        """
        Extracts the specified information from the provided text using the OpenAI API.

        Args:
            text (str): The input text from which to extract information.
            info_type (str): The type of information to extract (e.g., "price", "product name").

        Returns:
            dict: A dictionary containing the extracted information in JSON format.
        """
        # Initialize the conversation with a system message
        messages = [
            {"role": "system", "content": "You are an information extraction assistant."},
            {"role": "user", "content": self._create_prompt(text, info_type)}
        ]

        # Create a chat completion request with function calling enabled
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"}
        )       
        # Extract the model's response
        result = response.choices[0].message.content

                    # Return the extracted information
        return json.loads(result)
