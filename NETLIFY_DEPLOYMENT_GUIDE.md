# 🚀 Guide de Déploiement MyKalamaEnglish sur Netlify

## ⚠️ ARCHITECTURE IMPORTANTE

Votre application est **full-stack** :
- **Frontend (React)** → Peut être sur Netlify ✅
- **Backend (FastAPI/Python)** → Doit rester sur Emergent ❌
- **Base de données (MongoDB)** → Doit rester sur Emergent ❌

---

## 📋 OPTION 1 : Frontend Netlify + Backend Emergent (RECOMMANDÉ)

### Étape 1 : Télécharger les fichiers

Le dossier build est prêt dans : `/app/frontend/build/`

**Contenu :**
- `index.html` (page principale)
- `static/` (JS, CSS, images)
- `uploads/` (fichiers uploadés)
- `netlify.toml` (configuration)

### Étape 2 : Créer un compte Netlify

1. Allez sur : https://www.netlify.com/
2. Créez un compte gratuit (GitHub, email, etc.)
3. Cliquez sur **"Add new site"** → **"Deploy manually"**

### Étape 3 : Déployer le build

**Option A : Drag & Drop**
1. Glissez-déposez tout le contenu du dossier `build/` sur Netlify
2. Attendez le déploiement (30-60 secondes)
3. Netlify vous donnera une URL : `https://random-name.netlify.app`

**Option B : Via CLI**
```bash
# Installer Netlify CLI
npm install -g netlify-cli

# Se connecter
netlify login

# Déployer
cd /app/frontend/build
netlify deploy --prod
```

### Étape 4 : Configurer les variables d'environnement

**CRITIQUE** : Le frontend doit pointer vers le backend Emergent !

Sur Netlify :
1. Allez dans **Site settings** → **Environment variables**
2. Ajoutez :
   ```
   REACT_APP_BACKEND_URL = https://mykalamaenglish.com
   ```
3. **Redéployez** le site pour que la variable soit prise en compte

### Étape 5 : Configurer le domaine personnalisé

Sur Netlify :
1. Allez dans **Domain settings**
2. Cliquez sur **"Add custom domain"**
3. Entrez : `www.mykalamaenglish.com` (utilisez le sous-domaine www)
4. Suivez les instructions DNS

**Configuration DNS sur Hostinger :**
```
Type : CNAME
Nom : www
Pointe vers : [votre-site].netlify.app
TTL : 14400
```

---

## 📋 OPTION 2 : Tout garder sur Emergent (DÉJÀ CONFIGURÉ)

✅ **Avantage** : Tout en un seul endroit
✅ **Pas de configuration supplémentaire**
✅ **Backend et Frontend communiquent directement**

Votre site est déjà accessible sur : **https://mykalamaenglish.com**

---

## 🔧 Configuration Backend (si vous choisissez Netlify)

Le backend REST sur Emergent. Vous devez :

1. **Garder Emergent actif** pour le backend
2. **Configurer CORS** sur le backend pour accepter les requêtes de Netlify

Dans `/app/backend/server.py`, la configuration CORS est déjà OK :
```python
CORS_ORIGINS = "*"  # Accepte tous les domaines
```

---

## 📊 Comparaison

| Critère              | Emergent (actuel) | Netlify Frontend + Emergent Backend |
|----------------------|-------------------|-------------------------------------|
| Coût                 | Emergent          | Gratuit (Netlify) + Emergent        |
| Complexité           | ⭐ Simple         | ⭐⭐⭐ Moyenne                       |
| Performance Frontend | Bonne             | ⭐⭐⭐ Excellente (CDN Netlify)     |
| SSL                  | ✅                | ✅                                  |
| Domaine personnalisé | ✅                | ✅                                  |

---

## 📁 Structure des fichiers pour Netlify

```
build/
├── index.html          ← Page principale
├── static/
│   ├── js/            ← JavaScript React compilé
│   └── css/           ← Styles CSS
├── uploads/           ← Fichiers uploadés
└── netlify.toml       ← Configuration Netlify
```

---

## 🆘 Dépannage

### Problème : Site vide ou erreur sur Netlify
→ Vérifiez que `REACT_APP_BACKEND_URL` est bien configuré

### Problème : Erreur CORS
→ Le backend Emergent doit être actif et accessible

### Problème : Les routes React ne fonctionnent pas
→ Le fichier `netlify.toml` doit être présent pour les redirections

---

## 📞 Support

- Netlify Docs : https://docs.netlify.com/
- Emergent Support : Via l'interface Emergent

---

## ✅ Checklist Netlify

- [ ] Compte Netlify créé
- [ ] Dossier `build/` téléchargé
- [ ] Site déployé sur Netlify
- [ ] Variable `REACT_APP_BACKEND_URL` configurée
- [ ] Backend Emergent actif et accessible
- [ ] Test du site sur l'URL Netlify
- [ ] (Optionnel) Domaine personnalisé configuré

---

**RECOMMANDATION FINALE :**

Si tout fonctionne déjà sur **https://mykalamaenglish.com** via Emergent, 
**gardez cette configuration**. C'est plus simple et tout fonctionne déjà !

Netlify est utile si vous voulez :
- Utiliser le CDN ultra-rapide de Netlify
- Séparer frontend et backend
- Avoir des déploiements automatiques via GitHub
