import copy
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

from vite_config_plugin import (
    RawJS,
    ViteConfig,
    ViteConfigPlugin,
)


class TestRawJS:
    def test_init(self):
        code = "console.log('hello')"
        raw_js = RawJS(code)
        assert raw_js.code == code

    def test_init_empty(self):
        raw_js = RawJS("")
        assert raw_js.code == ""

    def test_init_multiline(self):
        code = """
        function test() {
            return true;
        }
        """
        raw_js = RawJS(code)
        assert raw_js.code == code


class TestViteConfigPlugin:
    def setup_method(self):
        """Set up test fixtures."""
        self.basic_config = {
            "plugins": [RawJS("somePlugin()")],
            "build": {
                "outDir": "dist",
            },
        }
        self.plugin = ViteConfigPlugin(self.basic_config)

    def test_init(self):
        assert self.plugin.name == "vite_config"
        assert self.plugin.config == self.basic_config
        assert self.plugin.imports == []

    def test_init_with_imports(self):
        imports = ['import { test } from "test";']
        plugin = ViteConfigPlugin(self.basic_config, imports=imports)
        assert plugin.imports == imports

    def test_python_to_js_raw_js(self):
        raw_js = RawJS("console.log('test')")
        result = self.plugin.__python_to_js__(raw_js)
        assert result == "console.log('test')"

    def test_python_to_js_string(self):
        result = self.plugin.__python_to_js__("test string")
        assert result == "'test string'"

    def test_python_to_js_boolean_true(self):
        result = self.plugin.__python_to_js__(True)
        assert result == "true"

    def test_python_to_js_boolean_false(self):
        result = self.plugin.__python_to_js__(False)
        assert result == "false"

    def test_python_to_js_none(self):
        result = self.plugin.__python_to_js__(None)
        assert result == "null"

    def test_python_to_js_number(self):
        assert self.plugin.__python_to_js__(42) == "42"
        assert self.plugin.__python_to_js__(3.14) == "3.14"

    def test_python_to_js_list(self):
        test_list = ["item1", 42, True]
        result = self.plugin.__python_to_js__(test_list)
        assert result == "['item1', 42, true]"

    def test_python_to_js_tuple(self):
        test_tuple = ("item1", 42, True)
        result = self.plugin.__python_to_js__(test_tuple)
        assert result == "['item1', 42, true]"

    def test_python_to_js_empty_dict(self):
        result = self.plugin.__python_to_js__({})
        assert result == "{}"

    def test_python_to_js_simple_dict(self):
        test_dict = {"key1": "value1", "key2": 42}
        result = self.plugin.__python_to_js__(test_dict)
        assert "key1: 'value1'" in result
        assert "key2: 42" in result
        assert result.startswith("{")
        assert result.endswith("}")

    def test_python_to_js_dict_with_special_keys(self):
        test_dict = {"special-key": "value", "normal_key": "value2"}
        result = self.plugin.__python_to_js__(test_dict)
        assert "'special-key': 'value'" in result
        assert "normal_key: 'value2'" in result

    def test_python_to_js_nested_dict(self):
        test_dict = {
            "outer": {
                "inner": "value",
                "number": 42,
            }
        }
        result = self.plugin.__python_to_js__(test_dict)
        assert "outer:" in result
        assert "inner: 'value'" in result
        assert "number: 42" in result

    def test_handle_dict_empty(self):
        result = self.plugin.__handle_dict__({}, "", 0)
        assert result == "{}"

    def test_handle_dict_with_content(self):
        test_dict = {"key": "value"}
        result = self.plugin.__handle_dict__(test_dict, "", 0)
        assert "key: 'value'" in result

    def test_deep_merge_simple(self):
        mergee = {"a": 1, "b": 2}
        merger = {"b": 3, "c": 4}
        result = self.plugin.__deep_merge__(mergee, merger)
        expected = {"a": 1, "b": 2, "c": 4}
        assert result == expected

    def test_deep_merge_nested(self):
        mergee = {
            "plugins": ["plugin1"],
            "build": {"outDir": "dist", "sourcemap": True}
        }
        merger = {
            "plugins": ["plugin2"],
            "build": {"sourcemap": False, "minify": True}
        }
        result = self.plugin.__deep_merge__(mergee, merger)
        assert "plugin1" in result["plugins"]
        assert "plugin2" in result["plugins"]
        assert result["build"] == {"outDir": "dist", "sourcemap": True, "minify": True}

    def test_deep_merge_overwrites_non_dict(self):
        mergee = {"key": "old_value"}
        merger = {"key": "new_value"}
        result = self.plugin.__deep_merge__(mergee, merger)
        assert result["key"] == "old_value"

    def test_alias_dict_to_js_array_empty(self):
        result = self.plugin.__alias_dict_to_js_array__([])
        assert result.code == "[]"

    def test_alias_dict_to_js_array_single(self):
        aliases = [{"find": "@", "replacement": "./src"}]
        result = self.plugin.__alias_dict_to_js_array__(aliases)
        expected_pattern = r'\[\s*{\s*find:\s*"@",\s*replacement:\s*fileURLToPath\(new URL\("./src",\s*import\.meta\.url\)\)\s*}\s*\]'
        assert re.search(expected_pattern, result.code)

    def test_alias_dict_to_js_array_multiple(self):
        aliases = [
            {"find": "@", "replacement": "./src"},
            {"find": "$", "replacement": "./public"}
        ]
        result = self.plugin.__alias_dict_to_js_array__(aliases)
        assert '"@"' in result.code
        assert '"$"' in result.code
        assert "./src" in result.code
        assert "./public" in result.code

    def test_alias_dict_to_js_array_escapes_quotes(self):
        aliases = [{"find": 'test"quote', "replacement": './path"with"quotes'}]
        result = self.plugin.__alias_dict_to_js_array__(aliases)
        assert '\\"' in result.code

    def test_alias_dict_to_js_array_converts_backslashes(self):
        aliases = [{"find": "@", "replacement": ".\\src\\components"}]
        result = self.plugin.__alias_dict_to_js_array__(aliases)
        assert "./src/components" in result.code
        assert "\\" not in result.code

    @patch('vite_config_plugin.get_config')
    @patch('vite_config_plugin.environment')
    def test_set_defaults(self, mock_env, mock_get_config):
        # Mock the config
        mock_config = MagicMock()
        mock_config.frontend_path = "/app"
        mock_get_config.return_value = mock_config
        
        # Mock environment variables
        mock_env.VITE_HMR.get.return_value = True
        mock_env.VITE_FORCE_FULL_RELOAD.get.return_value = False

        defaults = self.plugin.__set_defaults__()
        
        # Check that defaults contain expected structure
        assert "plugins" in defaults
        assert "build" in defaults
        assert "server" in defaults
        assert "resolve" in defaults
        
        # Check plugins list contains expected items
        plugins = defaults["plugins"]
        assert any(isinstance(p, RawJS) and "alwaysUseReactDomServerNode" in p.code for p in plugins)
        assert any(isinstance(p, RawJS) and "reactRouter" in p.code for p in plugins)
        assert any(isinstance(p, RawJS) and "safariCacheBustPlugin" in p.code for p in plugins)

    @patch('vite_config_plugin.get_config')
    @patch('vite_config_plugin.environment')
    def test_set_defaults_with_full_reload(self, mock_env, mock_get_config):
        mock_config = MagicMock()
        mock_config.frontend_path = ""
        mock_get_config.return_value = mock_config
        
        mock_env.VITE_HMR.get.return_value = False
        mock_env.VITE_FORCE_FULL_RELOAD.get.return_value = True

        defaults = self.plugin.__set_defaults__()
        
        plugins = defaults["plugins"]
        assert any(isinstance(p, RawJS) and "fullReload" in p.code for p in plugins)

    @patch('vite_config_plugin.get_config')
    @patch('vite_config_plugin.environment')
    def test_set_defaults_imports(self, mock_env, mock_get_config):
        mock_config = MagicMock()
        mock_config.frontend_path = ""
        mock_get_config.return_value = mock_config
        
        mock_env.VITE_HMR.get.return_value = True
        mock_env.VITE_FORCE_FULL_RELOAD.get.return_value = False

        # Test with custom imports
        plugin = ViteConfigPlugin({}, imports=['import custom from "custom";'])
        _ = plugin.__set_defaults__()
        
        expected_imports = [
            'import { fileURLToPath, URL } from "url";',
            'import { reactRouter } from "@react-router/dev/vite";',
            'import { defineConfig } from "vite";',
            'import safariCacheBustPlugin from "./vite-plugin-safari-cachebust";',
            'import custom from "custom";'
        ]
        
        assert plugin.imports == expected_imports

    @patch('vite_config_plugin.get_web_dir')
    @patch('vite_config_plugin.get_config')
    @patch('vite_config_plugin.environment')
    def test_render_vite_config(self, mock_env, mock_get_config, mock_get_web_dir):
        # Setup mocks
        mock_config = MagicMock()
        mock_config.frontend_path = ""
        mock_get_config.return_value = mock_config
        
        mock_env.VITE_HMR.get.return_value = True
        mock_env.VITE_FORCE_FULL_RELOAD.get.return_value = False
        
        mock_web_dir = MagicMock()
        mock_get_web_dir.return_value = mock_web_dir
        
        # Test rendering
        config = {"build": {"outDir": "custom_dist"}}
        plugin = ViteConfigPlugin(config)
        
        _, content = plugin.__render_vite_config__()
        
        # Check that the content contains expected parts
        assert "import { defineConfig }" in content
        assert "export default defineConfig" in content
        assert "alwaysUseReactDomServerNode" in content
        assert "fullReload" in content
        assert "outDir: 'custom_dist'" in content

    def test_render_vite_config_structure(self):
        with patch('vite_config_plugin.get_config') as mock_get_config, \
             patch('vite_config_plugin.environment') as mock_env, \
             patch('vite_config_plugin.get_web_dir') as mock_get_web_dir:
            
            mock_config = MagicMock()
            mock_config.frontend_path = ""
            mock_get_config.return_value = mock_config
            
            mock_env.VITE_HMR.get.return_value = False
            mock_env.VITE_FORCE_FULL_RELOAD.get.return_value = False
            
            mock_get_web_dir.return_value = Path("/mock/web/dir")
            
            config = {}
            plugin = ViteConfigPlugin(config)
            
            _, content = plugin.__render_vite_config__()
            
            # Verify structure
            lines = content.split('\n')
            
            # Should start with imports
            assert any("import" in line for line in lines[:10])
            
            # Should contain function definitions
            assert "function alwaysUseReactDomServerNode" in content
            assert "function fullReload" in content
            
            # Should end with export
            assert "export default defineConfig" in content

    @patch('vite_config_plugin.get_config')
    @patch('vite_config_plugin.environment')
    def test_pre_compile(self, mock_env, mock_get_config):
        mock_config = MagicMock()
        mock_config.frontend_path = ""
        mock_get_config.return_value = mock_config
        
        mock_env.VITE_HMR.get.return_value = True
        mock_env.VITE_FORCE_FULL_RELOAD.get.return_value = False

        # Mock context
        mock_add_save_task = MagicMock()
        context = {"add_save_task": mock_add_save_task}
        
        self.plugin.pre_compile(**context)
        
        # Verify that add_save_task was called
        mock_add_save_task.assert_called_once()
        
        # Verify the callable passed to add_save_task
        task_func = mock_add_save_task.call_args[0][0]
        assert callable(task_func)

    def test_plugin_inheritance(self):
        from reflex.plugins.base import Plugin
        assert issubclass(ViteConfigPlugin, Plugin)
        assert isinstance(self.plugin, Plugin)


