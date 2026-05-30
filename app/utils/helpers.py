from datetime import date


def annee_academique_courante():
    today = date.today()
    if today.month >= 9:
        return f'{today.year}-{today.year + 1}'
    return f'{today.year - 1}-{today.year}'


def format_date_fr(d):
    if not d:
        return ''
    mois = [
        '', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
        'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
    ]
    return f'{d.day} {mois[d.month]} {d.year}'
