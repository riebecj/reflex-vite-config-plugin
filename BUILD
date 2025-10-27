python_requirements(
    name="pyproject",
    source="pyproject.toml",
)

files(
    name="build_files",
    sources=["pyproject.toml", "README.md", "LICENSE"],
)

python_distribution(
    name="reflex-vite-config-plugin",
    dependencies=["src/vite_config_plugin", ":build_files"],
    provides=python_artifact(),
    generate_setup = False,
)
