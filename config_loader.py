import tomllib

def load_ui_config(path="config/ui.toml"):
    with open(path, "rb") as f:
        return tomllib.load(f)
