from app.database.base import Base
from app.database.db import db
from app import create_app
from app.database import insert

import os

app = create_app()

UPLOAD_FOLDER = UPLOAD_FOLDER = os.path.join(os.path.abspath(os.curdir), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if __name__ == '__main__':
    Base.metadata.create_all(bind=db)
    app.run(debug=True)