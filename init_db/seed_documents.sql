-- Seed des 16 pièces requises pour la diplomation (numéros 18 à 33)
INSERT INTO document_requis (numero, nom, observation, obligatoire, conditionnel, condition_texte) VALUES
('18', 'Photocopie certifiée conforme de l''acte de naissance', 'A la mairie', true, false, NULL),
('19', 'Communiqué d''entrée en première année', 'A retirer à la scolarité de l''ENSET', true, false, NULL),
('20', 'Communiqué d''admission sur titre (3e ou 4e année)', 'A retirer à la scolarité', true, true, 'Admis sur titre en 3e/4e'),
('21', 'Communiqué d''admission définitive (liste d''attente)', 'A retirer à la scolarité', true, true, 'Admis sur liste d''attente'),
('22', 'Communiqué d''admission directe en 4e année', 'A retirer à la scolarité', true, true, 'Admis sur titres supérieurs'),
('23', 'Photocopie du DIPET 1', 'A retirer à la scolarité', true, true, 'Tiers supérieur ou retour sur titre'),
('24', 'Communiqué de correction de filière ou de nom', 'A retirer à la scolarité', false, true, 'Si correction appliquée'),
('25', 'Chemise cartonnée contenant tous les documents', 'A remettre au Chef de Bureau', true, false, NULL),
('26', 'Photocopie certifiée conforme du Protocole ou GCE OL', 'A la Préfecture', true, false, NULL),
('27', 'Photocopie certifiée conforme du Baccalauréat ou GCE AL', 'A la Préfecture', true, false, NULL),
('28', 'Photocopie certifiée du BTS/HND/DUT/Licence/Diplôme Ing.', 'A la Préfecture', true, true, 'Entrée en 3e/4e année'),
('29', 'Certificat d''individualité (variation de nom)', 'A la Mairie', false, true, 'Si variation de nom'),
('30', 'Certificat de conformité lieu de naissance', 'A la sous-préfecture', false, true, 'Si variation du lieu'),
('31', 'Certificat de conformité date de naissance', 'A la sous-préfecture', false, true, 'Si variation de date'),
('32', 'Photocopie simple du décret d''intégration', 'A la sous-préfecture', false, true, 'Uniquement fonctionnaires'),
('33', 'Fiche de diplomation', 'A acheter à l''intendance', true, false, NULL)
ON CONFLICT DO NOTHING;
