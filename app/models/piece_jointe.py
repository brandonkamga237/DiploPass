from app import db


class PieceJointe(db.Model):
    """Fichier déposé par un étudiant pour son dossier de diplomation."""
    __tablename__ = 'piece_jointe'

    id_piece = db.Column(db.Integer, primary_key=True)

    id_dossier = db.Column(
        db.Integer,
        db.ForeignKey('dossier_diplomation.id_dossier', ondelete='CASCADE'),
        nullable=False,
    )
    id_document_requis = db.Column(
        db.Integer,
        db.ForeignKey('document_requis.id_document'),
        nullable=True,
    )

    nom_original  = db.Column(db.String(255), nullable=False)
    cle_minio     = db.Column(db.String(500), nullable=False, unique=True)
    mime_type     = db.Column(db.String(100))
    taille_octets = db.Column(db.Integer)
    date_upload   = db.Column(db.DateTime, server_default=db.func.now())
    statut        = db.Column(db.String(20), default='DEPOSE')  # DEPOSE | VALIDE | REJETE

    document_requis = db.relationship('DocumentRequis', backref='pieces_deposees', lazy=True)

    @property
    def taille_lisible(self):
        if not self.taille_octets:
            return '—'
        kb = self.taille_octets / 1024
        if kb < 1024:
            return f'{kb:.0f} Ko'
        return f'{kb / 1024:.1f} Mo'

    @property
    def est_image(self):
        return self.mime_type in ('image/jpeg', 'image/png', 'image/webp', 'image/gif')

    @property
    def est_pdf(self):
        return self.mime_type == 'application/pdf'

    def __repr__(self):
        return f'<PieceJointe {self.id_piece} — {self.nom_original}>'
