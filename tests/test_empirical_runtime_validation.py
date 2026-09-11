"""Invented receipt corruption tests for the independent original validation helpers."""
import copy
from pathlib import Path
import unittest

from scripts.validate_roa_empirical_runtime import load_independent_functions, tsha


class RuntimeValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.helpers = load_independent_functions(Path("E:/paper/ReliableRAG"))

    def test_original_cross_line_parser_is_preserved(self):
        self.assertEqual(self.helpers["parsed_query"]("Search query: \nSearch query: FIRST\nSearch query: SECOND", "toy"), ("Search query: FIRST", False))
        self.assertEqual(self.helpers["parsed_answer"]("Final Answer: toy\nextra"), "toy")

    def test_token_render_and_parser_corruption_fails(self):
        class Tokenizer:
            pad_token_id = 0; eos_token_id = 2
            def __len__(self): return 7
            def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True): return "TOY "+messages[0]["content"]
            def __call__(self, prompts, **kwargs): return dict(input_ids=[[1,3]], attention_mask=[[1,1]])
            def batch_decode(self, values, skip_special_tokens=True): return ["Answer: toy"]
        tokenizer = Tokenizer()
        evidence = [dict(rank=i+1, document_id="toy-"+str(i), title="Toy", text="Invented") for i in range(5)]
        trace = dict(dataset="hotpotqa", retriever="bm25", sample_id="toy", position=0)
        templates = dict(answer="{question}\n{evidence}", repair_query="{question}\n{evidence}")
        rendered = self.helpers["render"](evidence)
        prompt = tokenizer.apply_chat_template([dict(content=templates["answer"].format(question="Invented?", evidence=rendered["text"]))])
        rec = dict(**trace, stage="a0", prompt_sha256=tsha(prompt), input_token_ids=[1,3], attention_mask=[1,1],
            generated_token_ids=[4,2], raw_text="Answer: toy", input_tokens=2, output_tokens=2, native_output_score_steps=2,
            render=rendered, parsed_text="toy", parser_fallback=None, logical_generation_calls=1, qwen_forward_calls=2,
            runtime_config_sha256="synthetic")
        validate = lambda value: self.helpers["validate_generation"](value, trace, "a0", evidence, "Invented?", tokenizer, templates, dict(runtime_config_sha256="synthetic"))
        validate(rec)
        mutations = [dict(input_token_ids=[1,4]), dict(parsed_text="changed"), dict(raw_text="changed"),
                     dict(generated_token_ids=[4]*49), dict(prompt_sha256="0"*64), dict(output_tokens=1)]
        for change in mutations:
            with self.subTest(change=list(change)), self.assertRaises(RuntimeError): validate(dict(copy.deepcopy(rec), **change))


if __name__ == "__main__":
    unittest.main()