class TestViteConfigTyping:
    def test_vite_config_basic(self):
        config: ViteConfig = {
            "plugins": [RawJS("test()")],
            "build": {
                "outDir": "dist"
            }
        }
        assert config["plugins"][0].code == "test()"
        assert config["build"]["outDir"] == "dist"

    def test_vite_config_partial(self):
        config: ViteConfig = {}
        assert isinstance(config, dict)

    def test_vite_config_server_options(self):
        config: ViteConfig = {
            "server": {
                "port": 3000,
                "host": "localhost",
                "https": {
                    "key": "path/to/key",
                    "cert": "path/to/cert"
                }
            }
        }
        assert config["server"]["port"] == 3000
        assert config["server"]["https"]["key"] == "path/to/key"

    def test_vite_config_build_options(self):
        config: ViteConfig = {
            "build": {
                "target": "es2015",
                "sourcemap": True,
                "minify": "esbuild"
            }
        }
        assert config["build"]["target"] == "es2015"
        assert config["build"]["sourcemap"] is True


class TestComplexScenarios:
    def test_full_config_merge_scenario(self):
        user_config = {
            "plugins": [RawJS("customPlugin()")],
            "server": {
                "port": 4000,
                "host": "0.0.0.0"
            },
            "build": {
                "sourcemap": True,
                "rollupOptions": {
                    "external": ["react", "react-dom"]
                }
            }
        }
        
        with patch('vite_config_plugin.get_config') as mock_get_config, \
             patch('vite_config_plugin.environment') as mock_env:
            
            mock_config = MagicMock()
            mock_config.frontend_path = "app"
            mock_get_config.return_value = mock_config
            
            mock_env.VITE_HMR.get.return_value = False
            mock_env.VITE_FORCE_FULL_RELOAD.get.return_value = False
            
            plugin = ViteConfigPlugin(user_config)
            defaults = plugin.__set_defaults__()
            merged = plugin.__deep_merge__(copy.deepcopy(user_config), defaults)
            
            # User config should be preserved
            assert merged["server"]["port"] == 4000
            assert merged["server"]["host"] == "0.0.0.0"
            assert merged["build"]["sourcemap"] is True
            
            # Defaults should be added
            assert "hmr" in merged["server"]
            assert "plugins" in merged
            
            # Deep merge should work for rollupOptions
            assert "jsx" in merged["build"]["rollupOptions"]
            assert merged["build"]["rollupOptions"]["external"] == ["react", "react-dom"]

    def test_complex_alias_configuration(self):
        plugin = ViteConfigPlugin({})
        
        complex_aliases = [
            {"find": "@components", "replacement": "./src/components"},
            {"find": "@utils", "replacement": "./src/utils"},
            {"find": "~styles", "replacement": "./src/styles"},
            {"find": "@/lib", "replacement": "./lib"}
        ]
        
        result = plugin.__alias_dict_to_js_array__(complex_aliases)
        
        # Check all aliases are present
        for alias in complex_aliases:
            assert alias["find"] in result.code
            assert alias["replacement"].replace("\\", "/") in result.code
        
        # Check structure
        assert result.code.startswith("[")
        assert result.code.endswith("]")
        assert "fileURLToPath" in result.code

    def test_javascript_output_validity(self):
        config = {
            "plugins": [RawJS("somePlugin()")],
            "server": {
                "port": 3000,
                "hmr": {"port": 24678}
            },
            "build": {
                "rollupOptions": {
                    "output": {
                        "manualChunks": RawJS("(id) => id.includes('node_modules') ? 'vendor' : null")
                    }
                }
            },
            "resolve": {
                "alias": [
                    {"find": "@", "replacement": "./src"}
                ]
            }
        }
        
        with patch('vite_config_plugin.get_config') as mock_get_config, \
             patch('vite_config_plugin.environment') as mock_env, \
             patch('vite_config_plugin.get_web_dir') as mock_get_web_dir:
            
            mock_config = MagicMock()
            mock_config.frontend_path = ""
            mock_get_config.return_value = mock_config
            
            mock_env.VITE_HMR.get.return_value = True
            mock_env.VITE_FORCE_FULL_RELOAD.get.return_value = False
            
            mock_get_web_dir.return_value = Path("/test")
            
            plugin = ViteConfigPlugin(config)
            _, output = plugin.__render_vite_config__()
            
            # Basic syntax checks
            assert output.count("{") == output.count("}")
            assert output.count("[") == output.count("]")
            assert output.count("(") == output.count(")")
            
            # Check that RawJS content is not quoted
            assert "(id) => id.includes('node_modules') ? 'vendor' : null" in output
            assert "'(id) => id.includes('node_modules') ? 'vendor' : null'" not in output
            
            # Check that regular strings are quoted
            assert "port: 3000" in output
            assert "'3000'" not in output  # numbers shouldn't be quoted
