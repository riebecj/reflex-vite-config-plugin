"""Vite configuration plugin for Reflex applications.

This module provides a plugin system for customizing Vite build configurations
in Reflex applications. The plugin allows users to specify Vite configuration
options using Python dictionaries and automatically converts them to valid
JavaScript configuration files for the Vite build system.
"""

import copy
import re
from typing import Any, Literal, TypedDict

from reflex import constants
from reflex.config import get_config
from reflex.environment import environment
from reflex.plugins.base import Plugin, PreCompileContext
from reflex.utils.prerequisites import get_web_dir


class RawJS:
    """A wrapper for raw JavaScript code to be embedded in configuration.

    Attributes:
        code (str): The raw JavaScript code to be embedded.
    """

    def __init__(self, code: str) -> None:
        """Initialize a RawJS wrapper with JavaScript code.

        Args:
            code: The raw JavaScript code to be embedded.
        """
        self.code = code


class Alias(TypedDict):
    """Configuration for module path aliases in Vite.

    Attributes:
        find: The module path pattern to find and replace.
        replacement: The replacement path for the matched pattern.
    """

    find: str | RawJS
    replacement: str | RawJS


class Resolve(TypedDict, total=False):
    """Configuration options for Vite module resolution.

    Attributes:
        alias: List of module path aliases for resolution.
        dedupe: List of packages to dedupe or raw JS configuration.
        conditions: List of export conditions for module resolution.
        mainFields: List of main fields to check during resolution.
        extensions: List of file extensions to resolve.
        preserveSymlinks: Whether to preserve symbolic links during resolution.
    """

    alias: list[Alias]
    dedupe: list[str] | RawJS
    conditions: list[str] | RawJS
    mainFields: list[str] | RawJS
    extensions: list[str] | RawJS
    preserveSymlinks: bool | RawJS


class HTML(TypedDict, total=False):
    """Configuration options for HTML handling in Vite.

    Attributes:
        cspNonce: Content Security Policy nonce for inline scripts and styles.
    """

    cspNonce: str | RawJS


class CSS(TypedDict, total=False):
    """Configuration options for CSS handling in Vite.

    Attributes:
        postcss: PostCSS configuration or plugin path.
        preprocessorOptions: Options for CSS preprocessors like Sass, Less, etc.
        preprocessorMaxWorkers: Maximum number of preprocessor workers or True for auto.
    """

    postcss: str | RawJS
    preprocessorOptions: dict[str, Any] | RawJS
    preprocessorMaxWorkers: int | Literal[True] | RawJS


class Json(TypedDict, total=False):
    """Configuration options for JSON handling in Vite.

    Attributes:
        namedExports: Whether to enable named exports for JSON imports.
        stringify: Whether to stringify JSON or use automatic handling.
    """

    namedExports: bool | RawJS
    stringify: bool | Literal["auto"] | RawJS


class HTTPSOptions(TypedDict):
    """Configuration options for HTTPS settings.

    Attributes:
        key: The private key for HTTPS configuration.
        cert: The certificate for HTTPS configuration.
    """

    key: str | RawJS
    cert: str | RawJS


class HMROptions(TypedDict, total=False):
    """Configuration options for Vite Hot Module Replacement (HMR).

    Attributes:
        protocol: The protocol to use for HMR connection.
        host: The host for HMR server.
        port: The port for HMR server.
        path: The path for HMR WebSocket connection.
        timeout: Timeout for HMR connection in milliseconds.
        overlay: Whether to show HMR error overlay.
        clientPort: The port for HMR client connection.
    """

    protocol: str | RawJS
    host: str | RawJS
    port: int | RawJS
    path: str | RawJS
    timeout: int | RawJS
    overlay: bool | RawJS
    clientPort: int | RawJS


class WarmupOptions(TypedDict, total=False):
    """Configuration options for Vite warmup settings.

    Attributes:
        clientFiles: List of client files to warmup.
        ssrFiles: List of SSR files to warmup.
    """

    clientFiles: list[str] | RawJS
    ssrFiles: list[str] | RawJS


