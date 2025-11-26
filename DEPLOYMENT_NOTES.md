# MyKalamaEnglish - Notes de Déploiement

## Variables d'environnement requises pour le déploiement

### Backend (à configurer dans Emergent)
```
MONGO_URL=<sera fourni par Emergent avec MongoDB Atlas>
DB_NAME=kalamaenglish_db
JWT_SECRET=<générer une clé aléatoire sécurisée>
CORS_ORIGINS=*
AWS_ACCESS_KEY_ID=<votre clé AWS>
AWS_SECRET_ACCESS_KEY=<votre secret AWS>
AWS_REGION=us-east-1
AWS_SES_SENDER_EMAIL=papemansour01@gmail.com
EMERGENT_LLM_KEY=sk-emergent-c25Ef6bC93fBe8705A
KALAMATHEQUE_ACCESS_CODE=Digika
FRONTEND_URL=https://mykalamaenglish.com
```

### Frontend (à configurer dans Emergent)
```
REACT_APP_BACKEND_URL=https://mykalamaenglish.com
```

## Ports utilisés
- Frontend: 3000
- Backend: 8001

## Base de données
- MongoDB Atlas sera fourni automatiquement par Emergent
- Collection principale: users
- Base de données: kalamaenglish_db

## Modifications apportées pour le déploiement

1. ✅ Ajout de validation stricte pour JWT_SECRET (pas de fallback en production)
2. ✅ Renommage de SECRET_KEY en JWT_SECRET dans .env
3. ✅ Ajout de CORS_ORIGINS dans .env
4. ✅ Nettoyage des fichiers volumineux dans uploads/
5. ✅ Création de .dockerignore pour exclure les fichiers inutiles
6. ✅ Configuration supervisord.conf déjà présente

## Après le déploiement

1. Vérifier que l'application est accessible sur mykalamaenglish.com
2. Tester la connexion admin: admin@mykalamaenglish.com / adminco
3. Tester l'inscription de groupe
4. Vérifier les dashboards (Admin, Professeur, Étudiant, K-Kid)

## Support

En cas de problème de déploiement, vérifier :
- Les logs Kubernetes dans l'interface Emergent
- La configuration des variables d'environnement
- La propagation DNS du domaine mykalamaenglish.com
