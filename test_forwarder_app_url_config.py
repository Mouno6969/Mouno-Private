import ast
import pathlib
import unittest


CONFIG_PATH = pathlib.Path(__file__).with_name("config.py")
CONFIG_SOURCE = CONFIG_PATH.read_text(encoding="utf-8")
CONFIG_TREE = ast.parse(CONFIG_SOURCE)
ENV_EXAMPLE = CONFIG_PATH.with_name(".env.example").read_text(encoding="utf-8")


def default_scb_forwarder_app_url():
    for node in CONFIG_TREE.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "SCB_FORWARDER_APP_URL" for target in node.targets):
            continue
        call = node.value
        if isinstance(call, ast.Call) and len(call.args) >= 2:
            return ast.literal_eval(call.args[1])
    raise AssertionError("SCB_FORWARDER_APP_URL default not found")


class ForwarderAppUrlConfigTests(unittest.TestCase):
    def test_default_app_url_is_direct_apk_release_url(self):
        url = default_scb_forwarder_app_url()

        self.assertNotIn("/actions/", url)
        self.assertIn("/releases/latest/download/", url)
        self.assertTrue(url.endswith(".apk"))

    def test_env_example_uses_same_installable_url(self):
        self.assertIn(f"SCB_FORWARDER_APP_URL={default_scb_forwarder_app_url()}", ENV_EXAMPLE)


if __name__ == "__main__":
    unittest.main()
