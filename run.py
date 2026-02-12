"""Development entry point — run with `python run.py`."""

from nestscout import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
