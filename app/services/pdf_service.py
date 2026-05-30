from flask import render_template, current_app
import io


def generer_diplome_pdf(dossier):
    """
    Génère un PDF du diplôme à partir du dossier de diplomation.
    Nécessite WeasyPrint installé avec ses dépendances système.
    """
    try:
        from weasyprint import HTML
        html_content = render_template('pdf/diplome.html', dossier=dossier)
        pdf_bytes = HTML(string=html_content, base_url=current_app.root_path).write_pdf()
        return io.BytesIO(pdf_bytes)
    except ImportError:
        raise RuntimeError('WeasyPrint non disponible.')
    except Exception as e:
        raise RuntimeError(f'Erreur génération PDF : {e}')
