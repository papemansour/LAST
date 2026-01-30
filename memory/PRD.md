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
│       │   └── AdminAnalytics.js  # Graphiques avec recharts
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

## Tableau de Bord Analytique 📊

### Composants
- **Cartes de résumé** : Étudiants, Professeurs, Heures, **Revenus nets (entrées/sorties)**
- **Évolution des inscriptions** : Graphique en aire (6 derniers mois)
- **Heures par semaine** : Graphique en barres
- **Revenus mensuels** : **Graphique à 2 lignes (Entrées en vert, Sorties en rouge)**
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
- Admin: admin@mykalamaenglish.com / admin123
- Teacher: proftest.flashcards@mykalamaenglish.com / teacher123

## Backlog Priorisé

### P0 - Critique
- [ ] Continuer refactorisation de server.py (>6000 lignes)

### P1 - Important
- [ ] Synchronisation factures avec Monday.com
- [ ] Stratégie pour cours groupés

### P2 - Normal
- [ ] Envoi de jeux par le professeur
- [ ] Export PDF/CSV des statistiques admin