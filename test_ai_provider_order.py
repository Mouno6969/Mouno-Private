import ast
import pathlib
import unittest


BOT_PATH = pathlib.Path(__file__).with_name("bot.py")
BOT_SOURCE = BOT_PATH.read_text(encoding="utf-8")
BOT_TREE = ast.parse(BOT_SOURCE)

CONFIG_PATH = pathlib.Path(__file__).with_name("config.py")
CONFIG_SOURCE = CONFIG_PATH.read_text(encoding="utf-8")
CONFIG_TREE = ast.parse(CONFIG_SOURCE)


def load_provider_order_namespace(ai_provider_order):
    names = {
        "AI_PROVIDER_LABELS",
        "FAST_NVIDIA_PROVIDER_ORDER",
        "STANDARD_PROVIDER_ORDER",
        "SLOW_NVIDIA_PROVIDER_ORDER",
        "ai_provider_order",
    }
    body = []
    for node in BOT_TREE.body:
        if isinstance(node, ast.Assign):
            targets = {target.id for target in node.targets if isinstance(target, ast.Name)}
            if targets & names:
                body.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in names:
            body.append(node)

    module = ast.Module(body=body, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"AI_PROVIDER_ORDER": ai_provider_order}
    exec(compile(module, str(BOT_PATH), "exec"), namespace)
    return namespace


def default_config_provider_order():
    for node in CONFIG_TREE.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "AI_PROVIDER_ORDER" for target in node.targets):
            continue
        call = node.value
        if isinstance(call, ast.Call) and len(call.args) >= 2:
            return ast.literal_eval(call.args[1])
    raise AssertionError("AI_PROVIDER_ORDER default not found")


class AIProviderOrderTests(unittest.TestCase):
    def test_default_config_puts_cerebras_first_without_dropping_others(self):
        order = default_config_provider_order().split(",")

        self.assertEqual(order[0], "cerebras")
        self.assertEqual(order[1], "groq")
        self.assertEqual(order[2], "gemini")
        self.assertEqual(order.count("cerebras"), 1)
        self.assertEqual(order.count("groq"), 1)
        self.assertEqual(order.count("gemini"), 1)

    def test_ai_provider_order_pins_required_order_before_custom_order(self):
        namespace = load_provider_order_namespace("openrouter,mistral")

        order = namespace["ai_provider_order"]()

        self.assertEqual(order[:3], ["cerebras", "groq", "gemini"])
        self.assertEqual(order[3:5], ["openrouter", "mistral"])


if __name__ == "__main__":
    unittest.main()
