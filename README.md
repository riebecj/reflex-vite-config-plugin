# Reflex Vite Config Plugin

[![PyPI Version](https://img.shields.io/pypi/v/reflex-vite-config-plugin)](https://pypi.org/project/reflex-vite-config-plugin/)
[![Python Versions](https://img.shields.io/pypi/pyversions/reflex-vite-config-plugin)](https://pypi.org/project/reflex-vite-config-plugin/)
[![License](https://img.shields.io/github/license/riebecj/reflex-vite-config-plugin)](https://github.com/riebecj/reflex-vite-config-plugin/blob/main/LICENSE)

A Reflex `rx.Config()` plugin that allows you to fully customize your Vite configuration using Python dictionaries. This plugin seamlessly integrates with Reflex's build system to provide complete control over Vite's build process, development server, and optimization settings.

## Table of Contents:
- [Quick Start](#quick-start)
    - [Installation](#installation)
    - [Basic Usage](#basic-usage)
    - [Advanced Configuration](#advanced-configuration)
- [Configuration Options](#configuration-options)
    - [Using RawJS](#using-rawjs-for-javascript-code)
    - [Custom Imports](#custom-imports)
    - [Custom Functions](#custom-functions)
- [API Reference](#api-reference)
- [Example](#example)
- [Contributing](#contributing)
- [Links](#links)
- [FAQ](#faq)

## Features

-  **Pythonic Configuration**: Define Vite configs using Python dictionaries with full type safety
-  **Complete Vite API Coverage**: Support for all Vite configuration options
-  **Raw JavaScript Support**: Embed raw JavaScript code where needed using the `RawJS` wrapper
-  **Reflex Default Merging**: Utilizes deep merging with Reflex's defaults
-  **Type Safety**: Type hints for all configuration options
-  **Development Tools**: Enhanced development server configuration

## Requirements

- Python 3.11+
- Reflex >= 0.8.17

## Quick Start

### Installation

```bash
pip install reflex-vite-config-plugin
```

### Basic Usage

```python
import reflex as rx
from vite_config_plugin import ViteConfigPlugin, RawJS

# Create your Vite configuration
vite_config = {
    "server": {
        "port": 4000,
        "host": "0.0.0.0"
    },
    "build": {
        "sourcemap": True,
        "target": "es2020"
    }
}

# Create and configure your app
app = rx.App(
    plugins=[
        ViteConfigPlugin(vite_config)
    ]
)
```

### Advanced Configuration

```python
from vite_config_plugin import ViteConfigPlugin, RawJS

# Advanced configuration with custom plugins and optimization
advanced_config = {
    "plugins": [
        RawJS("vue()"),
        RawJS("typescript()"),
    ],
    "server": {
        "port": 3000,
        "hmr": {
            "port": 24678,
            "overlay": True
        },
        "proxy": {
            "/api": "http://localhost:8000"
        }
    },
    "build": {
        "target": "es2020",
        "sourcemap": True,
        "rollupOptions": {
            "external": ["react", "react-dom"],
            "output": {
                "manualChunks": RawJS("""
                    (id) => {
                        if (id.includes('node_modules')) {
                            return 'vendor';
                        }
                    }
                """)
            }
        }
    },
    "resolve": {
        "alias": [
            {"find": "@", "replacement": "./src"},
            {"find": "@components", "replacement": "./src/components"},
            {"find": "@utils", "replacement": "./src/utils"}
        ]
    },
    "optimizeDeps": {
        "include": ["lodash", "axios"],
        "exclude": ["@my/custom-package"]
    }
}

# With custom imports
app = rx.App(
    plugins=[
        ViteConfigPlugin(
            advanced_config,
            imports=[
                'import vue from "@vitejs/plugin-vue";',
                'import typescript from "@rollup/plugin-typescript";'
            ]
        )
    ]
)
```

## Configuration Options

The plugin supports all Vite configuration options through typed dictionaries:

### Server Configuration
```python
{
    "server": {
        "host": "localhost",          # Server host
        "port": 3000,                 # Server port
        "strictPort": False,          # Strict port binding
        "https": {                    # HTTPS configuration
            "key": "/path/to/key.pem",
            "cert": "/path/to/cert.pem"
        },
        "proxy": {                    # Proxy configuration
            "/api": "http://localhost:8000",
            "/ws": {
                "target": "ws://localhost:8080",
                "ws": True
            }
        },
        "hmr": {                      # Hot Module Replacement
            "port": 24678,
            "overlay": True
        }
    }
}
```

### Build Configuration
```python
{
    "build": {
        "target": "es2020",           # Build target
        "outDir": "dist",             # Output directory
        "sourcemap": True,            # Generate sourcemaps
        "minify": "esbuild",          # Minification method
        "rollupOptions": {            # Rollup-specific options
            "external": ["react"],
            "output": {
                "format": "es"
            }
        },
        "lib": {                      # Library mode
            "entry": "./src/lib.ts",
            "name": "MyLib",
            "formats": ["es", "umd"]
        }
    }
}
```

### Module Resolution
```python
{
    "resolve": {
        "alias": [                    # Path aliases
            {"find": "@", "replacement": "./src"},
            {"find": "~", "replacement": "./"}
        ],
        "extensions": [".js", ".ts", ".jsx", ".tsx"],
        "mainFields": ["browser", "module", "main"]
    }
}
```

### CSS Configuration
```python
{
    "css": {
        "postcss": "./postcss.config.js",
        "preprocessorOptions": {
            "scss": {
                "additionalData": "$primary: #1976d2;"
            },
            "less": {
                "math": "parens-division"
            }
        }
    }
}
```

### Using RawJS for JavaScript Code

For configuration values that need to be raw JavaScript, use the `RawJS` wrapper:

```python
from vite_config_plugin import RawJS

vite_config = {
    "define": {
        "__VERSION__": RawJS("JSON.stringify(process.env.npm_package_version)"),
        "__DEV__": RawJS("process.env.NODE_ENV === 'development'")
    },
    "plugins": [
        RawJS("react()"),
        RawJS("viteTsconfigPaths()")
    ],
    "build": {
        "rollupOptions": {
            "output": {
                "manualChunks": RawJS("""
                    (id) => {
                        if (id.includes('node_modules')) {
                            if (id.includes('react')) {
                                return 'react-vendor';
                            }
                            return 'vendor';
                        }
                    }
                """)
            }
        }
    }
}
```

### Custom Imports

Add custom JavaScript imports to your Vite config:

```python
config = rx.Config(
    plugins=[
        ViteConfigPlugin(
            config,
            imports=[
                'import react from "@vitejs/plugin-react";',
                'import { resolve } from "path";',
                'import { defineConfig, loadEnv } from "vite";'
            ]
        )
    ]
)
```

### Custom Functions

Add custom JavaScript functions to your Vite config:

```python
func = """
function foo() {
    return 'bar';
}
"""
config = rx.Config(
    plugins=[
        ViteConfigPlugin(
            config,
            functions=[RawJS(func)]
        )
    ]
)
```

## API Reference

### ViteConfigPlugin

The main plugin class for Vite configuration.

```python
ViteConfigPlugin(
    config: ViteConfig,
    *,
    imports: list[str] | None = None,
    functions: list[RawJS] | None = None,
)
```

**Parameters:**
- `config`: A dictionary containing Vite configuration options
- `imports`: Optional list of JavaScript import statements
- `functions`: Optional list of `RawJS` objects containing Javascript functions used in the Vite config.

### RawJS

Wrapper for embedding raw JavaScript code in configuration.

```python
RawJS(code: str)
```

**Parameters:**
- `code`: Raw JavaScript code string

### Type Definitions

The plugin includes comprehensive TypeScript-style type definitions:

- `ViteConfig`: Main configuration type
- `Server`: Development server options
- `BuildOptions`: Build configuration
- `Resolve`: Module resolution settings
- `OptimizeDeps`: Dependency optimization
- And many more...

## Example

```python
import reflex as rx
from vite_config_plugin import ViteConfigPlugin, RawJS

config = rx.Config(
    plugins=[
        ViteConfigPlugin(
            {
                "plugins": [
                    RawJS("react()"),
                    RawJS("tsconfigPaths()")
                ],
                "build": {
                    "target": "es2020",
                    "sourcemap": True
                },
                "server": {
                    "port": 3000,
                    "open": True
                }
            },
            imports=[
                'import react from "@vitejs/plugin-react";',
                'import tsconfigPaths from "vite-tsconfig-paths";'
            ],
        ),
    ],
)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Prereuisites

This repository builds with [pantsbuild](https://www.pantsbuild.org/) which requires Linux or Mac. If you're on a Windows, you can use WSL.
Install `pants` using the [provided instructions](https://www.pantsbuild.org/stable/docs/getting-started/installing-pants) for your OS.

### Development Setup

1. Fork the repository and clone.
2. Install dependencies: `pants lock`
3. *Optionally* export a venv: `pants venv`. Creates `dist/export/python/virtualenvs/python-default/3.X.Y`.
4. If you run `pants venv` you can update your IDE interpreter using the available venv.

Now you can make code changes as necessary.

### Submitting a PR

Before you submit a PR, ensure the following run without errors:

1. Run tests: `pants test all`
2. Format code: `pants fmt all`
3. Lint code: `pants lint all`

## Links

- [PyPI Package](https://pypi.org/project/reflex-vite-config-plugin/)
- [GitHub Repository](https://github.com/riebecj/reflex-vite-config-plugin)
- [Reflex Documentation](https://reflex.dev)
- [Vite Documentation](https://vitejs.dev)

## FAQ

### Q: Can I use this plugin with existing Vite plugins?
A: Yes! You can include any Vite plugin using the `RawJS` wrapper in the `plugins` array.

### Q: How do I handle environment-specific configurations?
A: Use Python's environment variables and conditionals to create different configs for development/production.

### Q: Can I override the default Reflex Vite configuration?
A: That depends. The plugin uses deep `dict` merging, so MOST of your configuration will override defaults but lists of items are concantenated rather than overridden. That being said, it is ***not*** recommended to override Reflex's defaults as it can break Reflex/Vite in unexpected ways.

---

Made with ❤️ for the Reflex community
