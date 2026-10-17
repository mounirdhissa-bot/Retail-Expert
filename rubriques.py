"""Définition des 5 rubriques d'audit et de leurs points de contrôle.

Chaque point est un tuple (code, aspect, zone de contrôle, critère, point critique).
Pour ajouter, retirer ou renommer un critère, il suffit de modifier ce fichier :
les formulaires, le calcul du score et l'enregistrement en base suivent.

Audit Caisse et Audit Responsable Magasin reprennent les grilles Excel
sources/fiche_audit_poissonnerie_v2.xlsx (onglets CHECK LISTE CAISSIER et
CHECK LIST RESPONSABLE MAGASIN). Les trois autres rubriques sont provisoires.
"""

# Évaluation : code -> (libellé, points obtenus ; None = exclu du calcul)
EVALUATIONS = {
    "C": ("Conforme", 2),
    "PC": ("Partiellement conforme", 1),
    "NC": ("Non conforme", 0),
    "NA": ("Non applicable", None),
}
POINTS_MAX = 2
COEF_CRITIQUE = 3  # coefficient d'un point critique, 1 sinon

# Seuils du résultat (score en %)
SEUIL_SATISFAISANT = 85
SEUIL_A_AMELIORER = 70


_CAISSE = [
    ('p01', 'Merchandising', 'Vitrines positives', 'Produits traiteur séparés des produits gourmet', False),
    ('p02', 'Merchandising', 'Vitrines positives', 'Produits soigneusement présentés', False),
    ('p03', 'Merchandising', 'Vitrines positives', 'Pinces de service disponibles et propres', False),
    ('p04', 'Merchandising', 'Vitrines positives', 'Aucun poisson ni objet non conforme dans la vitrine', False),
    ('p05', 'Merchandising', 'Vitrines positives', 'Vitrine propre (vitres, étagères, joints)', False),
    ('p06', 'Merchandising', 'Vitrines positives', 'Éclairage fonctionnel', False),
    ('p07', 'Merchandising', 'Vitrines positives', 'Température relevée entre 0 et +4 °C (noter la valeur en observation)', True),
    ('p08', 'Merchandising', 'Vitrines négatives', 'Présentation soignée', False),
    ('p09', 'Merchandising', 'Vitrines négatives', 'Crevettes séparées par calibre (40/50 séparée de la 60/70)', False),
    ('p10', 'Merchandising', 'Vitrines négatives', "Croustillant asiatique séparé de l'oriental", False),
    ('p11', 'Merchandising', 'Vitrines négatives', 'Vitrine propre, givre et morceaux de glace éliminés', False),
    ('p12', 'Merchandising', 'Vitrines négatives', 'Éclairage fonctionnel', False),
    ('p13', 'Merchandising', 'Vitrines négatives', 'Aucun produit non conforme (emballage abîmé, produit décongelé)', True),
    ('p14', 'Merchandising', 'Vitrines négatives', 'Température relevée à -18 °C ou moins (noter la valeur en observation)', True),
    ('p15', 'Merchandising', 'Balisage (frais, surgelé, traiteur)', 'Un balisage affiché devant chaque produit', False),
    ('p16', 'Merchandising', 'Balisage (frais, surgelé, traiteur)', 'Nom du produit et prix imprimés, jamais écrits à la main', False),
    ('p17', 'Merchandising', 'Balisage (frais, surgelé, traiteur)', "Aucune faute d'orthographe", False),
    ('p18', 'Merchandising', 'Balisage (frais, surgelé, traiteur)', 'Prix affiché identique au prix en caisse (vérifier 3 produits)', False),
    ('p19', 'Organisation de la caisse', 'Propreté de la caisse', "Aucune étiquette ni trace d'étiquette sur la caisse ou le matériel informatique", False),
    ('p20', 'Organisation de la caisse', 'Propreté de la caisse', 'Aucun papier par terre ou sur la caisse (tout est jeté à la poubelle)', False),
    ('p21', 'Organisation de la caisse', 'Propreté de la caisse', 'Caisse très bien nettoyée', False),
    ('p22', 'Organisation de la caisse', 'Rangement de la caisse', 'Uniquement le matériel de travail : unité centrale, écran, douchette, clavier, souris, TPE', False),
    ('p23', 'Organisation de la caisse', 'Rangement de la caisse', 'Sacs non tissés bien rangés sous la caisse', False),
    ('p24', 'Organisation de la caisse', 'Fond de caisse et monnaie', 'Fond de caisse de 1 000 DH présent', False),
    ('p25', 'Organisation de la caisse', 'Fond de caisse et monnaie', 'Monnaie disponible en permanence : tous types de pièces et de billets', False),
    ('p26', 'Organisation de la caisse', 'Flyers et fiches de réclamation', 'Fiches de réclamation et flyers exposés et visibles pour les clients', False),
    ('p27', 'Organisation de la caisse', 'Flyers et fiches de réclamation', 'Supports des flyers et fiches bien nettoyés', False),
    ('p28', 'Produits', 'Produits en attente', 'Produits en attente (clients, livreurs) conservés dans la chaîne du froid', True),
    ('p29', 'Produits', 'Barquettes contrôlées', 'Aucune barquette prête à remettre au client ne contient de jus de poisson (sinon retour au réemballage)', False),
    ('p30', 'Produits', 'Barquettes contrôlées', 'Chaque barquette porte la bonne étiquette, une seule étiquette par barquette', False),
    ('p31', 'Hygiène et accueil', 'Tenue et accueil', 'Tenue de travail propre et complète', False),
    ('p32', 'Hygiène et accueil', 'Tenue et accueil', 'Accueil client : salutation, amabilité, remerciement', False),
]

