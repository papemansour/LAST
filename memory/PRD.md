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
│   ├── websocket_manager.py   # NEW: Gestionnaire WebSocket temps réel
│   └── routes/                # Routes modulaires (extraction en cours)
│       ├── auth_routes.py     # Routes authentification extraites
│       ├── billing_routes.py  # Documentation routes facturation
│       └── course_summaries.py
├── frontend/
│   └── src/
│       ├── pages/             # Dashboards (Admin, Student, Teacher, Secretary)
│       ├── components/        # Composants réutilisables
│       ├── hooks/             # NEW: useNotifications.js
│       └── utils/             # Utilitaires (api.js, fileUrl.js)
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
- ✅ **Notifications WebSocket temps réel**
- ✅ **Refactorisation server.py** (routes auth extraites)

## Notifications Temps Réel (WebSocket)

### Architecture
- **Backend**: `websocket_manager.py` gère les connexions WebSocket
- **Endpoint**: `/ws/notifications/{user_id}` pour les notifications push
- **Frontend**: `NotificationBell.js` avec indicateur de connexion (vert/rouge)

### Fonctionnement
1. L'utilisateur se connecte → WebSocket établi automatiquement
2. Étudiant pose une question → Notification push au professeur
3. Professeur répond → Notification push à l'étudiant
4. Ping/pong toutes les 30s pour maintenir la connexion
5. Reconnexion automatique après 5s si déconnecté

### Endpoints
- `WS /ws/notifications/{user_id}` - Connexion WebSocket
- `GET /api/ws/online-status` - Nombre d'utilisateurs en ligne

## Dernières Modifications (28 Janvier 2026)

### Nouvelles Fonctionnalités
1. **WebSocket Manager** - Gestionnaire de connexions temps réel
2. **Notifications Push** - Toast automatique pour nouvelles questions/réponses
3. **Indicateur de connexion** - Point vert/rouge dans NotificationBell
4. **Routes extraites** - auth_routes.py pour meilleure maintenabilité

### Corrections de Bugs
1. **Notification endpoints** - Corrigé `current_user.id` → `current_user['id']`
2. **create_notification unifiée** - Fonction avec signature flexible

## Backlog Priorisé

### P0 - Critique
- [x] ~~Notifications temps réel~~ ✅ FAIT
- [x] ~~Refactorisation server.py~~ ✅ EN COURS (auth extraites)
- [ ] Résoudre le bug de téléchargement de documents (données manquantes)

### P1 - Important
- [ ] Synchronisation factures avec Monday.com
- [ ] Stratégie pour cours groupés

### P2 - Normal
- [ ] Envoi de jeux par le professeur
- [ ] Continuer extraction des routes (billing, admin)

## Tests
- Tests automatisés: `/app/backend/tests/`
- Rapports: `/app/test_reports/iteration_3.json`
- Dernier taux de réussite: 100% (13/13 tests backend + frontend vérifié)