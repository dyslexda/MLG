import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[0]))
from application import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0')