_RESPONSABLE_MAGASIN = [
    ('p01', 'Merchandising', 'Étal de poisson', 'Produits disposés en arc et de manière croisée', False),
    ('p02', 'Merchandising', 'Étal de poisson', 'Glace en contact avec le ventre du poisson', False),
    ('p03', 'Merchandising', 'Étal de poisson', 'Poisson bien visible, pas noyé sous la glace', False),
    ('p04', 'Merchandising', 'Étal de poisson', "Fond de l'étal non visible (glace suffisante)", False),
    ('p05', 'Merchandising', 'Étal de poisson', 'Étal bien rempli, sans espaces vides', False),
    ('p06', 'Merchandising', 'Étal de poisson', 'Calamar, filets et darnes jamais en contact direct avec la glace', False),
    ('p07', 'Merchandising', 'Étal de poisson', 'Filets de sardine, crevette décortiquée et calamaritos présentés en bacs perforés', False),
    ('p08', 'Merchandising', 'Étal de poisson', 'Aucun poisson de mauvaise qualité ou au mauvais visuel (œil bombé et brillant, branchies rouges, odeur marine, chair ferme)', True),
    ('p09', 'Merchandising', 'Étal de poisson', 'Glace renouvelée ; température du produit entre 0 et +2 °C (noter la valeur en observation)', True),
    ('p10', 'Merchandising', 'Coquillages et crustacés', 'Coquillages exposés dans des contenants en forme de bateau', False),
    ('p11', 'Merchandising', 'Coquillages et crustacés', 'Gambas cuites présentées en bacs perforés', False),
    ('p12', 'Merchandising', 'Coquillages et crustacés', 'Crevette royale, crevette grise, homard, langouste et cigale sur grilles inox ou aluminium', False),
    ('p13', 'Merchandising', 'Coquillages et crustacés', 'Produits nobles bien visibles, jamais mélangés aux produits non nobles', False),
    ('p14', 'Merchandising', 'Coquillages et crustacés', 'Coquillages vivants : étiquette sanitaire présente et conservée', True),
    ('p15', 'Merchandising', 'Balisage', 'Nom et prix placés derrière chaque produit (derrière la queue pour les poissons)', False),
    ('p16', 'Merchandising', 'Balisage', "Aucune faute d'orthographe", False),
    ('p17', 'Hygiène des locaux', 'Espace client', "Sol de l'espace client nettoyé avant 9h (vérifier la fiche de nettoyage)", False),
    ('p18', 'Hygiène des locaux', 'Espace client', 'Sol nettoyé à nouveau à 13h30/14h et à 18h (fiche de nettoyage signée)', False),
    ('p19', 'Hygiène des locaux', 'Espace client', 'Assises clients nettoyées avant 9h, mouches mortes et insectes éliminées', False),
    ('p20', 'Hygiène des locaux', 'Espace client', "Bois décoratif de l'étal et des vitrines très propre", False),
    ('p21', 'Hygiène des locaux', 'Espace client', 'Inox très propre, sans écailles', False),
    ('p22', 'Hygiène des locaux', 'Espace client', 'Caisses de stockage très propres', False),
    ('p23', 'Hygiène des locaux', 'Espace de travail', 'Sol propre, sans carcasses de poisson', False),
    ('p24', 'Hygiène des locaux', 'Espace de travail', 'Carcasses jetées uniquement dans les poubelles', False),
    ('p25', 'Hygiène des locaux', 'Espace de travail', 'Carcasses poissons nobles ou de roches conservée en caisse propre au frais', False),
    ('p26', 'Hygiène des locaux', 'Espace de travail', 'Planches de découpe propres', False),
    ('p27', 'Hygiène des locaux', 'Espace de travail', 'Aucune étiquette sur la balance ou les murs', False),
    ('p28', 'Hygiène des locaux', 'Espace de travail', 'Barquettes et matériel de travail bien rangés', False),
    ('p29', 'Hygiène des locaux', 'Espace de travail', "Machine d'emballage bien nettoyée", False),
    ('p30', 'Hygiène des locaux', 'Vestiaires et toilettes', "Vestiaires et toilettes nettoyés quotidiennement à l'eau de javel et au désodorisant", False),
    ('p31', 'Hygiène des locaux', 'Vestiaires et toilettes', 'Affaires du personnel rangées dans les casiers, pas de chaussures par terre', False),
    ('p32', 'Hygiène des locaux', 'Vestiaires et toilettes', 'Lave-mains équipé : savon et essuie-mains à usage unique', True),
    ('p33', 'Hygiène des locaux', 'Couloir et zone de réception', "Caisses rangées dans l'espace dédié", False),
    ('p34', 'Hygiène des locaux', 'Couloir et zone de réception', 'Caisses marché séparées des caisses de stockage', False),
    ('p35', 'Hygiène des locaux', 'Couloir et zone de réception', 'Aucune caisse contenant des produits dans les couloirs après 10h', True),
    ('p36', 'Hygiène des locaux', 'Couloir et zone de réception', 'Murs des couloirs et portes des chambres froides propres', False),
    ('p37', 'Hygiène des locaux', 'Couloir et zone de réception', 'Poignées des portes et afficheurs de température sans graisse ni écailles', False),
    ('p38', 'Hygiène du personnel', 'Tenue et comportement', 'Tenue de travail propre (lavée le jour de repos)', False),
    ('p39', 'Hygiène du personnel', 'Tenue et comportement', 'Coiffe portée, aucun bijou ni montre', True),
    ('p40', 'Hygiène du personnel', 'Tenue et comportement', 'Port de gants alimentaire en latex', True),
    ('p41', 'Hygiène du personnel', 'Tenue et comportement', "Lavage des mains entre chaque tâche (observé pendant l'audit)", True),
    ('p42', 'Hygiène du personnel', 'Tenue et comportement', 'Plaies et coupures protégées (pansement + gant)', True),
    ('p43', 'Produits', 'Produits en attente', "Aucun produit en attente plus de 10 min dans l'espace emballage", True),
    ('p44', 'Produits', 'Produits en attente', 'Commandes contrôlées et passées immédiatement à la caisse', False),
    ('p45', 'Produits', 'Barquettes contrôlées', 'Aucune barquette prête à transférer à la caisse ne contient de jus de poisson (sinon retour au réemballage)', False),
    ('p46', 'Produits', 'Barquettes contrôlées', 'Chaque barquette porte la bonne étiquette, une seule étiquette par barquette', False),
    ('p47', 'Sécurité alimentaire', 'Nettoyage et nuisibles', 'Plan de nettoyage affiché et fiches signées à jour', False),
    ('p48', 'Sécurité alimentaire', 'Nettoyage et nuisibles', 'Passage du prestataire anti-nuisibles à jour, aucun signe de nuisibles', True),
    ('p49', "Gestion de l'équipe", 'Organisation', 'Planning affiché et respecté', False),
    ('p50', 'Gestion commerciale', 'Suivi quotidien', 'Invendus et pertes enregistrés (fiche de casse)', False),
    ('p51', 'Gestion commerciale', 'Suivi quotidien', 'Réclamations clients enregistrées et traitées', False),
]

