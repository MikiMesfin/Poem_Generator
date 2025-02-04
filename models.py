from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Poem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poem_text = db.Column(db.Text, nullable=False)
    creator_name = db.Column(db.String(100), nullable=True)
    recipient_relationship = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def __repr__(self):
        return f'<Poem {self.id}>' 