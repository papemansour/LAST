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
