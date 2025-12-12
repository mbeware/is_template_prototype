from flask import Flask, render_template, request, redirect
from config_loader import load_ui_config
from ui_renderer import prepare_context

app = Flask(__name__)

# In real implementation this is replaced with named pipe logic
LIVE_LOGS = ["Booting...", "Loading modules...", "Ready."]


@app.route("/")
def index():
    cfg = load_ui_config()
    ctx = prepare_context(cfg)
    return render_template("screen.html", **ctx)


# ----- MENU ACTION ---------------------------------------------------------
@app.route("/menu_action", methods=["POST"])
def menu_action():
    choice = request.form.get("choice")
    print(f"[FR] Menu sélectionné: {choice}")
    # TODO: send to service pipe
    return redirect("/")


# ----- TEXT INPUT ACTION ---------------------------------------------------
@app.route("/text_input_action", methods=["POST"])
def text_input_action():
    value = request.form.get("value")
    print(f"[FR] Texte reçu: {value}")
    # TODO: send to pipe
    return redirect("/")


# ----- TEXT BLOCK AUTO REFRESH ---------------------------------------------
@app.route("/refresh_block")
def refresh_block():
    idx = int(request.args.get("index", 1))
    # TODO: read actual logs from service FIFO
    return "\n".join(LIVE_LOGS)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
