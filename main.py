from web.app import app
from database import init_db
import os

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    init_db()
    app.run(debug=debug_mode, host="0.0.0.0", port=5000, threaded=False)