_ZONE_STOCKAGE = [
    ('rangement', 'Contrôles', 'Général', 'Zone rangée, allées dégagées', False),
    ('sol', 'Contrôles', 'Général', 'Aucune marchandise posée à même le sol', False),
    ('fifo', 'Contrôles', 'Général', 'Rotation des stocks respectée (FIFO / FEFO)', False),
    ('dlc', 'Contrôles', 'Général', 'Aucun produit à DLC dépassée', False),
    ('temp_froid', 'Contrôles', 'Général', 'Températures des chambres froides conformes', False),
    ('releves_temp', 'Contrôles', 'Général', 'Relevés de température enregistrés', False),
    ('separation', 'Contrôles', 'Général', "Séparation alimentaire / non alimentaire / produits d'entretien", False),
    ('etiquetage', 'Contrôles', 'Général', 'Étiquetage et traçabilité des lots', False),
    ('nuisibles', 'Contrôles', 'Général', 'Absence de nuisibles, plan de lutte à jour', False),
    ('proprete', 'Contrôles', 'Général', 'Propreté générale de la zone', False),
]

_CUISINE = [
    ('tenue_hygiene', 'Contrôles', 'Général', "Tenue d'hygiène complète (charlotte, blouse, gants)", False),
    ('mains', 'Contrôles', 'Général', 'Lavage des mains respecté, lave-mains équipé', False),
    ('plan_nettoyage', 'Contrôles', 'Général', 'Plan de nettoyage affiché et suivi', False),
    ('temp_cuisson', 'Contrôles', 'Général', 'Températures de cuisson contrôlées', False),
    ('refroidissement', 'Contrôles', 'Général', 'Refroidissement rapide maîtrisé', False),
    ('cru_cuit', 'Contrôles', 'Général', 'Séparation cru / cuit respectée', False),
    ('etiquetage', 'Contrôles', 'Général', 'Préparations étiquetées et datées', False),
    ('huiles', 'Contrôles', 'Général', 'Huiles de friture contrôlées', False),
    ('equipements', 'Contrôles', 'Général', 'Équipements propres et en bon état', False),
    ('dechets', 'Contrôles', 'Général', 'Gestion des déchets conforme', False),
]

