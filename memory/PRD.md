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
  routes/ auth.py, admin.py, secretary.py, teacher.py, student.py, club.py, news.py, notifications.py, misc.py, kalamai.py, prestataire.py
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
- [x] **Fiche Employe** - Modal detaille avec email, role, anciennete, solde conges, historique
- [x] **Gestion Paie & Congés STAFFS** - Bulletin de salaire pour tous les staffs (Com + autres créés par admin)
- [x] **30 jours/an de congés pour STAFFS** - Avec solde visuel et gestion complète

### Dashboard Professeur
- [x] Carte compteur de conges payes
- [x] Pointage, Meet, Documents, Salaires

### Dashboard Etudiant
- [x] Onglet Paye (recus de paiement)
- [x] Club, Jeux, News, Kalamatheque
- [x] **Kalamai AI Tutor** - Chat conversationnel + Quiz adaptatif avec OpenAI

### Systeme de Conges Payes
- [x] 2.5 jours/mois, max 30j/an pour professeurs
- [x] 30 jours/an fixe pour STAFFS (Communication + autres)
- [x] Historique detaille par employe
- [x] Alertes automatiques quand solde <= 5 jours
- [x] Deduction auto a l'approbation

### Tests de Niveau
- [x] 20 questions debutant/intermediaire/avance MCQ
- [x] Feedback immediat apres chaque question
- [x] Blocage a la 5eme question pour utilisateurs non connectes
- [x] Affichage des packs dans l'ecran de blocage

### API Endpoints Cles - STAFFS (Nouveau Decembre 2025)
- `GET /api/secretary/all-staff` - Liste tous les staffs (communication + staff créés par admin)
- `GET /api/secretary/staff-payments` - Liste les paiements staffs
- `POST /api/secretary/staff-payments` - Créer un paiement staff (avec bonus/déductions)
- `DELETE /api/secretary/staff-payments/{id}` - Supprimer un paiement staff
- `GET /api/secretary/staff-leaves` - Liste les congés staffs
- `POST /api/secretary/staff-leaves` - Créer un congé staff
- `DELETE /api/secretary/staff-leaves/{id}` - Supprimer un congé staff

### API Endpoints Cles - Kalamai
- `POST /api/kalamai/chat` - Chat avec le tuteur IA
- `POST /api/kalamai/generate-quiz` - Génère un quiz adaptatif
- `GET /api/kalamai/history` - Historique des conversations

### Logo dans les Documents
- [x] **Logo sur la page d'accueil** - En haut à gauche avec "My KALAMA English"
- [x] **Logo dans les Reçus Étudiants** - printReceipt() avec logo MyKalama
- [x] **Logo dans les Fiches de Paie Professeurs** - printTeacherInvoice() avec logo MyKalama
- [x] **Logo dans les Factures Prestataires** - download_facture_pdf() avec logo MyKalama
- [x] **PAS de logo dans le Dashboard Communication** - Comme demandé par l'utilisateur

## Taches Restantes (Backlog)
- [ ] Refactoriser SecretaryDashboard.js (>2300 lignes) en sous-composants
- [ ] Refactoriser AdminDashboard.js (>2800 lignes)
- [ ] Sync factures Monday.com (P2)
- [ ] Export PDF/CSV stats admin (P2)

## Derniere Mise a Jour: Decembre 2025

### Mise à jour Décembre 2025 - Gestion STAFFS Complete
- **Endpoints STAFFS créés** : GET/POST/DELETE pour staff-payments et staff-leaves
- **UI STAFFS** : Section "Bulletin de Salaire - STAFFS" et "Gestion des Congés - STAFFS (30j/an)" dans l'onglet Facturation
- **Dropdown Staff** : Affiche tous les staffs (Communication + autres créés par admin)
- **Solde Congés Visuel** : Barre de progression colorée (vert >10j, jaune 5-10j, rouge <5j)
- **Logo dans Documents** : Ajouté dans printReceipt, printTeacherInvoice et factures prestataires

### Tarifs en vigueur (avec code KALAMA2020)
- Pack K-Kid : 30€ / 15,000 FCFA
- Pack Débutant : 80€ / 25,000 FCFA
- Pack Intermédiaire : 100€ / 35,000 FCFA
- Pack Avancé : 150€ / 50,000 FCFA

### Pack Groupe
- 2 personnes : 120€
- Personne supplémentaire : +30€
