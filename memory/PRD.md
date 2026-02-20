# MyKalamaEnglish - PRD (Product Requirements Document)

## Description du Projet
Plateforme e-learning complète pour l'apprentissage de l'anglais, développée avec React (frontend), FastAPI (backend) et MongoDB (base de données).

## Personas Utilisateurs
- **Étudiants**: Apprennent l'anglais via cours en ligne, exercices, jeux et ressources multimédia
- **Professeurs**: Gèrent leurs étudiants, créent des cours, envoient des résumés et des liens de cours
- **Administrateur**: Gère les utilisateurs, les inscriptions, les prix et supervise la plateforme
- **Secrétaire**: Gère la facturation des professeurs et les reçus des étudiants

## Architecture Technique
```
/app/
├── backend/
│   ├── server.py              # API principale FastAPI
│   ├── config.py              # Configuration DB et utilitaires
│   ├── email_service.py       # Service d'emails
│   ├── websocket_manager.py   # Gestionnaire WebSocket temps réel
│   └── routes/                # Routes modulaires (extraction en cours)
│       ├── auth_routes.py     # Routes authentification extraites
│       ├── billing_routes.py  # Documentation routes facturation
│       └── course_summaries.py
├── frontend/
│   └── src/
│       ├── pages/             # Dashboards (Admin, Student, Teacher, Secretary)
│       ├── components/        # Composants réutilisables
│       │   ├── AdminAnalytics.js  # Graphiques avec recharts + tableau revenus éditable
│       │   └── AdminTrash.js      # Poubelle avec "Vider la poubelle"
│       ├── hooks/             # useNotifications.js
│       └── utils/             # Utilitaires (api.js, fileUrl.js)
```

## Fonctionnalités Implémentées (100% Complétées)

### Phase 1 - Core ✅
- ✅ Authentification JWT
- ✅ Dashboards multi-rôles
- ✅ Système de cours et de liens Google Meet
- ✅ Messagerie interne
- ✅ Gestion des documents

### Phase 2 - Fonctionnalités Avancées ✅
- ✅ Promo Ramadan (-10% avec code promo)
- ✅ Système de gamification (points, badges)
- ✅ Résumés de cours avec Q/R + messages vocaux
- ✅ Système de disponibilités étudiants
- ✅ Facturation avec bonus/déductions (sans TVA)

### Phase 3 - Janvier 2026 ✅
- ✅ Récapitulatif mensuel des heures pour admin
- ✅ Édition des réunions planifiées
- ✅ Double check bleu (accusés de lecture)
- ✅ Notifications WebSocket temps réel
- ✅ **Tableau de bord analytique** avec graphiques (recharts)
- ✅ **Bug documents résolu** - Nettoyage des fichiers invalides
- ✅ **Bug dashboards résolu** - Import Calendar corrigé

### Phase 4 - Janvier 2026 (Fork 2) ✅
- ✅ **Séparation des revenus Admin Analytics** - Graphique avec entrées (reçus élèves) vs sorties (paiements profs)
- ✅ **Suppression onglet "Cours" professeur** - Onglet retiré du TeacherDashboard.js
- ✅ **Filtre EUR/FCFA sur graphique revenus** - Basculement dynamique entre les deux devises
- ✅ **Nouveau système de déductions professeurs** :
  - Suppression de la TVA sur les bulletins de salaire
  - Déductions: 1 cours manqué = 5€ (EUR) ou 1500 FCFA
  - Bulletin de salaire affiche: Somme Initiale → Déductions → Somme Nette

### Phase 5 - Janvier 2026 (Fork 3) ✅
- ✅ **Stockage MongoDB pour les documents** - Les fichiers sont maintenant stockés en Base64 dans MongoDB
  - Résout le problème de perte des fichiers après déploiement
  - Endpoint: `/api/files/{file_id}` pour récupérer les fichiers
  - Limite: 15MB par fichier
- ✅ **Système de Cours Groupés** - Gestion des cours avec plusieurs étudiants (SUPPRIMÉ depuis Phase 7)

### Phase 6 - Janvier 2026 (Fork 4) ✅
- ✅ **Création d'étudiant par l'admin** - Formulaire complet dans l'espace admin
  - Champs: Prénom, Nom, Email, Téléphone (avec indicatif pays), Niveau, Prix, Devise, Mot de passe provisoire
  - Génération automatique de code Digika
  - Affichage des credentials après création avec option de copie
  - Endpoint: `POST /api/admin/create-student`