class ServerFsOptions(TypedDict, total=False):
    """Configuration options for Vite server file system settings.

    Attributes:
        strict: Whether to enforce strict file system rules.
        allow: List of paths that are allowed to be served.
        deny: List of paths that are denied from being served.
    """

    strict: bool | RawJS
    allow: list[str] | RawJS
    deny: list[str] | RawJS


class Server(TypedDict, total=False):
    """Configuration options for Vite development server.

    Attributes:
        host: The host to bind the server to.
        allowedHosts: List of allowed hosts or True to allow all.
        port: The port number for the development server.
        strictPort: Whether to use strict port binding.
        https: HTTPS configuration options.
        open: Whether to open browser or specify URL to open.
        proxy: Proxy configuration for the development server.
        cors: CORS configuration settings.
        headers: Custom headers to send with responses.
        hmr: Hot Module Replacement configuration.
        warmup: Warmup configuration options.
        watch: File watching configuration.
        middlewareMode: Whether to run in middleware mode.
        fs: File system configuration options.
        origin: Origin URL for the server.
        sourcemapIgnoreList: Sourcemap ignore list configuration.
    """

    host: str | bool | RawJS
    allowedHosts: list[str] | Literal[True] | RawJS
    port: int | RawJS
    strictPort: bool | RawJS
    https: HTTPSOptions
    open: bool | str | RawJS
    proxy: dict[str, Any] | RawJS
    cors: bool | dict[str, Any] | RawJS
    headers: dict[str, str] | RawJS
    hmr: bool | HMROptions
    warmup: WarmupOptions
    watch: dict[str, Any] | None | RawJS
    middlewareMode: bool | RawJS
    fs: ServerFsOptions
    origin: str | RawJS
    sourcemapIgnoreList: Literal[False] | RawJS


class ModulePreloadOptions(TypedDict, total=False):
    """Configuration options for Vite module preload settings.

    Attributes:
        polyfill: Whether to polyfill module preload functionality.
        resolveDependencies: Custom function for resolving dependencies.
    """

    polyfill: bool | RawJS
    resolveDependencies: RawJS


class BuildLibOptions(TypedDict, total=False):
    """Configuration options for Vite library build settings.

    Attributes:
        entry: Entry point(s) for the library build.
        name: Name of the library for UMD/IIFE builds.
        formats: Output formats for the library build.
        fileName: Custom filename pattern for output files.
        cssFileName: Custom filename pattern for CSS files.
    """

    entry: str | list[str] | RawJS
    name: str | RawJS
    formats: list[Literal["es", "cjs", "umd", "iife"]] | RawJS
    fileName: str | RawJS
    cssFileName: str | RawJS


class BuildOptions(TypedDict, total=False):
    """Configuration options for Vite build settings.

    Attributes:
        target: Build target(s) for the output bundle.
        modulePreload: Module preload configuration options.
        polyfillModulePreload: Whether to polyfill module preload.
        outDir: Output directory for build files.
        assetsDir: Directory for static assets within outDir.
        assetsInlineLimit: Size limit for inlining assets as base64.
        cssCodeSplit: Whether to enable CSS code splitting.
        cssTarget: CSS build target(s).
        cssMinify: CSS minification method or boolean.
        sourcemap: Sourcemap generation options.
        rollupOptions: Additional Rollup configuration.
        commonjsOptions: CommonJS plugin options.
        dynamicImportVarsOptions: Dynamic import variables options.
        lib: Library build configuration.
        manifest: Whether to generate build manifest.
        ssrManifest: Whether to generate SSR manifest.
        ssr: SSR build configuration.
        emitAssets: Whether to emit assets during build.
        ssrEmitAssets: Whether to emit assets during SSR build.
        minify: Minification method or boolean.
        terserOptions: Terser minification options.
        write: Whether to write files to disk.
        emptyOutDir: Whether to empty output directory before build.
        copyPublicDir: Whether to copy public directory.
        reportCompressedSize: Whether to report compressed bundle sizes.
        chunkSizeWarningLimit: Warning threshold for chunk sizes in bytes.
        watch: File watching configuration for build mode.
    """

    target: str | list[str] | RawJS
    modulePreload: bool | ModulePreloadOptions | RawJS
    polyfillModulePreload: bool | RawJS
    outDir: str | RawJS
    assetsDir: str | RawJS
    assetsInlineLimit: int | RawJS
    cssCodeSplit: bool | RawJS
    cssTarget: str | list[str] | RawJS
    cssMinify: bool | Literal["esbuild", "lightningcss"] | RawJS
    sourcemap: bool | Literal["inline", "hidden"] | RawJS
    rollupOptions: dict[str, Any] | RawJS
    commonjsOptions: dict[str, Any] | RawJS
    dynamicImportVarsOptions: dict[str, Any] | RawJS
    lib: BuildLibOptions
    manifest: bool | str | RawJS
    ssrManifest: bool | str | RawJS
    ssr: bool | str | RawJS
    emitAssets: bool | RawJS
    ssrEmitAssets: bool | RawJS
    minify: bool | Literal["terser", "esbuild"] | RawJS
    terserOptions: dict[str, Any] | RawJS
    write: bool | RawJS
    emptyOutDir: bool | RawJS
    copyPublicDir: bool | RawJS
    reportCompressedSize: bool | RawJS
    chunkSizeWarningLimit: int | RawJS
    watch: None | dict[str, Any] | RawJS


