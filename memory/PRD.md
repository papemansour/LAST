# MyKalamaEnglish - PRD (Product Requirements Document)

## Plateforme
E-learning platform pour l'apprentissage de l'anglais avec multi-dashboards (Admin, Professeur, Secretaire, Etudiant).

## Stack Technique
- **Frontend**: React + Tailwind CSS + Shadcn/UI
- **Backend**: FastAPI (Python) - Architecture modulaire avec routes separees
- **Base de donnees**: MongoDB
- **Paiements**: Stripe (liens de paiement)
- **Email**: AWS SES

## Architecture Backend (Refactorisee)
```
/app/backend/
  server.py          (177 lignes - orchestrateur slim)
  config.py          (DB, auth, JWT, security)
  models/schemas.py  (Modeles Pydantic)
  utils/helpers.py   (Fonctions utilitaires partagees)
  routes/
    auth.py          (9 routes - inscription, login, mot de passe)
    admin.py         (55 routes - gestion utilisateurs, analytics, etc.)
    secretary.py     (24 routes - facturation, reunions, rapports)
    teacher.py       (65 routes - sessions, liens Meet, documents)
    student.py       (30 routes - cours, jeux, progression, recus)
    club.py          (18 routes - posts, evenements, leaderboard)
    news.py          (9 routes - actualites)
    notifications.py (7 routes - notifications utilisateurs)
    misc.py          (52 routes - pricing, promo codes, paiements, uploads)
```

## Fonctionnalites Implementees

### Authentification et Roles
- [x] Login multi-roles (Admin, Professeur, Secretaire, Etudiant)
- [x] Login secretaire par code
- [x] Changement de mot de passe
- [x] Lettre de bienvenue personnalisee par niveau
- [x] Deconnexion synchronisee via useAuth Context

### Dashboard Admin
- [x] Gestion des utilisateurs (CRUD, approbation, corbeille)
- [x] Analytics globales (etudiants, professeurs, inscriptions)
- [x] Gestion des conges
- [x] Recapitulatif mensuel des heures des professeurs
- [x] Gestion des questions de test par niveau
- [x] Badges et defis hebdomadaires

### Dashboard Professeur
- [x] Gestion des liens Google Meet
- [x] Systeme de pointage (chronometre, pauses)
- [x] Documents et cours
- [x] Bulletins de salaire (Mes Payes)
- [x] Demandes de conges
- [x] Disponibilites

### Dashboard Secretaire
- [x] Facturation professeurs (bulletins de salaire)
- [x] Recus etudiants (avec notification au student)
- [x] Factures prestataires
- [x] Reunions et rapports
- [x] Statistiques de facturation

### Dashboard Etudiant
- [x] Onglet Bienvenue avec lettre personnalisee
- [x] Kalama Club (posts, evenements, leaderboard)
- [x] Mon Pack (details du forfait)
- [x] **Paye (Recus de paiement)** - NOUVEAU
- [x] Liens de cours (Google Meet)
- [x] Disponibilites
- [x] Jeux educatifs (Flashcards, Quiz, Memory)
- [x] Messages / Conversations
- [x] Documents
- [x] Resumes de cours
- [x] Progression et defis
- [x] News
- [x] Kalamatheque (bibliotheque)
- [x] Profil
- [x] Coffre aux tresors (points)

### Tests de Niveau
- [x] 20 questions debutant (MCQ) - personnalisees
- [x] 20 questions intermediaire (MCQ) - personnalisees
- [x] 20 questions avance (MCQ)
- [x] Systeme de soumission et scoring

### Systeme de Pointage (Assiduite)
- [x] Chronometre avec pauses pour les professeurs
- [x] Enregistrement des sessions avec nom/email
- [x] Recapitulatif mensuel admin avec heures/sessions par professeur

## Taches Restantes

### P1 - Priorite Haute
- [ ] Synchroniser les factures avec Monday.com

### P2 - Priorite Moyenne
- [ ] Export PDF/CSV des statistiques admin

### Backlog
- [ ] Ameliorations UI/UX selon retours utilisateur

## Derniere Mise a Jour
- Date: 16 Avril 2026
- Refactorisation complete du backend (8448 -> 177 lignes server.py)
- Ajout onglet Paye pour les etudiants
- 20 questions intermediaires personnalisees ajoutees
- 20 questions debutant personnalisees ajoutees
- Correction du mapping des champs dans la creation des recus etudiants
