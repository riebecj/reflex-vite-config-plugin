from vite_config_plugin import ( # pants: no-infer-dep
    Alias,
    BuildLibOptions,
    BuildOptions,
    CSS,
    HMROptions,
    HTML,
    HTTPSOptions,
    Json,
    ModulePreloadOptions,
    OptimizeDepsOptions,
    PreviewOptions,
    RawJS,
    Resolve,
    SSROptions,
    SSRResolveOptions,
    Server,
    ServerFsOptions,
    ViteConfig,
    WarmupOptions,
    WorkerOptions,
)


class TestTypeDefinitions:
    def test_alias_type(self):
        alias: Alias = {
            "find": "@",
            "replacement": "./src"
        }
        assert alias["find"] == "@"
        assert alias["replacement"] == "./src"
        
        # Test with RawJS
        alias_raw: Alias = {
            "find": RawJS("regex"),
            "replacement": RawJS("path")
        }
        assert isinstance(alias_raw["find"], RawJS)
        assert isinstance(alias_raw["replacement"], RawJS)

    def test_resolve_type(self):
        resolve: Resolve = {
            "alias": [{"find": "@", "replacement": "./src"}],
            "extensions": [".js", ".ts", ".jsx", ".tsx"],
            "preserveSymlinks": True
        }
        assert len(resolve["alias"]) == 1
        assert ".js" in resolve["extensions"]
        assert resolve["preserveSymlinks"] is True

    def test_html_type(self):
        html: HTML = {
            "cspNonce": "random-nonce-value"
        }
        assert html["cspNonce"] == "random-nonce-value"
        
        # Test with RawJS
        html_raw: HTML = {
            "cspNonce": RawJS("getNonce()")
        }
        assert isinstance(html_raw["cspNonce"], RawJS)

    def test_css_type(self):
        css: CSS = {
            "postcss": "./postcss.config.js",
            "preprocessorOptions": {
                "scss": {
                    "additionalData": "$primary: #123;"
                }
            },
            "preprocessorMaxWorkers": 4
        }
        assert css["postcss"] == "./postcss.config.js"
        assert css["preprocessorMaxWorkers"] == 4
        assert "scss" in css["preprocessorOptions"]

    def test_json_type(self):
        json_config: Json = {
            "namedExports": True,
            "stringify": "auto"
        }
        assert json_config["namedExports"] is True
        assert json_config["stringify"] == "auto"

    def test_https_options_type(self):
        https: HTTPSOptions = {
            "key": "/path/to/key.pem",
            "cert": "/path/to/cert.pem"
        }
        assert https["key"] == "/path/to/key.pem"
        assert https["cert"] == "/path/to/cert.pem"

    def test_hmr_options_type(self):
        hmr: HMROptions = {
            "protocol": "ws",
            "host": "localhost",
            "port": 24678,
            "path": "/vite-hmr",
            "timeout": 30000,
            "overlay": True,
            "clientPort": 3000
        }
        assert hmr["protocol"] == "ws"
        assert hmr["port"] == 24678
        assert hmr["overlay"] is True

    def test_warmup_options_type(self):
        warmup: WarmupOptions = {
            "clientFiles": ["./src/main.ts", "./src/app.tsx"],
            "ssrFiles": ["./src/entry-server.ts"]
        }
        assert len(warmup["clientFiles"]) == 2
        assert len(warmup["ssrFiles"]) == 1

    def test_server_fs_options_type(self):
        fs: ServerFsOptions = {
            "strict": True,
            "allow": [".."],
            "deny": [".env*"]
        }
        assert fs["strict"] is True
        assert ".." in fs["allow"]
        assert ".env*" in fs["deny"]

    def test_server_type(self):
        server: Server = {
            "host": "0.0.0.0",
            "port": 3000,
            "strictPort": False,
            "https": {
                "key": "key.pem",
                "cert": "cert.pem"
            },
            "open": True,
            "proxy": {
                "/api": "http://localhost:3001"
            },
            "cors": True,
            "headers": {
                "X-Custom-Header": "value"
            },
            "hmr": {
                "port": 24678
            },
            "warmup": {
                "clientFiles": ["./src/main.ts"]
            },
            "watch": {
                "ignored": ["node_modules/**"]
            },
            "middlewareMode": False,
            "fs": {
                "strict": True
            },
            "origin": "http://localhost:3000"
        }
        assert server["host"] == "0.0.0.0"
        assert server["port"] == 3000
        assert "/api" in server["proxy"]
        assert server["cors"] is True

    def test_module_preload_options_type(self):
        preload: ModulePreloadOptions = {
            "polyfill": True,
            "resolveDependencies": RawJS("(filename, deps) => deps")
        }
        assert preload["polyfill"] is True
        assert isinstance(preload["resolveDependencies"], RawJS)

    def test_build_lib_options_type(self):
        lib: BuildLibOptions = {
            "entry": "./src/lib.ts",
            "name": "MyLib",
            "formats": ["es", "cjs", "umd"],
            "fileName": "my-lib",
            "cssFileName": "style"
        }
        assert lib["entry"] == "./src/lib.ts"
        assert lib["name"] == "MyLib"
        assert "es" in lib["formats"]

    def test_build_options_type(self):
        build: BuildOptions = {
            "target": "es2015",
            "modulePreload": True,
            "outDir": "dist",
            "assetsDir": "assets",
            "assetsInlineLimit": 4096,
            "cssCodeSplit": True,
            "cssTarget": "chrome80",
            "cssMinify": "esbuild",
            "sourcemap": True,
            "rollupOptions": {
                "external": ["react"]
            },
            "lib": {
                "entry": "./src/lib.ts",
                "name": "MyLib"
            },
            "manifest": True,
            "ssrManifest": False,
            "ssr": "./src/entry-server.ts",
            "minify": "terser",
            "write": True,
            "emptyOutDir": True,
            "reportCompressedSize": True,
            "chunkSizeWarningLimit": 500
        }
        assert build["target"] == "es2015"
        assert build["outDir"] == "dist"
        assert build["sourcemap"] is True
        assert "react" in build["rollupOptions"]["external"]

    def test_preview_options_type(self):
        preview: PreviewOptions = {
            "host": "localhost",
            "port": 4173,
            "strictPort": True,
            "https": {
                "key": "key.pem",
                "cert": "cert.pem"
            },
            "open": "/dashboard",
            "proxy": {
                "/api": "http://localhost:3000"
            },
            "cors": False
        }
        assert preview["host"] == "localhost"
        assert preview["port"] == 4173
        assert preview["open"] == "/dashboard"

    def test_optimize_deps_options_type(self):
        optimize: OptimizeDepsOptions = {
            "entries": ["./src/main.ts"],
            "exclude": ["@my/dep"],
            "include": ["react", "react-dom"],
            "esbuildOptions": {
                "target": "es2020"
            },
            "force": True,
            "disabled": False
        }
        assert "./src/main.ts" in optimize["entries"]
        assert "@my/dep" in optimize["exclude"]
        assert "react" in optimize["include"]
        assert optimize["force"] is True

    def test_ssr_resolve_options_type(self):
        ssr_resolve: SSRResolveOptions = {
            "conditions": ["node"],
            "externalConditions": ["production"],
            "mainFields": ["main", "module"]
        }
        assert "node" in ssr_resolve["conditions"]
        assert "production" in ssr_resolve["externalConditions"]
        assert "main" in ssr_resolve["mainFields"]

    def test_ssr_options_type(self):
        ssr: SSROptions = {
            "external": ["react", "react-dom"],
            "noExternal": ["@my/lib"],
            "target": "node",
            "resolve": {
                "conditions": ["node"]
            }
        }
        assert "react" in ssr["external"]
        assert "@my/lib" in ssr["noExternal"]
        assert ssr["target"] == "node"

    def test_worker_options_type(self):
        worker: WorkerOptions = {
            "format": "es",
            "plugins": RawJS("[]"),
            "rollupOptions": {
                "external": ["worker-dependency"]
            }
        }
        assert worker["format"] == "es"
        assert isinstance(worker["plugins"], RawJS)
        assert "worker-dependency" in worker["rollupOptions"]["external"]

    def test_vite_config_type(self):
        config: ViteConfig = {
            "plugins": [RawJS("vue()")],
            "root": "./src",
            "base": "/app/",
            "mode": "development",
            "define": {
                "__VERSION__": '"1.0.0"'
            },
            "publicDir": "public",
            "cacheDir": "node_modules/.vite",
            "resolve": {
                "alias": [{"find": "@", "replacement": "./src"}]
            },
            "html": {
                "cspNonce": "nonce-value"
            },
            "css": {
                "postcss": "./postcss.config.js"
            },
            "json": {
                "namedExports": True
            },
            "server": {
                "port": 3000
            },
            "build": {
                "outDir": "dist"
            },
            "preview": {
                "port": 4173
            },
            "ssr": {
                "target": "node"
            },
            "worker": {
                "format": "es"
            }
        }
        
        # Verify all major sections are present and correct
        assert isinstance(config["plugins"][0], RawJS)
        assert config["root"] == "./src"
        assert config["base"] == "/app/"
        assert config["mode"] == "development"
        assert "__VERSION__" in config["define"]
        assert config["publicDir"] == "public"
        assert len(config["resolve"]["alias"]) == 1
        assert config["server"]["port"] == 3000
        assert config["build"]["outDir"] == "dist"


