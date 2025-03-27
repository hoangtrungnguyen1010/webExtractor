import os
import aisuite as ai
from .base_model import BaseModel

class AISuiteModel(BaseModel):
    def __init__(self, provider_model: str):
        """
        Initialize the AISuiteModel with the specified provider and model.

        Args:
            provider_model (str): The provider and model identifier in the format 'provider:model_name'.
            For example, 'openai:gpt-4o' or 'anthropic:claude-3-5-sonnet-20240620'.
        """
        self.provider_model = provider_model
        self.client = ai.Client()

    def load_model(self):
        # No explicit loading required; AISuite handles model access via API calls.
        pass

    def generate_response(self, prompt: str) -> str:
        """
        Generate a response from the model based on the given prompt.

        Args:
            prompt (str): The input text prompt for the model.

        Returns:
            str: The generated response from the model.
        """
        messages = [{"role": "user", "content": prompt}]
        response = self.client.chat.completions.create(
            model=self.provider_model,
            messages=messages,
            temperature=0.75
        )
        return response.choices[0].message.content
