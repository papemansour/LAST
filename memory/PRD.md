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
    admin.py         (55+ routes - gestion utilisateurs, analytics, conges)
    secretary.py     (24 routes - facturation, reunions, rapports)
    teacher.py       (65+ routes - sessions, liens Meet, documents, conges)
    student.py       (30+ routes - cours, jeux, progression, recus)
    club.py          (18 routes - posts, evenements, leaderboard)
    news.py          (9 routes - actualites)
    notifications.py (7 routes - notifications utilisateurs)
    misc.py          (52 routes - pricing, promo codes, paiements, uploads)
```

## Fonctionnalites Implementees

### Authentification et Roles
- [x] Login multi-roles (Admin, Professeur, Secretaire, Etudiant)
- [x] Login secretaire par code (via useAuth context)
- [x] Changement de mot de passe
- [x] Lettre de bienvenue personnalisee par niveau
- [x] Deconnexion synchronisee via useAuth Context

### Dashboard Admin (Glass Effect)
- [x] Interface glass-morphism (fond sombre + backdrop-blur)
- [x] Onglets teal unifies
- [x] Gestion des utilisateurs (CRUD, approbation, corbeille)
- [x] Analytics globales
- [x] Compteur de conges payes (2.5j/mois, max 30j/an)
- [x] Gestion des conges avec deduction automatique
- [x] Gestion des questions de test par niveau

### Dashboard Professeur
- [x] Carte compteur de conges payes
- [x] Gestion des liens Google Meet
- [x] Systeme de pointage (chronometre, pauses)
- [x] Bulletins de salaire (Mes Payes)
- [x] Demandes de conges

### Dashboard Secretaire
- [x] Facturation professeurs / etudiants / prestataires
- [x] **Onglet RH** - Vue globale des conges de tous les employes
- [x] Table employes avec jauge conges (Acquis/Pris/Restants)
- [x] Reunions et rapports

### Dashboard Etudiant
- [x] Onglet Paye (recus de paiement)
- [x] Kalama Club, Jeux, News, Kalamatheque
- [x] Progression et coffre aux tresors

### Systeme de Conges Payes
- [x] 2.5 jours ouvrables par mois de travail effectif
- [x] Maximum 30 jours ouvrables par an (5 semaines)
- [x] Calcul automatique depuis la date de creation du compte
- [x] Deduction automatique lors de l'approbation d'un conge
- [x] Visible dans admin, professeur, et secretaire (RH)
- [x] Collection MongoDB: leave_balances

### Tests de Niveau
- [x] 20 questions debutant (MCQ) - personnalisees
- [x] 20 questions intermediaire (MCQ) - personnalisees
- [x] 20 questions avance (MCQ)

## Taches Restantes

### P1 - Priorite Haute
- [ ] Synchroniser les factures avec Monday.com

### P2 - Priorite Moyenne
- [ ] Export PDF/CSV des statistiques admin

## Derniere Mise a Jour: Decembre 2025
- Effet glass admin dashboard + couleur teal unifiee
- Systeme complet de conges payes (backend + frontend)
- Onglet RH dans le secretariat
- Fix login secretaire (useAuth context)
- Questions intermediaires personnalisees