class TestTypeCompatibility:
    def test_partial_configs(self):
        # Empty config should be valid
        empty_config: ViteConfig = {}
        assert isinstance(empty_config, dict)
        
        # Partial config should be valid
        partial_config: ViteConfig = {
            "plugins": [RawJS("test()")]
        }
        assert len(partial_config) == 1

    def test_raw_js_in_all_contexts(self):
        config: ViteConfig = {
            "plugins": RawJS("[]"),  # As single value
            "base": RawJS("process.env.BASE_URL"),  # As string replacement
            "define": RawJS("{ __DEV__: process.env.NODE_ENV === 'development' }"),  # As object
            "server": {
                "port": RawJS("parseInt(process.env.PORT) || 3000"),  # As number replacement
                "host": RawJS("process.env.HOST || 'localhost'")  # In nested object
            }
        }
        
        # All should be RawJS instances
        assert isinstance(config["plugins"], RawJS)
        assert isinstance(config["base"], RawJS)
        assert isinstance(config["define"], RawJS)
        assert isinstance(config["server"]["port"], RawJS)
        assert isinstance(config["server"]["host"], RawJS)

    def test_literal_types(self):
        # Mode literals
        config_dev: ViteConfig = {"mode": "development"}
        config_prod: ViteConfig = {"mode": "production"}
        assert config_dev["mode"] == "development"
        assert config_prod["mode"] == "production"
        
        # Worker format literals
        worker_config: WorkerOptions = {"format": "es"}
        assert worker_config["format"] == "es"
        
        worker_config_iife: WorkerOptions = {"format": "iife"}
        assert worker_config_iife["format"] == "iife"
        
        # SSR target literals
        ssr_config: SSROptions = {"target": "node"}
        assert ssr_config["target"] == "node"
        
        ssr_config_worker: SSROptions = {"target": "webworker"}
        assert ssr_config_worker["target"] == "webworker"

    def test_union_types(self):
        # String or bool unions
        server_config: Server = {
            "host": True,  # bool option
            "open": "/dashboard"  # string option
        }
        assert server_config["host"] is True
        assert server_config["open"] == "/dashboard"
        
        # List or bool unions
        resolve_config: Resolve = {
            "dedupe": ["react"],  # list option
        }
        assert "react" in resolve_config["dedupe"]
        
        # String or False unions
        vite_config: ViteConfig = {
            "publicDir": False  # False option
        }
        assert vite_config["publicDir"] is False
