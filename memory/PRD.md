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
│   ├── server.py          # API principale FastAPI (en cours de refactorisation)
│   ├── config.py          # Configuration
│   ├── email_service.py   # Service d'emails
│   └── routes/            # Routes modulaires (documentation prête)
│       ├── auth.py        # Documentation routes authentification
│       ├── billing.py     # Documentation routes facturation
│       └── course_summaries.py
├── frontend/
│   └── src/
│       ├── pages/         # Dashboards (Admin, Student, Teacher, Secretary)
│       ├── components/    # Composants réutilisables
│       └── utils/         # Utilitaires (api.js, fileUrl.js)
```

## Fonctionnalités Implémentées

### Phase 1 - Core (Complété)
- ✅ Authentification JWT
- ✅ Dashboards multi-rôles
- ✅ Système de cours et de liens Google Meet
- ✅ Messagerie interne
- ✅ Gestion des documents

### Phase 2 - Fonctionnalités Avancées (Complété)
- ✅ Promo Ramadan (-10% avec code promo)
- ✅ Système de gamification (points, badges)
- ✅ Résumés de cours avec Q/R
- ✅ Système de disponibilités étudiants
- ✅ Facturation avec bonus/déductions (sans TVA)

### Phase 3 - Janvier 2026 (Complété)
- ✅ Récapitulatif mensuel des heures pour admin
- ✅ Édition des réunions planifiées
- ✅ Messages vocaux dans Q/R des résumés
- ✅ Double check bleu (accusés de lecture)
- ✅ Onglets "Dispo Étudiants" pour admin et professeur
- 🔄 Refactorisation server.py (documentation prête)

## Dernières Modifications (28 Janvier 2026)

### Nouvelles Fonctionnalités
1. **AdminMonthlyHours** - Récapitulatif mensuel avec export CSV, classement professeurs
2. **Édition réunions** - Modal d'édition dans SecretaryDashboard
3. **PUT /api/secretary/meetings/{id}** - Endpoint mise à jour réunions
4. **PUT /api/student/mark-answer-read/{id}** - Marquage réponses lues

### Corrections de Bugs
1. **create_notification unifiée** - Fonction avec signature flexible
2. **Invalid Date corrigé** - Vérifications null sur dates d'assiduité
3. **Endpoint disponibilités** - Correction assigned_teacher

## Backlog Priorisé

### P0 - Critique
- [ ] Exécuter la refactorisation de server.py (documentation prête)
- [ ] Résoudre définitivement le bug de téléchargement de documents

### P1 - Important
- [ ] Synchronisation factures avec Monday.com
- [ ] Stratégie pour cours groupés

### P2 - Normal
- [ ] Envoi de jeux par le professeur

## Endpoints Clés

### Disponibilités
- `POST /api/student/set-availability`
- `GET /api/teacher/students-availability`
- `GET /api/admin/all-students-availability`

### Récap Mensuel
- `GET /api/admin/monthly-teacher-hours?month=X&year=Y`

### Facturation
- `POST /api/secretary/teacher-payments` (avec bonus/déductions)
- `PUT /api/secretary/meetings/{id}`

### Q/R Résumés
- `PUT /api/student/mark-answer-read/{id}`
- `PUT /api/teacher/mark-question-read/{id}`

## Tests
- Tests automatisés: `/app/backend/tests/`
- Rapports: `/app/test_reports/iteration_2.json`
- Dernier taux de réussite: 100% (15/15 tests backend)