- ✅ **Tarification automatique** - Prix auto-rempli selon niveau et devise (30/01/2026)
  - Le champ "Prix" se met à jour dynamiquement quand le niveau ou la devise change
  - Récupération des prix depuis l'endpoint `/api/pricing`
  - Prix affichés dans le menu déroulant des niveaux (ex: "Débutant (76€)" ou "Débutant (13,500 FCFA)")
  - Composant: `CreateStudentForm.js`
- ✅ **Import CSV d'étudiants en masse** (30/01/2026)
  - Upload de fichier CSV avec drag & drop ou sélection manuelle
  - Colonnes supportées: prenom, nom, email, telephone, niveau, prix, devise (séparateur `;`)
  - Gestion intelligente: import, skip (doublons), erreurs avec rapport détaillé
  - Téléchargement d'un modèle CSV
  - Copie des credentials (individuel ou en masse)
  - Endpoints: `POST /api/admin/import-students-csv`, `GET /api/admin/csv-template`
  - Composant: `ImportStudentsCSV.js`
- ✅ **Système de jeux amélioré** (30/01/2026)
  - **Envoi à plusieurs étudiants** : Sélection individuelle ou "Tous les étudiants" en un clic
  - **Notifications automatiques** : L'étudiant reçoit une notification "🎮 Nouveau jeu assigné!"
  - **Nouveaux types de jeux** :
    - **Quiz** : Questions à choix multiples avec temps limite optionnel
    - **Memory** : Jeu de mémoire avec paires de mots (français/anglais)
  - Interface à onglets : Flashcards | Quiz | Memory | Scores
  - Endpoints ajoutés:
    - Quiz: `POST /api/teacher/create-quiz`, `POST /api/teacher/add-quiz-question`, `GET /api/teacher/my-quizzes`
    - Memory: `POST /api/teacher/create-memory-game`, `POST /api/teacher/add-memory-pair`, `GET /api/teacher/my-memory-games`
  - Composants mis à jour: `TeacherGames.js`, `StudentGamesAdvanced.js`

### Phase 7 - Février 2026 (Fork 5) ✅
- ✅ **Nettoyage UI Admin** (17/02/2026)
  - Suppression des onglets "Groupes" (pending-groups et group-courses) de AdminDashboard.js
  - Suppression des imports PendingGroupRegistrations et GroupCourses
  - Suppression du doublon de l'onglet "Poubelle"
- ✅ **Vider la poubelle** (17/02/2026)
  - Bouton "Vider la poubelle (X)" dans AdminTrash.js avec double confirmation
  - Endpoint: `DELETE /api/admin/empty-trash`
  - data-testid: `empty-trash-button`
- ✅ **Analytics - Heures par Trimestre** (17/02/2026)
  - Remplacement du graphique "Heures par Semaine" par "Heures par Trimestre"
  - Labels: T1 2025, T2 2025, T3 2025, T4 2025, T1 2026
  - API: `hours_by_semester` dans `/api/admin/analytics`
- ✅ **Analytics - Édition des revenus** (17/02/2026)
  - Tableau des revenus mensuels avec bouton d'édition (crayon) pour chaque mois
  - Modal d'édition avec champs: Entrées EUR/FCFA, Sorties EUR/FCFA
  - Endpoint: `POST /api/admin/update-revenue`
  - data-testid: `edit-revenue-{month}`

### Phase 8 - Février 2026 (Fork 6) ✅
- ✅ **Promo Ramadan** (20/02/2026)
  - Bannière: "🌙 PROMO RAMADAN : -10% sur tous les packs ! Code : RAMADAN2026 - Valable jusqu'au 20 mars 2026"
  - Code promo Stripe: `promo_1T2s9HI4faCc3GWYXTWySNJ1`
  - **K-Kid exclu de la promo** (pas de réduction sur le pack enfants)
  - RamadanPromoBanner.js mis à jour avec mention "(Hors Pack K-Kid)"
  - HomePage.js: Logique conditionnelle pour appliquer la promo uniquement aux packs non-K-Kid

- ✅ **Référence de facture FAC-YYYY-XXX** (20/02/2026)
  - Format: FAC-2026-001, FAC-2026-002, etc.
  - Générée automatiquement lors de la création d'un bulletin de salaire professeur
  - Visible dans l'espace secrétaire sur la liste des bulletins
  - Stockée dans le champ `invoice_ref` de la collection `teacher_payments`

- ✅ **Solde à venir (Professeur)** (20/02/2026)
  - Nouvelle section dans l'onglet "Mes Payes" du dashboard professeur
  - Disponible **uniquement à partir du 25 du mois**
  - Affiche le montant prévu avant la réception officielle du bulletin
  - Endpoint: `GET /api/teacher/upcoming-balance`
  - Message dynamique: "Disponible dans X jour(s)" ou montant si disponible

