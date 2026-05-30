"""
storage_service.py — Abstraction MinIO pour DigiPass

Toutes les opérations sur les fichiers (upload, URL signée, suppression)
passent par ce module. Changer de backend de stockage ne nécessite que
de modifier ce fichier.
"""
import os
import uuid
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

BUCKET = os.environ.get('MINIO_BUCKET', 'digipass')


def _client() -> Minio:
    return Minio(
        os.environ.get('MINIO_ENDPOINT', 'localhost:9000'),
        access_key=os.environ.get('MINIO_ACCESS_KEY', 'digipass'),
        secret_key=os.environ.get('MINIO_SECRET_KEY', 'digipass2026'),
        secure=os.environ.get('MINIO_SECURE', 'false').lower() == 'true',
    )


def _ensure_bucket(client: Minio) -> None:
    if not client.bucket_exists(BUCKET):
        client.make_bucket(BUCKET)


def upload_piece(file_obj, id_dossier: int, id_document: int | None,
                 nom_original: str, mime_type: str) -> str:
    """
    Stocke un fichier dans MinIO et retourne la clé de l'objet.

    Clé format : dossiers/{id_dossier}/{id_document}/{uuid}_{nom_original}
    """
    client = _client()
    _ensure_bucket(client)

    ext = nom_original.rsplit('.', 1)[-1].lower() if '.' in nom_original else 'bin'
    nom_safe = nom_original.replace(' ', '_')
    doc_folder = str(id_document) if id_document else 'autres'
    cle = f"dossiers/{id_dossier}/{doc_folder}/{uuid.uuid4().hex}_{nom_safe}"

    file_obj.seek(0, 2)        # aller à la fin
    taille = file_obj.tell()
    file_obj.seek(0)           # revenir au début

    client.put_object(
        BUCKET, cle, file_obj, taille,
        content_type=mime_type,
    )
    return cle, taille


def presigned_url(cle: str, expires_sec: int = 3600) -> str:
    """Retourne une URL signée valable `expires_sec` secondes."""
    client = _client()
    return client.presigned_get_object(
        BUCKET, cle, expires=timedelta(seconds=expires_sec)
    )


def supprimer(cle: str) -> None:
    """Supprime un objet de MinIO (ne lève pas d'erreur si absent)."""
    try:
        client = _client()
        client.remove_object(BUCKET, cle)
    except S3Error:
        pass


def verifier_connexion() -> bool:
    """Retourne True si MinIO est joignable."""
    try:
        client = _client()
        client.bucket_exists(BUCKET)
        return True
    except Exception:
        return False