_LABORATOIRE = [
    ('acces', 'Contrôles', 'Général', "Accès réservé et sas d'hygiène respecté", False),
    ('tenue', 'Contrôles', 'Général', 'Tenue de travail conforme', False),
    ('matieres', 'Contrôles', 'Général', 'Matières premières tracées (lots, fournisseurs)', False),
    ('fiches_tech', 'Contrôles', 'Général', 'Fiches techniques des recettes disponibles', False),
    ('pesees', 'Contrôles', 'Général', 'Pesées et dosages respectés', False),
    ('temperatures', 'Contrôles', 'Général', 'Températures des enceintes conformes', False),
    ('echantillons', 'Contrôles', 'Général', 'Échantillons témoins conservés', False),
    ('allergenes', 'Contrôles', 'Général', 'Allergènes identifiés et maîtrisés', False),
    ('nettoyage', 'Contrôles', 'Général', 'Nettoyage et désinfection réalisés', False),
    ('autocontroles', 'Contrôles', 'Général', 'Autocontrôles et analyses à jour', False),
]


RUBRIQUES = {
    "caisse": {
        "titre": "Audit Caisse",
        "couleur": "#2563EB",
        "icone": "point_of_sale",  # icône Material Symbols
        "description": "Grille Caissier : merchandising, organisation de la caisse, produits, hygiène et accueil.",
        "points": _CAISSE,
    },
    "responsable_magasin": {
        "titre": "Audit Responsable Magasin",
        "couleur": "#7C3AED",
        "icone": "storefront",  # icône Material Symbols
        "description": "Étal, hygiène des locaux et du personnel, produits, sécurité alimentaire, gestion.",
        "points": _RESPONSABLE_MAGASIN,
    },
    "zone_stockage": {
        "titre": "Audit Zone de stockage",
        "couleur": "#D97706",
        "icone": "inventory_2",  # icône Material Symbols
        "description": "Réserve, chambres froides, rotation et traçabilité des stocks (grille provisoire).",
        "points": _ZONE_STOCKAGE,
    },
    "cuisine": {
        "titre": "Audit Cuisine",
        "couleur": "#E11D48",
        "icone": "skillet",  # icône Material Symbols
        "description": "Hygiène, HACCP et bonnes pratiques de production (grille provisoire).",
        "points": _CUISINE,
    },
    "laboratoire": {
        "titre": "Audit Laboratoire",
        "couleur": "#0D9488",
        "icone": "science",  # icône Material Symbols
        "description": "Atelier de fabrication : hygiène, traçabilité et contrôles (grille provisoire).",
        "points": _LABORATOIRE,
    },
}
