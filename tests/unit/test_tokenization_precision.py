import unittest
import os
from src.utils.tokenizer import count_tokens, TokenEncoderFactory

class TestTokenizationPrecision(unittest.TestCase):
    def test_tiktoken_fallback(self):
        """Verify that count_tokens uses tiktoken when available or follows fallback."""
        text = "Hello, world! This is a test of the emergency broadcast system."
        
        # Test default (cl100k_base)
        count_default = count_tokens(text)
        self.assertGreater(count_default, 0)
        
        # Test specific OpenAI model
        count_gpt4 = count_tokens(text, "gpt-4")
        self.assertEqual(count_default, count_gpt4) # Both use cl100k_base
        
    def test_heuristic_fallback(self):
        """Verify that unknown models use the heuristic BPE-style counting."""
        text = "Lego principles ensure modularity and scalability."
        
        # We manually trigger the fallback by using a non-existent model name
        factory = TokenEncoderFactory()
        tokens = factory.get_encoder("non-existent-model").encode(text)
        
        self.assertIsInstance(tokens, list)
        self.assertGreater(len(tokens), 0)
        
    def test_empty_string(self):
        """Verify handling of empty strings."""
        self.assertEqual(count_tokens(""), 0)

if __name__ == "__main__":
    unittest.main()
