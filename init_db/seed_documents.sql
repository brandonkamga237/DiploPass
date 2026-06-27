-- Seed des pièces requises pour la diplomation
-- Obligatoires (toujours) : 18, 26, 27, 28
-- Conditionnels / optionnels : tout le reste
-- Supprimés : 25 (Chemise cartonnée), 33 (Fiche de diplomation)

INSERT INTO document_requis (numero, nom, observation, obligatoire, conditionnel, condition_texte) VALUES
('18', 'Photocopie certifiée conforme de l''acte de naissance', 'A la mairie', true, false, NULL),
('19', 'Communiqué d''entrée en première année', 'A retirer à la scolarité de l''ENSET', false, true, 'Entrée en 1re année'),
('20', 'Communiqué d''admission sur titre (3e ou 4e année)', 'A retirer à la scolarité', false, true, 'Admis sur titre en 3e/4e'),
('21', 'Communiqué d''admission définitive (liste d''attente)', 'A retirer à la scolarité', false, true, 'Admis sur liste d''attente'),
('22', 'Communiqué d''admission directe en 4e année', 'A retirer à la scolarité', false, true, 'Admis sur titres supérieurs'),
('23', 'Photocopie du DIPET 1', 'A retirer à la scolarité', false, true, 'Tiers supérieur ou retour sur titre'),
('24', 'Communiqué de correction de filière ou de nom', 'A retirer à la scolarité', false, true, 'Si correction appliquée'),
('26', 'Photocopie certifiée conforme du Probatoire ou GCE OL', 'A la Préfecture', true, false, NULL),
('27', 'Photocopie certifiée conforme du Baccalauréat ou GCE AL', 'A la Préfecture', true, false, NULL),
('28', 'Photocopie certifiée du BTS/HND/DUT/Licence/Diplôme Ing.', 'A la Préfecture', true, false, NULL),
('29', 'Certificat d''individualité (variation de nom)', 'A la Mairie', false, true, 'Si variation de nom'),
('30', 'Certificat de conformité lieu de naissance', 'A la sous-préfecture', false, true, 'Si variation du lieu'),
('31', 'Certificat de conformité date de naissance', 'A la sous-préfecture', false, true, 'Si variation de date'),
('32', 'Photocopie simple du décret d''intégration', 'A la sous-préfecture', false, true, 'Uniquement fonctionnaires')
ON CONFLICT DO NOTHING;

-- Mise à jour des enregistrements déjà présents (si DB existante)
UPDATE document_requis SET obligatoire = false, conditionnel = true,
  condition_texte = 'Entrée en 1re année'
  WHERE numero = '19';
UPDATE document_requis SET obligatoire = false, conditionnel = true WHERE numero IN ('20','21','22','23','24');
UPDATE document_requis SET obligatoire = true, conditionnel = false, condition_texte = NULL WHERE numero IN ('26','27','28');
UPDATE document_requis SET obligatoire = false, conditionnel = true WHERE numero IN ('29','30','31','32');
-- Supprimer chemise cartonnée et fiche de diplomation
DELETE FROM document_requis WHERE numero IN ('25','33');
