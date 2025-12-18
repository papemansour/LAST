# 🎨 Charte Graphique - MyKalama English

## 📋 Informations Générales

**Nom de la marque :** MyKalama English  
**Slogan :** "Apprendre l'anglais facilement"  
**Secteur :** Éducation / Formation en ligne  
**Public cible :** Étudiants francophones (enfants, adolescents, adultes)

---

## 🎨 Palette de Couleurs

### Couleurs Principales

**Teal/Turquoise (Couleur dominante)**
- **Teal 600** : `#0d9488` - Boutons principaux, titres
- **Teal 700** : `#0f766e` - Hover states
- **Teal 800** : `#115e59` - Textes importants
- **Teal 50** : `#f0fdfa` - Arrière-plans clairs

**Rose/Pink (Couleur secondaire - Pack K-Kid)**
- **Pink 500** : `#ec4899` - Accents enfants
- **Pink 600** : `#db2777` - Hover states

### Couleurs d'Accentuation

**Vert (Succès, Promos)**
- **Green 600** : `#16a34a` - Messages de succès
- **Green 50** : `#f0fdf4` - Fonds de promo

**Orange/Jaune (Nouvel An, Alertes)**
- **Orange 500** : `#f97316` - Badges "NOUVEAU"
- **Yellow 500** : `#eab308` - Alertes importantes

**Bleu (Informations)**
- **Blue 600** : `#2563eb` - Liens, informations
- **Blue 50** : `#eff6ff` - Fonds informatifs

**Violet (Admin)**
- **Purple 600** : `#9333ea` - Interface admin
- **Purple 100** : `#f3e8ff` - Fonds admin

### Couleurs Neutres

- **Gray 50** : `#f9fafb` - Arrière-plans
- **Gray 100** : `#f3f4f6` - Cartes secondaires
- **Gray 600** : `#4b5563` - Textes secondaires
- **Gray 900** : `#111827` - Textes principaux
- **White** : `#ffffff` - Fonds blancs

---

## ✍️ Typographie

### Polices

**Police Principale :** System Font Stack (San Francisco, Segoe UI, Roboto, Arial)
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 
             'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