- ✅ **Logique de visibilité des bulletins** (20/02/2026)
  - Bulletin créé entre le **25 et 28** du mois → Visible dans "Mes Payes" **à partir du 29**
  - Bulletin créé **le 29+** → Visible immédiatement
  - Champs ajoutés: `visible_from` (date ISO), `status` ("pending" ou "visible")
  - Endpoint `GET /api/teacher/my-payments` filtre par date de visibilité

- ✅ **Profil spécial Ndeyemane (Secrétaire)** (20/02/2026)
  - Email: `ndeyemane.dieng@mykalamaenglish.com`
  - Mot de passe: `Teacherc209e87f`
  - Rôle: `teacher` avec interface limitée
  - **Titre**: "Espace Privé" (au lieu de "Espace Professeur")
  - **Pas de welcome gift** ni de lettre de bienvenue
  - **Pas de cartes statistiques** (étudiants, cours, messages)
  - **Onglets affichés (7)**: Club, Messages Admin, Horaires, News, Bibliothèque, Mes Payes, Profil
  - **Onglets masqués (9)**: Bienvenue, Étudiants, Dispo Étudiants, Liens Meet, Jeu, Vidéos K-Kid, Pointage, Documents, Résumés
  - Détection par email dans TeacherDashboard.js

- ✅ **Système de Congés Professeurs** (20/02/2026)
  - **Côté Professeur (Onglet Horaires)**:
    - Section bleue "🏖️ Demande de Congé"
    - Formulaire: Date début, Date fin, Motif (optionnel)
    - Bouton bleu "Envoyer la demande"
    - Liste des demandes avec statuts (En attente, Approuvé, Refusé)
    - Possibilité d'annuler une demande en attente
  - **Côté Admin (Nouvel onglet "Congés")**:
    - Liste des demandes en attente avec boutons Approuver/Refuser
    - Possibilité d'ajouter un commentaire
    - Historique des demandes traitées
    - Notifications automatiques à l'admin et au professeur
  - **Endpoints**:
    - `GET /api/teacher/my-leave-requests`
    - `POST /api/teacher/leave-request`
    - `DELETE /api/teacher/leave-request/{id}`
    - `GET /api/admin/leave-requests`
    - `POST /api/admin/leave-request/{id}/approve`
    - `POST /api/admin/leave-request/{id}/reject`
  - **Collection MongoDB**: `leave_requests`

## Tableau de Bord Analytique 📊

### Composants
- **Cartes de résumé** : Étudiants, Professeurs, Heures, **Revenus nets (avec badge EUR/FCFA cliquable)**
- **Évolution des inscriptions** : Graphique en aire (6 derniers mois)
- **Heures par Trimestre** : Graphique en barres (T1-T4 par année)
- **Revenus mensuels** : **Graphique à 2 lignes + sélecteur EUR/FCFA + tableau éditable**
- **Répartition par niveau** : Graphique circulaire
- **Classement des professeurs** : Top 5 par heures enseignées

### Endpoints
- `GET /api/admin/analytics?period=week|month|year`
  - Retourne: incoming_eur, outgoing_eur, net_eur (et équivalents FCFA)
  - revenue_by_month: chaque mois contient incoming_eur, outgoing_eur
  - hours_by_semester: heures groupées par trimestre
- `POST /api/admin/update-revenue` - Correction des données de revenus
- `DELETE /api/admin/empty-trash` - Vider la poubelle
- `GET /api/admin/check-documents-integrity`
- `POST /api/admin/cleanup-invalid-documents`

## Tests
- **Backend** : 100% (11/11 tests passés - iteration 7)
- **Frontend** : 100% (UI vérifiée)
- Rapport: `/app/test_reports/iteration_7.json`

## Credentials de Test
- Admin: admin@mykalamaenglish.com / adminco
- Secrétaire: secretaire@mykalamaenglish.com / kalamasecret
- Teacher (test): proftest.flashcards@mykalamaenglish.com / teacher123
- Ndeyemane (secrétaire): ndeyemane.dieng@mykalamaenglish.com / Teacherc209e87f

## Backlog Priorisé

### P0 - Critique
- [x] ~~Stockage persistant des documents~~ ✅ Résolu avec MongoDB
- [ ] Continuer refactorisation de server.py (>6000 lignes)

### P1 - Important
- [x] ~~Stratégie pour cours groupés~~ ✅ Implémenté puis supprimé
- [ ] Synchronisation factures avec Monday.com

### P2 - Normal
- [x] ~~Envoi de jeux par le professeur~~ ✅ Implémenté
- [ ] Export PDF/CSV des statistiques admin