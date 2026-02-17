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

## Tableau de Bord Analytique 📊

### Composants
- **Cartes de résumé** : Étudiants, Professeurs, Heures, **Revenus nets (avec badge EUR/FCFA cliquable)**
- **Évolution des inscriptions** : Graphique en aire (6 derniers mois)
- **Heures par semaine** : Graphique en barres
- **Revenus mensuels** : **Graphique à 2 lignes + sélecteur EUR/FCFA**
- **Répartition par niveau** : Graphique circulaire
- **Classement des professeurs** : Top 5 par heures enseignées

### Endpoints
- `GET /api/admin/analytics?period=week|month|year`
  - Retourne: incoming_eur, outgoing_eur, net_eur (et équivalents FCFA)
  - revenue_by_month: chaque mois contient incoming_eur, outgoing_eur
- `GET /api/admin/check-documents-integrity`
- `POST /api/admin/cleanup-invalid-documents`

## Tests
- **Backend** : 100% (10/10 tests passés - iteration 6)
- **Frontend** : 100% (UI vérifiée)
- Rapport: `/app/test_reports/iteration_6.json`

## Credentials de Test
- Admin: admin@mykalamaenglish.com / adminco
- Secrétaire: secretaire@mykalamaenglish.com / secretaireco
- Teacher (test): proftest.flashcards@mykalamaenglish.com / teacher123

## Backlog Priorisé

### P0 - Critique
- [x] ~~Stockage persistant des documents~~ ✅ Résolu avec MongoDB
- [ ] Continuer refactorisation de server.py (>6000 lignes)

### P1 - Important
- [x] ~~Stratégie pour cours groupés~~ ✅ Implémenté
- [ ] Synchronisation factures avec Monday.com

### P2 - Normal
- [ ] Envoi de jeux par le professeur
- [ ] Export PDF/CSV des statistiques admin