class PreviewOptions(TypedDict, total=False):
    """Configuration options for Vite preview server.

    Attributes:
        host: The host to bind the preview server to.
        allowedHosts: List of allowed hosts or True to allow all.
        port: The port number for the preview server.
        strictPort: Whether to use strict port binding.
        https: HTTPS configuration options.
        open: Whether to open browser or specify URL to open.
        proxy: Proxy configuration for the preview server.
        cors: CORS configuration settings.
        headers: Custom headers to send with responses.
    """

    host: str | bool | RawJS
    allowedHosts: list[str] | Literal[True] | RawJS
    port: int | RawJS
    strictPort: bool | RawJS
    https: HTTPSOptions
    open: bool | str | RawJS
    proxy: dict[str, Any] | RawJS
    cors: bool | dict[str, Any] | RawJS
    headers: dict[str, str] | RawJS


class OptimizeDepsOptions(TypedDict, total=False):
    """Configuration options for Vite dependency optimization.

    Attributes:
        entries: Entry points for dependency optimization.
        exclude: Dependencies to exclude from optimization.
        include: Dependencies to include in optimization.
        esbuildOptions: Additional esbuild configuration options.
        force: Whether to force re-optimization of dependencies.
        noDiscovery: Whether to disable automatic dependency discovery.
        holdUntilCrawlEnd: Whether to hold optimization until crawl completion.
        disabled: Whether to disable dependency optimization entirely.
    """

    entries: str | list[str] | RawJS
    exclude: list[str] | RawJS
    include: list[str] | RawJS
    esbuildOptions: dict[str, Any] | RawJS
    force: bool | RawJS
    noDiscovery: bool | RawJS
    holdUntilCrawlEnd: bool | RawJS
    disabled: bool | Literal["build", "dev"] | RawJS


class SSRResolveOptions(TypedDict, total=False):
    """Configuration options for SSR module resolution in Vite.

    Attributes:
        conditions: List of conditions for module resolution.
        externalConditions: List of external conditions for module resolution.
        mainFields: List of main fields to check for module resolution.
    """

    conditions: list[str] | RawJS
    externalConditions: list[str] | RawJS
    mainFields: list[str] | RawJS


class SSROptions(TypedDict, total=False):
    """Configuration options for Server-Side Rendering (SSR) in Vite.

    Attributes:
        external: External dependencies to be excluded from bundling.
        noExternal: Dependencies that should not be externalized.
        target: The SSR build target environment.
        resolve: SSR-specific module resolution options.
    """

    external: list[str] | bool | RawJS
    noExternal: str | list[str] | Literal[True] | RawJS
    target: Literal["node", "webworker"]
    resolve: SSRResolveOptions


