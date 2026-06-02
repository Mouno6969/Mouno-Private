import ast
import pathlib
import unittest


BOT_PATH = pathlib.Path(__file__).with_name("bot.py")
BOT_SOURCE = BOT_PATH.read_text(encoding="utf-8")
BOT_TREE = ast.parse(BOT_SOURCE)


def load_functions(*names):
    module = ast.Module(
        body=[node for node in BOT_TREE.body if isinstance(node, ast.FunctionDef) and node.name in names],
        type_ignores=[],
    )
    ast.fix_missing_locations(module)
    namespace = {}
    exec(compile(module, str(BOT_PATH), "exec"), namespace)
    return namespace


def function_source(name):
    for node in BOT_TREE.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(BOT_SOURCE, node)
    raise AssertionError(f"Function not found: {name}")


class AIResponseValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        namespace = load_functions("_validate_ai_response_text", "_extract_openai_chat_text")
        cls.validate = staticmethod(namespace["_validate_ai_response_text"])
        cls.extract_openai = staticmethod(namespace["_extract_openai_chat_text"])

    def test_rejects_empty_and_null_like_values(self):
        for value in (None, "", "   ", "none", " None ", "null", "NULL", "undefined", "nil", "[]", "{}"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(RuntimeError, "Empty AI response returned"):
                    self.validate(value)

    def test_allows_normal_answers_containing_null_like_words(self):
        self.assertEqual(self.validate(" There is none available "), "There is none available")
        self.assertEqual(self.validate("null value was mentioned"), "null value was mentioned")

    def test_openai_extractor_rejects_null_like_content(self):
        for content in (None, "null", " None ", [{"text": " [] "}], [{"text": "{}"}]):
            with self.subTest(content=content):
                with self.assertRaisesRegex(RuntimeError, "Empty AI response returned"):
                    self.extract_openai({"choices": [{"message": {"content": content}}]})

    def test_openai_extractor_returns_valid_text(self):
        self.assertEqual(
            self.extract_openai({"choices": [{"message": {"content": " There is none available "}}]}),
            "There is none available",
        )
        self.assertEqual(
            self.extract_openai({"choices": [{"message": {"content": [{"text": "Hello"}, {"text": " world"}]}}]}),
            "Hello world",
        )

    def test_provider_extractors_use_shared_validation(self):
        self.assertIn("return _validate_ai_response_text(text)", function_source("_ask_gemini"))
        self.assertIn("return _validate_ai_response_text(text)", function_source("_ask_cohere"))

    def test_ai_provider_timeout_constant_is_defined(self):
        for node in BOT_TREE.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "AI_PROVIDER_TIMEOUT_SECONDS":
                        self.assertEqual(ast.literal_eval(node.value), 6)
                        return
        self.fail("AI_PROVIDER_TIMEOUT_SECONDS is not defined")

    def test_ai_provider_requests_use_timeout_parameter(self):
        for function_name in ("_ask_gemini", "_ask_openai_compatible", "_ask_cohere"):
            source = function_source(function_name)
            with self.subTest(function_name=function_name):
                # Signature should have the default timeout
                self.assertIn("timeout=AI_PROVIDER_TIMEOUT_SECONDS", source)
                # Body should use the timeout variable
                self.assertIn("timeout=timeout", source)


if __name__ == "__main__":
    unittest.main()