```

### Hiérarchie des Tailles

**Titres H1 (Hero)**
- Mobile : `text-4xl` (36px)
- Desktop : `text-6xl` (60px)
- Font-weight : `bold` (700)

**Titres H2 (Sections)**
- Mobile : `text-2xl` (24px)
- Desktop : `text-4xl` (36px)
- Font-weight : `bold` (700)

**Titres H3 (Sous-sections)**
- Mobile : `text-xl` (20px)
- Desktop : `text-2xl` (24px)
- Font-weight : `semibold` (600)

**Corps de Texte**
- Standard : `text-base` (16px)
- Font-weight : `normal` (400)

**Texte Secondaire**
- Taille : `text-sm` (14px)
- Couleur : Gray 600

---

## 🧩 Composants UI

### Boutons

**Bouton Principal (Call-to-Action)**
```
Couleur : Teal 600 (#0d9488)
Hover : Teal 700 (#0f766e)
Padding : px-6 py-3
Border-radius : rounded-lg (8px)
Font-weight : semibold (600)
```

**Bouton Secondaire (Outline)**
```
Border : 2px solid Teal 600
Couleur texte : Teal 600
Hover : Background Teal 50
```

**Bouton Don**
```
Gradient : Pink 500 → Red 500
Icon : Heart (❤️)
Shadow : lg
```

### Cartes (Cards)

**Style Standard**
```
Background : White
Border : 1px solid Gray 200
Border-radius : rounded-xl (12px)
Shadow : shadow-lg
Padding : p-6
```

**Effet Glace (Dashboards)**
```
Background : rgba(255, 255, 255, 0.1)
Backdrop-filter : blur(10px)
Border : 1px solid rgba(255, 255, 255, 0.2)
```

### Badges

**Nouveau**
```
Background : Orange 500
Couleur : White
Padding : px-2 py-1
Border-radius : rounded-full
Font-size : text-xs
```

**Promo**
```
Background : Green 600
Couleur : White
Font-weight : bold
```

---

## 🎭 Éléments Saisonniers

### Noël (jusqu'au 26 décembre)
- Emojis : 🎄 🎅 ❄️ ⛄ 🎁
- Couleurs : Rouge (#dc2626), Vert (#16a34a), Or (#fbbf24)
- Bannière : Background rouge pulsant

### Nouvel An (27 déc - 10 jan)
- Emojis : 🎉 🎊 🥳 🎆 ✨ 🎈
- Couleurs : Jaune → Orange gradient
- Animation : bounce, pulse

---

## 📱 Responsive Design

### Breakpoints TailwindCSS

- **Mobile** : < 640px (défaut)
- **Tablet** : ≥ 768px (md:)
- **Desktop** : ≥ 1024px (lg:)
- **Large Desktop** : ≥ 1280px (xl:)

### Règles Responsive

1. **Mobile First** : Design conçu d'abord pour mobile
2. **Touch Targets** : Minimum 44x44px pour les boutons
3. **Font Scaling** : Utilisation de `text-base` → `md:text-lg` → `lg:text-xl`
4. **Spacing** : Padding et margins adaptatifs avec `p-4` → `md:p-6` → `lg:p-8`

---

## 🎯 Identité Visuelle par Rôle

### 🎓 **Étudiant**
- Couleur principale : **Teal 600**
- Style : Moderne, épuré, encourageant
- Emojis : 📚 ✨ 🎯 🏆

### 👨‍🏫 **Professeur**
- Couleur principale : **Teal 700**
- Style : Professionnel, organisé
- Emojis : 📝 👥 📊 📧

### ⚙️ **Admin**
- Couleur principale : **Purple 600**
- Style : Fonctionnel, puissant
- Emojis : 🔧 📊 👥 📈

### 👶 **K-Kid (Enfants)**
- Couleur principale : **Pink 500**
- Style : Ludique, coloré, doux
- Emojis : 🎨 🎮 🌈 ⭐

---

## 🌟 Icônes et Illustrations

### Bibliothèque d'Icônes
**Lucide React** - Style minimaliste, cohérent

**Icônes Principales :**
- Navigation : `Home`, `Menu`, `User`, `LogOut`
- Actions : `Send`, `Download`, `Upload`, `Edit`, `Trash2`
- Contenus : `FileText`, `Image`, `Video`, `Book`
- Social : `MessageCircle`, `Users`, `Heart`

### Style des Icônes
- Stroke width : 2px
- Taille standard : `w-5 h-5` (20px)
- Taille grande : `w-6 h-6` (24px)
- Couleur : Hérite du texte parent

---

## 📐 Espacements et Grilles

### Système de Spacing (Tailwind)
- **xs** : `space-1` = 4px
- **sm** : `space-2` = 8px
- **md** : `space-4` = 16px
- **lg** : `space-6` = 24px
- **xl** : `space-8` = 32px

### Layout Grid
```
Container : max-w-7xl (1280px)
Padding : px-4 md:px-6 lg:px-8
Gap : gap-4 md:gap-6 lg:gap-8
```

---

## 🎬 Animations

### Transitions Standards
```css
transition-all duration-300 ease-in-out
```

### Animations Utilisées

**Fade In**
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
```

**Slide Up**
```css
@keyframes slideUp {
  from { 
    opacity: 0;
    transform: translateY(100px) scale(0.9);
  }
  to { 
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
```

**Bounce** (Emojis saisonniers)
```css
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}
```

**Pulse** (Bannières promos)
```css
animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
```

---

## 💎 Principes de Design

### 1. **Clarté**
- Interface épurée, sans encombrement
- Hiérarchie visuelle claire
- Espaces blancs généreux

### 2. **Accessibilité**
- Contraste minimum WCAG AA (4.5:1)
- Labels descriptifs sur tous les éléments interactifs
- Navigation au clavier supportée

### 3. **Cohérence**
- Utilisation systématique des composants définis
- Palette de couleurs respectée
- Espacements uniformes

### 4. **Performance**
- Images optimisées
- Lazy loading pour les contenus lourds
- Animations GPU-accelerated

### 5. **Feedback Utilisateur**
- Toast notifications pour les actions
- Loading states visibles
- Messages d'erreur clairs et utiles

---

## 📄 Footer

### Contenu
- Logo MyKalama English
- Navigation secondaire
- Réseaux sociaux (Instagram, Facebook, Snapchat, TikTok)
- Copyright © 2025 MyKalama English

### Style
```
Background : Teal 900
Couleur texte : White/Gray 300
Padding : py-12
```

---

## 🔗 Liens Utiles

**Site Web :** https://e-learn-dash.preview.emergentagent.com  
**Email Contact :** info@mykalamaenglish.com  
**Réseaux Sociaux :**
- Instagram : [@mykalamaenglish]
- Facebook : [MyKalama English]
- TikTok : [@mykalamaenglish]
- Snapchat : [@mykalamaenglish]

---

## 📝 Notes de Mise à Jour

**Version 1.0** - Décembre 2025
- Charte graphique initiale
- Définition des couleurs et typographie
- Documentation des composants UI

**Dernière mise à jour :** Décembre 2025  
**Créé par :** MyKalama English Team
