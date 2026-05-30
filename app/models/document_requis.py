from app import db


class DocumentRequis(db.Model):
    __tablename__ = 'document_requis'

    id_document = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(5), nullable=False)
    nom = db.Column(db.String(500), nullable=False)
    observation = db.Column(db.String(300))
    obligatoire = db.Column(db.Boolean, default=True)
    conditionnel = db.Column(db.Boolean, default=False)
    condition_texte = db.Column(db.String(300))

    def __repr__(self):
        return f'<Document {self.numero} — {self.nom[:40]}>'
