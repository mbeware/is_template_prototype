service_webui/
│
├── app.py
├── config_loader.py
├── ui_renderer.py
│
├── service_engine/
│   ├── router.py
│   └── pipes.py           # named pipe communication
│
├── config/
│   └── ui.toml
│
└── templates/
    ├── base.html
    ├── screen.html
    ├── widgets/
    │   ├── menu.html
    │   ├── text_input.html
    │   └── text_block.html
