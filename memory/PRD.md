# MyKalamaEnglish - PRD

## Plateforme
E-learning platform pour l'apprentissage de l'anglais avec multi-dashboards (Admin, Professeur, Secretaire, Etudiant).

## Stack Technique
- Frontend: React + Tailwind CSS + Shadcn/UI
- Backend: FastAPI (Python) - Architecture modulaire
- Base de donnees: MongoDB
- Paiements: Stripe (liens de paiement)
- Email: AWS SES

## Architecture Backend
```
/app/backend/
  server.py          (177 lignes - orchestrateur)
  config.py          (DB, auth, JWT)
  models/schemas.py  (Modeles Pydantic)
  utils/helpers.py   (Fonctions utilitaires)
  routes/ auth.py, admin.py, secretary.py, teacher.py, student.py, club.py, news.py, notifications.py, misc.py
```

## Fonctionnalites Implementees

### Dashboard Admin (Fond Blanc + Glass Effect)
- [x] Interface glass-morphism fond blanc + backdrop-blur
- [x] Onglets teal unifies
- [x] Compteur de conges payes (2.5j/mois, max 30j/an)
- [x] Gestion utilisateurs, analytics, conges, tests

### Dashboard Secretaire
- [x] Onglet RH avec historique conges par employe (clic pour derouler)
- [x] Alertes solde conges (seuil <= 5 jours)
- [x] Facturation (profs, etudiants, prestataires)
- [x] **Fiche Employe** - Modal detaille avec email, role, anciennete, solde conges, historique (Decembre 2025)

### Dashboard Professeur
- [x] Carte compteur de conges payes
- [x] Pointage, Meet, Documents, Salaires

### Dashboard Etudiant
- [x] Onglet Paye (recus de paiement)
- [x] Club, Jeux, News, Kalamatheque

### Systeme de Conges Payes
- [x] 2.5 jours/mois, max 30j/an
- [x] Historique detaille par employe
- [x] Alertes automatiques quand solde <= 5 jours
- [x] Deduction auto a l'approbation

### Tests de Niveau (MISE A JOUR Decembre 2025)
- [x] 20 questions debutant MCQ personnalisees
- [x] 20 questions intermediaire MCQ personnalisees
- [x] 20 questions avance MCQ
- [x] **Feedback immediat** apres chaque question (correct/incorrect + bonne reponse)
- [x] **Blocage a la 5eme question** pour utilisateurs non connectes
- [x] **Affichage des packs** (K-Kid, K-Debutant, K-Intermediaire, K-Avance) dans l'ecran de blocage
- [x] Boutons S'inscrire / Se connecter / Retour au site
- [x] Protection contre double-clic sur validation
- [x] Score en temps reel affiche

### API Endpoints Cles
- `GET /api/tests/{level}` - Recupere les questions (sans reponses correctes)
- `POST /api/tests/check-answer` - Verifie une reponse individuelle (NEW)
- `POST /api/tests/submit` - Soumet le test complet
- `GET /api/admin/leave-balances` - Solde conges de tout le staff
- `GET /api/admin/leave-balance/{userId}` - Historique conges d'un employe

## Taches Restantes
- [ ] Sync factures Monday.com (P1)
- [ ] Export PDF/CSV stats admin (P2)
- [ ] Charger prix dynamiques depuis /api/pricing pour packs gate (P2)

## Derniere Mise a Jour: Decembre 2025
- Fiche Employe complete avec modal accessible
- Test de niveau avec feedback + blocage Q5 + packs dynamiques (API /pricing)
- Protection double-clic sur soumission
- Correction route /register vers /?openRegister=true#pricing
- Ajout accessibilite (aria-label, DialogDescription)
- Onglets secrétariat scrollables sur mobile (overflow-x-auto)
- Jauge utilisation congés alignée avec le pourcentage affiché
- Nullish coalescing pour prix API
- **Système Prestataires complet**: inscription, connexion par code, dépôt factures
- **Onglet Prestataires** dans secrétariat: recherche par code, validation paiements
- **Onglet RH amélioré**: Calendrier disponibilités, Fiches Professeurs (ancienneté), Fiches Étudiants (niveau)
- **Compteur congés 30j/an** avec possibilité d'annulation par admin
- Accents français corrigés dans l'interface

### Mise à jour Septembre 2026
- **Notification email secrétaire**: Email automatique envoyé lors du dépôt d'une facture prestataire
- **Filtre par service**: Dropdown pour filtrer les factures par type de service (INFORMATIQUE, COMMUNICATION, etc.)
- **Téléchargement facture PDF**: Bouton pour télécharger/imprimer les factures prestataires (format HTML stylisé)
- **Onglet "Payées"**: Nouvel onglet dédié aux factures payées avec historique complet
- **Correction 109 erreurs de linting**: Remplacement des imports star, suppression fonctions redéfinies
- **Badges service**: Affichage du type de service sur chaque facture
- **Statistiques améliorées**: Total payé en € affiché dans le dashboard

