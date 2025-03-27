from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from .base_model import BaseModel

class HuggingFaceModel(BaseModel):
    def __init__(self, model_name: str):
        self.model_name = model_name

    def load_model(self):
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)

    def generate_response(self, prompt: str) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(**inputs)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