class WorkerOptions(TypedDict, total=False):
    """Configuration options for Vite worker build settings.

    Attributes:
        format: The output format for workers ("es" or "iife").
        plugins: Raw JavaScript plugins configuration.
        rollupOptions: Additional rollup configuration options.
    """

    format: Literal["es", "iife"]
    plugins: RawJS
    rollupOptions: dict[str, Any]


class ViteConfig(TypedDict, total=False):
    """Configuration options for Vite build tool.

    This TypedDict defines the structure for Vite configuration options,
    allowing partial specification of build settings, server options,
    and other Vite-related configurations.
    """

    plugins: list[RawJS] | RawJS
    root: str | RawJS
    base: str | RawJS
    mode: Literal["development", "production"] | RawJS
    define: dict[str, str | RawJS] | RawJS
    publicDir: str | Literal[False] | RawJS
    cacheDir: str | RawJS
    resolve: Resolve
    html: HTML
    css: CSS
    json: Json
    server: Server
    build: BuildOptions
    preview: PreviewOptions
    ssr: SSROptions
    worker: WorkerOptions


class ViteConfigPlugin(Plugin):
    """A Reflex plugin for customizing Vite configuration.

    This plugin allows customization of the Vite build configuration by merging
    user-provided configuration with sensible defaults. It handles conversion
    of Python configuration objects to JavaScript syntax for the vite.config.js file.

    Attributes:
        name (str): The plugin name identifier.
        config (dict[str, Any]): The Vite configuration dictionary.
        imports (list[str]): List of JavaScript import statements to include.
        functions (str): JavaScript helper functions for the Vite config.
    """

    name = "vite_config"

    def __init__(self, config: ViteConfig, *, imports: list[str] | None = None) -> None:
        """Initialize the ViteConfigPlugin with configuration and imports.

        Args:
            config: The Vite configuration dictionary to use.
            imports: Optional list of JavaScript import statements to include.
        """
        super().__init__()
        self.config = config
        self.imports = imports or []
        self.functions = """
// Ensure that bun always uses the react-dom/server.node functions.
function alwaysUseReactDomServerNode() {
  return {
    name: "vite-plugin-always-use-react-dom-server-node",
    enforce: "pre",

    resolveId(source, importer) {
      if (
        typeof importer === "string" &&
        importer.endsWith("/entry.server.node.tsx") &&
        source.includes("react-dom/server")
      ) {
        return this.resolve("react-dom/server.node", importer, {
          skipSelf: true,
        });
      }
      return null;
    },
  };
}

function fullReload() {
  return {
    name: "full-reload",
    enforce: "pre",
    handleHotUpdate({ server }) {
      server.ws.send({
        type: "full-reload",
      });
      return [];
    }
  };
}
        """

    def __set_defaults__(self) -> ViteConfig:
        """Set default configuration values for the Vite plugin."""
        self.imports = [
            'import { fileURLToPath, URL } from "url";',
            'import { reactRouter } from "@react-router/dev/vite";',
            'import { defineConfig } from "vite";',
            'import safariCacheBustPlugin from "./vite-plugin-safari-cachebust";',
            *self.imports,
        ]
        rxconfig = get_config()
        base = "/"
        if frontend_path := rxconfig.frontend_path.strip("/"):
            base += frontend_path + "/"

        default = {
            "plugins": [
                RawJS("alwaysUseReactDomServerNode()"),
                RawJS("reactRouter()"),
                RawJS("safariCacheBustPlugin()"),
            ],
            "build": {
                "assetsDir": RawJS(f'"{base}assets".slice(1)'),
                "rollupOptions": {
                    "jsx": {},
                    "output": {
                        "advancedChunks": {
                            "groups": [
                                {
                                    "test": RawJS("/env.json/"),
                                    "name": "reflex-env",
                                },
                            ],
                        },
                    },
                },
            },
            "experimental": {
                "enableNativePlugin": False,
            },
            "server": {
                "port": RawJS("process.env.PORT"),
                "hmr": bool(environment.VITE_HMR.get()),
                "watch": {
                    "ignored": [
                        "**/.web/backend/**",
                        "**/.web/reflex.install_frontend_packages.cached",
                    ],
                },
            },
            "resolve": {
                "mainFields": ["browser", "module", "jsnext"],
                "alias": [{"find": "@", "replacement": "./public"}, {"find": "$", "replacement": "./"}],
            },
        }
        if environment.VITE_FORCE_FULL_RELOAD.get():
            default["plugins"].append(RawJS("fullReload()"))
        return default

    def __python_to_js__(self, value: Any, indent: int = 0) -> str:  # noqa: ANN401
        """Convert a Python value to JavaScript literal syntax."""
        sp = " " * indent

        type_handlers = {
            RawJS: lambda v: v.code,
            dict: lambda v: self.__handle_dict__(v, sp, indent),
            list: lambda v: f"[{', '.join(self.__python_to_js__(item, indent + 1) for item in v)}]",
            str: lambda v: f"'{v}'",
            bool: lambda v: "true" if v else "false",
            type(None): lambda _: "null",
        }

        for value_type, handler in type_handlers.items():
            if isinstance(value, value_type):
                return handler(value)

        # Numeric / fallback
        return str(value)

    def __handle_dict__(self, value: dict, sp: str, indent: int) -> str:
        """Helper method to handle dictionary conversion to JavaScript object."""
        if set(value.keys()) and all(isinstance(k, str) for k in value):
            items = []
            for k, v in value.items():
                key = k if re.match(r"^[A-Za-z_$][A-Za-z0-9_$]*$", k) else f"'{k}'"
                items.append(f"{sp}  {key}: {self.__python_to_js__(v, indent + 1)}")
            return "{\n" + ",\n".join(items) + f"\n{sp}" + "}"
        return "{}"

    def __deep_merge__(self, mergee: dict, merger: dict) -> ViteConfig:
        """Deep merge two Vite configuration dictionaries.

        Args:
            mergee: The source configuration to merge from.
            merger: The target configuration to merge into, overwriting values.

        Returns:
            The merged configuration dictionary.
        """
        for k, v in mergee.items():
            if isinstance(v, dict) and isinstance(merger.get(k), dict):
                merger[k] = self.__deep_merge__(v, merger[k])
            elif isinstance(v, list):
                if k in merger:
                    merger[k].extend(v)
                else:
                    merger[k] = v
            else:
                merger[k] = v
        return merger

    def __alias_dict_to_js_array__(self, aliases: list[dict[str, str]], indent: int = 2) -> RawJS:
        """Convert a list of alias dictionaries to JavaScript array format.

        Args:
            aliases: List of dictionaries containing 'find' and 'replacement' keys.
            indent: Number of spaces for indentation (default: 2).

        Returns:
            RawJS object containing the JavaScript array representation.
        """
        if not aliases:
            return RawJS("[]")
        sp = "  " * indent
        lines = []
        for alias in aliases:
            safe_path = alias["replacement"].replace("\\", "/").replace('"', '\\"')
            converted_alias = (
                f'{sp}{{ find: "{alias["find"]}", '
                f'replacement: fileURLToPath(new URL("{safe_path}", import.meta.url)) }}'
            )
            lines.append(converted_alias)
        return RawJS("[\n" + ",\n".join(lines) + f"\n{sp * (indent - 1)}]")

    def __render_vite_config__(self) -> str:
        """Render a full JS Vite config file from a Python dict."""
        # Convert alias dict to array structure
        default_config = self.__set_defaults__()
        merged_config = self.__deep_merge__(copy.deepcopy(self.config), default_config)
        merged_config["resolve"]["alias"] = self.__alias_dict_to_js_array__(merged_config["resolve"]["alias"])

        vite_config = self.__python_to_js__(merged_config)
        imports = "\n".join(self.imports)
        vite_config = f"""{imports}

{self.functions}

export default defineConfig((config) => ({vite_config}));
        """
        return get_web_dir() / constants.ReactRouter.VITE_CONFIG_FILE, vite_config.strip()

    def pre_compile(self, **context: PreCompileContext) -> None:
        """Pre-compile hook to add Vite configuration generation task.

        Args:
            **context: Pre-compile context containing task management functions.
        """
        context["add_save_task"](self.__render_vite_config__)
