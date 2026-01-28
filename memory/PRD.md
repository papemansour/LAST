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
│   ├── server.py          # API principale FastAPI
│   ├── config.py          # Configuration
│   ├── email_service.py   # Service d'emails
│   └── routes/            # Routes modulaires (en cours de refactorisation)
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

### Phase 3 - En cours
- 🔄 Refactorisation server.py (monolithe >6000 lignes)
- 🔄 Refactorisation SecretaryDashboard.js
- ⏳ Récapitulatif mensuel des heures pour admin

## Dernières Modifications (Janvier 2026)

### Corrections de Bugs
1. **create_notification unifiée** - Fonction dupliquée avec signatures différentes → unifiée
2. **Invalid Date corrigé** - Ajout de vérifications null sur les dates d'assiduité
3. **Endpoint disponibilités** - Correction `teacher_id` → `assigned_teacher`

### Nouvelles Fonctionnalités
1. **Onglet "Dispo Étudiants"** dans TeacherDashboard et AdminDashboard
2. **Champs Bonus/Déductions** dans facturation (1 déduction = 5 EUR ou 2000 FCFA)
3. **Téléchargement PDF** des factures amélioré

## Backlog Priorisé

### P0 - Critique
- [ ] Terminer refactorisation server.py
- [ ] Terminer refactorisation SecretaryDashboard.js
- [ ] Résoudre définitivement le bug de téléchargement de documents

### P1 - Important
- [ ] Messages vocaux dans Q/R des résumés
- [ ] Double check bleu (accusés de lecture)
- [ ] Récapitulatif mensuel des heures pour admin
- [ ] Édition des réunions planifiées

### P2 - Normal
- [ ] Synchronisation factures avec Monday.com
- [ ] Stratégie pour cours groupés
- [ ] Envoi de jeux par le professeur

## Endpoints Clés

### Disponibilités
- `POST /api/student/set-availability` - Étudiant définit ses créneaux
- `GET /api/student/my-availability` - Récupère ses propres disponibilités
- `GET /api/teacher/students-availability` - Professeur voit les dispos de ses étudiants
- `GET /api/admin/all-students-availability` - Admin voit toutes les disponibilités

### Facturation
- `POST /api/secretary/teacher-payments` - Créer paiement avec bonus/déductions
- `GET /api/secretary/billing-stats` - Statistiques de facturation

## Variables d'Environnement Requises
```
# Backend (.env)
MONGO_URL=mongodb://localhost:27017
DB_NAME=kalamaenglish_db
JWT_SECRET=your-secret-key
FRONTEND_URL=https://...

# Frontend (.env)
REACT_APP_BACKEND_URL=https://...
```

## Tests
Les tests sont situés dans `/app/backend/tests/` et utilisent pytest.
Rapport de test le plus récent: `/app/test_reports/iteration_1.json`
