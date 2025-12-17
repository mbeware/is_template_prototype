def prepare_context(config,registeredServices):
    
    return {
        "services": [registeredServices],
        "config": config.get("config", []),
        "title": config.get("title", ""),
        "subtitle": config.get("subtitle", ""),
        "menus": config.get("menu", []),
        "text_inputs": config.get("text_input", []),
        "text_blocks": config.get("text_block", []),
    }
