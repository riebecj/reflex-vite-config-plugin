from pathlib import Path
from unittest.mock import MagicMock, patch

from reflex import constants

from vite_config_plugin import RawJS, ViteConfigPlugin


class TestViteConfigPluginIntegration:
    def test_complete_workflow_basic(self):
        user_config = {
            "plugins": [RawJS("customPlugin()")],
            "server": {"port": 4000},
            "build": {"outDir": "custom_dist"}
        }
        
        plugin = ViteConfigPlugin(user_config)
        
        # Test pre-compile hook
        mock_add_save_task = MagicMock()
        context = {"add_save_task": mock_add_save_task}
        plugin.pre_compile(**context)
        
        # Verify task was added
        mock_add_save_task.assert_called_once()
        
        # Test the actual task execution
        task_func = mock_add_save_task.call_args[0][0]
        file_path, content = task_func()
        
        # Verify output
        assert isinstance(file_path, type(Path()))
        assert isinstance(content, str)
        assert "export default defineConfig" in content
        assert "customPlugin()" in content
        assert "port: 4000" in content
        assert "outDir: 'custom_dist'" in content

    def test_workflow_with_complex_config(self):
        user_config = {
            "plugins": [
                RawJS("viteReact()"),
                RawJS("viteTsconfigPaths()")
            ],
            "server": {
                "port": 3000,
                "host": "0.0.0.0",
                "hmr": {"port": 24678}
            },
            "build": {
                "target": "es2020",
                "sourcemap": True,
                "rollupOptions": {
                    "external": ["react", "react-dom"],
                    "output": {
                        "manualChunks": RawJS("(id) => id.includes('node_modules') ? 'vendor' : null")
                    }
                }
            },
            "resolve": {
                "alias": [
                    {"find": "@", "replacement": "./src"},
                    {"find": "@components", "replacement": "./src/components"}
                ]
            }
        }
        
        plugin = ViteConfigPlugin(
            user_config,
            imports=['import { viteReact } from "@vitejs/plugin-react";']
        )
        
        with patch('vite_config_plugin.get_web_dir') as mock_get_web_dir:
            mock_get_web_dir.return_value = Path("/test/web/dir")
            file_path, content = plugin.__render_vite_config__()
            assert file_path == Path("/test/web/dir") / constants.ReactRouter.VITE_CONFIG_FILE

        
        # Verify complex features
        assert "viteReact()" in content
        assert "viteTsconfigPaths()" in content
        assert "port: 3000" in content
        assert "host: '0.0.0.0'" in content
        assert "target: 'es2020'" in content
        assert "sourcemap: true" in content
        assert "(id) => id.includes('node_modules') ? 'vendor' : null" in content
        
        # Verify imports
        assert 'import { viteReact } from "@vitejs/plugin-react";' in content
        
        # Verify alias handling
        assert "fileURLToPath" in content
        assert '"@"' in content
        assert '"@components"' in content

    def test_workflow_environment_variations(self):
        with patch('vite_config_plugin.environment') as mock_env:
            # Test with HMR disabled and full reload enabled
            mock_env.VITE_HMR.get.return_value = False
            mock_env.VITE_FORCE_FULL_RELOAD.get.return_value = True
            
            plugin = ViteConfigPlugin({})
            _, content = plugin.__render_vite_config__()
            
            # Should include fullReload plugin
            assert "fullReload()" in content
            
            # Test with different settings
            mock_env.VITE_HMR.get.return_value = True
            mock_env.VITE_FORCE_FULL_RELOAD.get.return_value = False
            
            plugin = ViteConfigPlugin({})
            _, content = plugin.__render_vite_config__()
            
            # Should have HMR enabled in server config
            assert "hmr: true" in content

    def test_workflow_frontend_path_variations(self):
        with patch('vite_config_plugin.get_config') as mock_get_config:
            # Test with empty frontend path
            mock_config = MagicMock()
            mock_config.frontend_path = ""
            mock_get_config.return_value = mock_config
            
            plugin = ViteConfigPlugin({})
            defaults = plugin.__set_defaults__()
            
            # Should use base "/"
            assert defaults["build"]["assetsDir"].code == '"/assets".slice(1)'
            
            # Test with custom frontend path
            mock_config.frontend_path = "app/frontend"
            
            plugin = ViteConfigPlugin({})
            defaults = plugin.__set_defaults__()
            
            # Should include frontend path
            assert "/app/frontend/" in defaults["build"]["assetsDir"].code


class TestErrorHandling:
    def test_invalid_config_types(self):
        plugin = ViteConfigPlugin({})
        
        # Test with None values
        result = plugin.__python_to_js__(None)
        assert result == "null"
        
        # Test with complex nested structures
        complex_config = {
            "nested": {
                "deeply": {
                    "values": [1, 2, {"key": RawJS("value")}]
                }
            }
        }
        result = plugin.__python_to_js__(complex_config)
        assert "value" in result  # RawJS should be unwrapped
        assert "'value'" not in result  # Should not be quoted

    def test_deep_merge_edge_cases(self):
        plugin = ViteConfigPlugin({})
        
        # Test merging with None values
        mergee = {"key": None}
        merger = {"key": "value"}
        result = plugin.__deep_merge__(mergee, merger)
        assert result["key"] is None
        
        # Test merging empty dicts
        result = plugin.__deep_merge__({}, {})
        assert result == {}
        
        # Test merging with list replacement
        mergee = {"list": [1, 2, 3]}
        merger = {"list": [4, 5, 6]}
        result = plugin.__deep_merge__(mergee, merger)
        assert result["list"] == [4, 5, 6] + [1, 2, 3]  # Should include all

    def test_alias_edge_cases(self):
        plugin = ViteConfigPlugin({})
        
        # Test with empty replacement
        aliases = [{"find": "@", "replacement": ""}]
        result = plugin.__alias_dict_to_js_array__(aliases)
        assert '""' in result.code
        
        # Test with special characters
        aliases = [{"find": "@special/path", "replacement": "./src/special-dir"}]
        result = plugin.__alias_dict_to_js_array__(aliases)
        assert "@special/path" in result.code
        assert "./src/special-dir" in result.code


class TestPerformance:
    def test_large_config_handling(self):
        # Create a large config with many plugins and options
        large_config = {
            "plugins": [RawJS(f"plugin{i}()") for i in range(100)],
            "build": {
                "rollupOptions": {
                    "output": {
                        f"chunk{i}": f"value{i}" for i in range(50)
                    }
                }
            },
            "resolve": {
                "alias": [
                    {"find": f"@alias{i}", "replacement": f"./src/path{i}"} 
                    for i in range(50)
                ]
            }
        }
        
        plugin = ViteConfigPlugin(large_config)
        
        # Should complete without errors
        _, content = plugin.__render_vite_config__()
        
        assert "plugin0()" in content
        assert "plugin99()" in content
        assert "@alias0" in content
        assert "@alias49" in content

    def test_deep_nesting_performance(self):
        nested_config = {"level1": {"level2": {"level3": {"level4": {"value": "deep"}}}}}
        
        plugin = ViteConfigPlugin(nested_config)
        result = plugin.__python_to_js__(nested_config)
        
        assert "value: 'deep'" in result
        assert result.count("{") == 5  # Should have correct nesting
