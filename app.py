from app.database.base import Base
from app.database.db import db
from app import *
from app.database import insert

app = create_app()

if __name__ == '__main__':
    Base.metadata.create_all(bind=db)
    app.run(debug=True)