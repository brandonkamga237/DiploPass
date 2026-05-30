import json
from datetime import datetime
from app import db
from app.models.etudiant import Etudiant
from werkzeug.security import generate_password_hash


def importer_etudiants_json(json_file, annee_academique=None):
    """
    Importe une liste de finissants depuis un fichier JSON.
    Si `annee_academique` est fournie (ex: "2024-2025"), elle est appliquée
    à tous les étudiants importés — sinon elle est lue dans chaque objet JSON.
    Les redoublants (matricule existant) voient leur annee_academique mise à jour.
    Mot de passe initial = matricule (sauf si le compte existe déjà).
    Retourne (nb_importes, nb_erreurs, details).
    """
    try:
        data = json.load(json_file)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return 0, 1, [f'Fichier JSON invalide : {e}']

    if not isinstance(data, list):
        return 0, 1, ["Le fichier JSON doit contenir un tableau d'objets."]

    importes, erreurs, details = 0, 0, []

    for item in data:
        try:
            matricule = item.get('matricule', '').strip()
            if not matricule:
                erreurs += 1
                details.append('Entrée ignorée : matricule manquant.')
                continue

            annee_val = annee_academique or item.get('annee_academique', '')

            existant = Etudiant.query.get(matricule)
            if existant:
                # Redoublant : on met à jour l'année de diplomation
                existant.annee_academique = annee_val
                details.append(f'{matricule} : redoublant mis à jour pour {annee_val}.')
                importes += 1
                continue

            date_naissance = None
            if item.get('date_naissance'):
                try:
                    date_naissance = datetime.strptime(item['date_naissance'], '%Y-%m-%d').date()
                except ValueError:
                    pass

            etu = Etudiant(
                matricule=matricule,
                nom=item.get('nom', '').upper(),
                prenom=item.get('prenom', ''),
                date_naissance=date_naissance or datetime(2000, 1, 1).date(),
                lieu_naissance=item.get('lieu_naissance', ''),
                filiere=item.get('filiere', ''),
                niveau=item.get('niveau'),
                cycle=item.get('cycle', 'LICENCE'),
                type_etudiant=item.get('type_etudiant', 'REGULIER'),
                statut_fonctionnaire=item.get('statut_fonctionnaire', False),
                sexe=item.get('sexe', ''),
                email=item.get('email'),
                telephone=item.get('telephone', ''),
                annee_academique=annee_val,
                mot_de_passe=generate_password_hash(matricule),
            )
            db.session.add(etu)
            importes += 1

        except Exception as e:
            erreurs += 1
            details.append(f"{item.get('matricule', '?')} : {str(e)}")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return 0, 1, [f'Erreur base de données : {str(e)}']

    return importes, erreurs, details
