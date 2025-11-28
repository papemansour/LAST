# Refactorisation de server.py

## Objectif
Diviser server.py (3670 lignes) en modules organisés par domaine fonctionnel.

## Structure proposée

```
/app/backend/
├── server.py (fichier principal, ~200 lignes)
├── routes/
│   ├── __init__.py
│   ├── auth.py (authentification: login, register, register-group, magic-code)
│   ├── admin.py (gestion admin: users, prices, pending groups, etc.)
│   ├── teacher.py (fonctionnalités professeur: send-link, send-document, sessions)
│   ├── student.py (fonctionnalités étudiant: my-links, my-documents, homework)
│   ├── club.py (Kalama Club: posts, events, comments)
│   ├── pricing.py (gestion des prix et codes promo)
│   ├── games.py (jeux et classements)
│   └── messaging.py (conversations, messages)
├── models/
│   └── models.py (tous les modèles Pydantic)
└── utils/
    ├── auth.py (JWT, password hashing, get_current_user)
    ├── email.py (envoi d'emails)
    └── notifications.py (création de notifications)
```

## Avantages
1. **Maintenabilité** : Code organisé et facile à naviguer
2. **Testabilité** : Modules indépendants plus faciles à tester
3. **Scalabilité** : Ajout de nouvelles fonctionnalités facilité
4. **Collaboration** : Plusieurs développeurs peuvent travailler en parallèle
5. **Performance** : Import sélectif des modules nécessaires

## État actuel
- ✅ Structure des dossiers créée
- ⏳ Extraction en cours des modèles Pydantic
- ⏳ Extraction des utilitaires
- ⏳ Division des routes par domaine
- ⏳ Mise à jour de server.py pour utiliser les nouveaux modules

## Prochaines étapes
1. Extraire les modèles Pydantic dans models/models.py
2. Extraire les utilitaires d'authentification dans utils/auth.py
3. Créer les fichiers de routes par domaine
4. Mettre à jour server.py pour importer depuis les nouveaux modules
5. Tester l'application après chaque étape

## Notes
- La refactorisation sera progressive pour ne pas casser l'application
- server.py original sera conservé temporairement comme backup
- Chaque module sera testé individuellement