### Mise à jour Septembre 2026 (Suite)
- **Design facture premium**: Nouveau design professionnel avec dégradé, icônes par service, polices Google
- **Modification facture**: La secrétaire peut modifier les heures et le montant avec motif obligatoire
- **Refus de facture**: La secrétaire peut refuser une facture avec motif (email envoyé au prestataire)
- **Onglet "Refusées"**: Nouvel onglet pour voir les factures refusées avec motif
- **Historique modifications**: Affichage des modifications sur les factures (montant initial → nouveau)
- **Alerte modification dans PDF**: Le PDF affiche les détails de modification si la facture a été modifiée
- **Migration uploads vers MongoDB**: Les fichiers uploadés sont maintenant stockés en base de données (persistance)

### Mise à jour Septembre 2026 (Suite 2)
- **Couleurs uniformisées teal**: Dashboard prestataires avec couleurs teal comme les professeurs
- **Suppression onglet Comptes Rendus**: Onglet retiré du secrétariat
- **Suppression section Factures Prestataires/Organismes**: Section supprimée de l'onglet Facturation
- **Gestion prestataires**: La secrétaire peut modifier ou supprimer les prestataires
- **Attestation sur l'honneur**: Formulaire complet lors du dépôt de facture prestataire avec:
  - Champ nom/prénom
  - Sélecteur de service (même liste déroulante)
  - Lieu de la société (Paris par défaut)
  - Période de travail (date début → fin)
  - Lieu et date de signature
  - Signature automatique avec le nom saisi

### Mise à jour Septembre 2026 (Suite 3)
- **Avertissement Article 441-7**: Encadré rouge en bas de l'attestation rappelant les peines pour fausse attestation (1 an + 15000€, jusqu'à 3 ans + 45000€)
- **Format facture simplifié**: Design simple une page avec couleurs teal (même style que professeurs)
- **Suppression doublon Admin Kalama**: Nettoyage de la base de données pour ne garder qu'un seul admin


### Mise à jour Septembre 2026 (Suite 4) - Code Promo KALAMA2020
- **Code promo KALAMA2020**: Réduction de 20% sur tous les packs (K-Kid, K-Débutant, K-Intermédiaire, K-Professionnel)
- **Code promo Stripe**: `promo_1UGN8OI4faCc3GWYv1BVZFjd` appliqué automatiquement à tous les paiements EUR
- **Restriction par devise**: Le code promo est UNIQUEMENT applicable pour les paiements en EUR (pas FCFA)
- **Affichage dynamique**: Badge "-20% avec le code KALAMA2020" visible uniquement quand EUR est sélectionné
- **Saisie manuelle**: L'utilisateur peut aussi taper "KALAMA2020" manuellement

### Mise à jour Septembre 2026 (Suite 5) - Export Excel Étudiants
- **Export Excel Admin**: Bouton "Export Excel" dans l'onglet Étudiants du dashboard admin
- **Données exportées**: Prénom, Nom, Email, Téléphone, Niveau, Statut, Date d'inscription
- **Format**: Fichier .xlsx avec entêtes stylisées (couleur teal)
- **Endpoint API**: `GET /api/admin/export-students-excel`
- **Filtres disponibles**: 
  - Filtre par niveau (K-Kid, Débutant, Intermédiaire, Avancé/Professionnel)
  - Filtre par plage de dates (date début, date fin)
- **Modale de filtres**: Interface conviviale avec dropdown et date pickers

### Mise à jour Septembre 2026 (Suite 6) - Email de Bienvenue
- **Envoi automatique**: Email envoyé lors de la validation de l'inscription par l'admin
- **Objet**: "Hello and Welcome"
- **Contenu**:
  - Confirmation inscription avec niveau
  - Accès aux leçons interactives, formation flexible, accompagnement
  - Identifiants de connexion (email + mot de passe provisoire)
  - Accès Kalamathèque avec mot de passe "Digika"
  - Lien de connexion vers Mykalama
- **From**: mykalamaenglish.com (via AWS SES)


### Mise à jour Septembre 2026 (Suite 7) - Espace Chargé(e) de Communication
- **Nouveau rôle**: `communication` - Chargé(e) de communication avec dashboard dédié
- **Codes personnels**: MBM et FZT - Chaque chargé de com a son propre espace
- **Authentification en 2 étapes**: 
  1. Email + mot de passe (com@mykalamaenglish.com / COMKALAMA)
  2. Code personnel (MBM ou FZT) pour accéder à son espace
- **Dashboard Communication** (`/communication`):
  - Statistiques: Actualités, Étudiants, Jours disponibles, Jours occupés
  - Onglet Actualités: Créer, modifier, supprimer des news
  - Onglet Mes Disponibilités: Calendrier mensuel avec gestion des disponibilités
    - Statuts: Disponible, Occupé, Incertain
    - Heures de début/fin
    - Notes optionnelles
  - Onglet Statistiques: Métriques de communication
- **Endpoints API**:
  - `GET /api/communication/stats` - Statistiques
  - `GET/POST/DELETE /api/communication/availability/{com_code}` - Disponibilités par code
  - `POST /api/admin/create-staff` - Création compte staff
