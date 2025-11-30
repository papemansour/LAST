# 🎨 CHARTE GRAPHIQUE - MY KALAMA ENGLISH

## 📋 Table des Matières
1. [Identité Visuelle](#identité-visuelle)
2. [Palette de Couleurs](#palette-de-couleurs)
3. [Typographie](#typographie)
4. [Logo & Branding](#logo--branding)
5. [Composants UI](#composants-ui)
6. [Iconographie](#iconographie)
7. [Animations & Effets](#animations--effets)
8. [Responsive Design](#responsive-design)
9. [États Interactifs](#états-interactifs)
10. [Illustrations & Images](#illustrations--images)

---

## 🎯 Identité Visuelle

### Mission
Plateforme d'apprentissage de l'anglais en ligne, moderne et engageante, adaptée à tous les niveaux.

### Valeurs
- **Accessibilité** : Formation accessible à tous
- **Excellence** : Qualité pédagogique premium
- **Flexibilité** : Apprentissage à son rythme
- **Communauté** : Esprit d'entraide et partage
- **Innovation** : Technologies modernes et gamification

### Ton de Communication
- Convivial et encourageant
- Professionnel mais accessible
- Motivant et positif
- Pédagogique et clair

---

## 🎨 Palette de Couleurs

### Couleurs Principales

#### Teal/Vert (Couleur Primaire)
```css
/* Principal */
--primary-50:  #f0fdfa    /* Backgrounds très légers */
--primary-100: #ccfbf1    /* Backgrounds légers */
--primary-200: #99f6e4    /* Borders légers */
--primary-300: #5eead4    /* Accents */
--primary-400: #2dd4bf    /* Hover states */
--primary-500: #14b8a6    /* Boutons principaux */
--primary-600: #0d9488    /* Boutons hover */
--primary-700: #0f766e    /* Textes importants */
--primary-800: #115e59    /* Textes très foncés */
--primary-900: #134e4a    /* Textes max contrast */
```

**Usage :**
- Navigation et headers
- Boutons d'action principaux
- Liens et éléments interactifs
- Accents et highlights
- Progression et succès

#### Vert (Couleur Secondaire - Gamification)
```css
/* Vert Émeraude */
--green-50:  #f0fdf4
--green-100: #dcfce7
--green-200: #bbf7d0
--green-300: #86efac
--green-400: #4ade80
--green-500: #22c55e    /* Success, Badges */
--green-600: #16a34a    /* Dashboards actifs */
--green-700: #15803d
--green-800: #166534
--green-900: #14532d
```

**Usage :**
- États de succès
- Badges et récompenses
- Progression complétée
- Validation de formulaires
- Dashboards (onglets actifs)

### Couleurs Complémentaires

#### Bleu (Confiance & Sérénité)
```css
--blue-50:  #eff6ff
--blue-100: #dbeafe
--blue-200: #bfdbfe
--blue-300: #93c5fd
--blue-400: #60a5fa
--blue-500: #3b82f6
--blue-600: #2563eb    /* Informations */
--blue-700: #1d4ed8
--blue-800: #1e40af
--blue-900: #1e3a8a
```

**Usage :**
- Informations et tips
- Liens secondaires
- Éléments informationnels
- Cartes de réduction (Euros)

#### Violet/Purple (Innovation & Créativité)
```css
--purple-50:  #faf5ff
--purple-100: #f3e8ff
--purple-200: #e9d5ff
--purple-300: #d8b4fe
--purple-400: #c084fc
--purple-500: #a855f7    /* Défis & Gamification */
--purple-600: #9333ea
--purple-700: #7e22ce
--purple-800: #6b21a8
--purple-900: #581c87
```

**Usage :**
- Système de défis
- Points XP et gamification
- Badges et récompenses
- Éléments premium

#### Jaune/Orange (Énergie & Récompenses)
```css
/* Jaune */
--yellow-400: #facc15
--yellow-500: #eab308    /* Coffre aux trésors plein */
--yellow-600: #ca8a04

/* Orange */
--orange-400: #fb923c
--orange-500: #f97316    /* Accents énergétiques */
--orange-600: #ea580c
```

**Usage :**
- Récompenses débloquées
- Coffre aux trésors plein
- Call-to-actions importants
- Événements spéciaux

#### Rose/Pink (Convivialité)
```css
--pink-50:  #fdf2f8
--pink-100: #fce7f3
--pink-200: #fbcfe8
--pink-300: #f9a8d4
--pink-400: #f472b6
--pink-500: #ec4899
--pink-600: #db2777
```

**Usage :**
- Accents féminins
- Dégradés avec violet
- Éléments décoratifs

#### Rouge (Urgent & Nouveau)
```css
--red-50:  #fef2f2
--red-100: #fee2e2
--red-200: #fecaca
--red-300: #fca5a5
--red-400: #f87171
--red-500: #ef4444     /* Erreurs */
--red-600: #dc2626     /* Badges "NOUVEAU" */
--red-700: #b91c1c     /* Cadeau */
```

**Usage :**
- Erreurs et alertes
- Badges "NOUVEAU"
- Notifications importantes
- Suppression d'éléments
- Cadeau de bienvenue

### Couleurs Neutres

#### Gris (Interface)
```css
--gray-50:  #f9fafb    /* Backgrounds */
--gray-100: #f3f4f6    /* Backgrounds légers */
--gray-200: #e5e7eb    /* Borders */
--gray-300: #d1d5db    /* Borders foncés */
--gray-400: #9ca3af    /* Textes secondaires */
--gray-500: #6b7280    /* Textes */
--gray-600: #4b5563    /* Textes importants */
--gray-700: #374151    /* Textes foncés */
--gray-800: #1f2937    /* Textes très foncés */
--gray-900: #111827    /* Footer, headers */
```

**Usage :**
- Textes principaux (700-900)
- Textes secondaires (400-600)
- Backgrounds (50-100)
- Borders (200-300)
- Footer et navigation (900)

#### Blanc & Noir
```css
--white: #ffffff
--black: #000000
--white-opacity-40: rgba(255, 255, 255, 0.4)   /* Effet glace */
--white-opacity-60: rgba(255, 255, 255, 0.6)   /* Hover glace */
--black-opacity-60: rgba(0, 0, 0, 0.6)         /* Modals backdrop */
```

---

## ✍️ Typographie

### Police Principale
**System Fonts Stack** (Performance optimale)
```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", 
             Roboto, "Helvetica Neue", Arial, sans-serif;
```

### Hiérarchie des Tailles

#### Desktop
```css
/* Headings */
--text-6xl: 3.75rem   /* 60px - Hero titles */
--text-5xl: 3rem      /* 48px - Page titles */
--text-4xl: 2.25rem   /* 36px - Section titles */
--text-3xl: 1.875rem  /* 30px - Subsection titles */
--text-2xl: 1.5rem    /* 24px - Card titles */
--text-xl:  1.25rem   /* 20px - Large text */

/* Body */
--text-lg:   1.125rem /* 18px - Large body */
--text-base: 1rem     /* 16px - Normal body */
--text-sm:   0.875rem /* 14px - Small text */
--text-xs:   0.75rem  /* 12px - Captions */
```

#### Mobile
```css
/* H1 (Hero) */
--text-4xl-mobile: 2.25rem  /* 36px */

/* H2 (Sections) */
--text-base-mobile: 1rem     /* 16px */
--text-lg-mobile:   1.125rem /* 18px */

/* Body */
--text-sm-mobile: 0.875rem   /* 14px */
```

### Graisses (Font Weights)
```css
--font-light:      300  /* Textes légers, citations */
--font-normal:     400  /* Texte normal */
--font-medium:     500  /* Emphasis léger */
--font-semibold:   600  /* Sous-titres */
--font-bold:       700  /* Titres */
--font-extrabold:  800  /* Titres importants */
--font-black:      900  /* Display text */
```

### Hauteurs de Ligne
```css
--leading-tight:  1.25   /* Titres */
--leading-snug:   1.375  /* Sous-titres */
--leading-normal: 1.5    /* Body text */
--leading-relaxed: 1.625 /* Textes longs */
--leading-loose:  2      /* Espacé */
```

### Espacements de Lettres
```css
--tracking-tighter: -0.05em  /* Titles serrés */
--tracking-tight:   -0.025em /* Titles */
--tracking-normal:  0        /* Normal */
--tracking-wide:    0.025em  /* Emphasis */
--tracking-wider:   0.05em   /* All caps */
--tracking-widest:  0.1em    /* Labels */
```

---

## 🏷️ Logo & Branding

### Logo Principal
```
MY KALAMA
English
```

**Typographie :**
- "MY KALAMA" : Bold (700), Teal-600 (#0d9488)
- "English" : SemiBold (600), Gray-600 (#4b5563)
- "English" en uppercase avec tracking-wide

**Tailles :**
- Desktop : 2xl (24px) / sm (14px)
- Mobile : lg (18px) / xs (12px)

### Variations
- **Navigation** : Full logo avec "English"
- **Footer** : Full logo + tagline
- **Favicon** : Initiales "MK"

### Zone de Protection
Espace minimum autour du logo : Hauteur du logo × 0.5

---

## 🧩 Composants UI

### Boutons

#### Primaire (Call-to-Action)
```css
/* Normal */
background: linear-gradient(to right, #14b8a6, #0d9488);
color: white;
padding: 0.75rem 2rem;
border-radius: 0.5rem;
font-weight: 600;

/* Hover */
background: linear-gradient(to right, #0d9488, #0f766e);
transform: translateY(-2px);
box-shadow: 0 10px 25px -5px rgba(20, 184, 166, 0.4);
```

#### Secondaire
```css
background: white;
border: 2px solid #14b8a6;
color: #0d9488;
```

#### Ghost
```css
background: transparent;
color: #0d9488;
hover:background: rgba(20, 184, 166, 0.1);
```

#### Tailles
- **xs** : px-2 py-1 text-xs
- **sm** : px-3 py-1.5 text-sm
- **md** : px-4 py-2 text-base (default)
- **lg** : px-6 py-3 text-lg
- **xl** : px-8 py-4 text-xl

### Cartes (Cards)

#### Standard
```css
background: white;
border-radius: 0.75rem;  /* 12px */
border: 1px solid #e5e7eb;
box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
padding: 1.5rem;

/* Hover */
box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
transform: translateY(-2px);
```

#### Avec Header
```css
/* Header */
background: #f0fdfa;  /* Teal-50 */
padding: 1rem 1.5rem;
border-bottom: 1px solid #99f6e4;

/* Content */
padding: 1.5rem;
```

### Onglets (Tabs)

#### Effet Glace (Glassmorphism)
```css
/* Inactif */
background: rgba(255, 255, 255, 0.4);
backdrop-filter: blur(12px);
border: 2px solid rgba(255, 255, 255, 0.3);

/* Hover */
background: rgba(255, 255, 255, 0.6);

/* Actif */
background: #16a34a;  /* Green-600 */
color: white;
box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
transform: scale(1.05);
```

### Inputs (Formulaires)

#### Text Input
```css
border: 1px solid #d1d5db;
border-radius: 0.5rem;
padding: 0.75rem 1rem;
font-size: 1rem;

/* Focus */
border-color: #14b8a6;
box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.1);
outline: none;

/* Error */
border-color: #ef4444;
```

#### Select (Dropdown)
```css
/* Même style que text input */
/* Avec icône chevron à droite */
background-image: url("data:image/svg...");
```

### Badges

#### Nouveau / Important
```css
background: #dc2626;  /* Red-600 */
color: white;
padding: 0.25rem 0.5rem;
border-radius: 9999px;  /* Fully rounded */
font-size: 0.75rem;
font-weight: 700;
```

#### Success / Complété
```css
background: #22c55e;  /* Green-500 */
color: white;
```

#### Info
```css
background: #3b82f6;  /* Blue-500 */
color: white;
```

### Modals

#### Backdrop
```css
background: rgba(0, 0, 0, 0.6);
backdrop-filter: blur(4px);
```

#### Content
```css
background: white;
border-radius: 1rem;
max-width: 42rem;  /* 672px */
max-height: 90vh;
box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
```

---

## 🎭 Iconographie

### Style d'Icônes
**Lucide React** (Outline style, consistent stroke width)

### Tailles
```css
--icon-xs: 16px   /* w-4 h-4 */
--icon-sm: 20px   /* w-5 h-5 */
--icon-md: 24px   /* w-6 h-6 */
--icon-lg: 32px   /* w-8 h-8 */
--icon-xl: 48px   /* w-12 h-12 */
```

### Emojis (Décoration)
Utilisés pour ajouter de la personnalité :
- 🎯 Objectifs
- 🎁 Cadeaux / Récompenses
- 🏆 Badges / Succès
- 💰 Points / Argent
- 📚 Apprentissage
- ✨ Magie / Nouveau
- 🎉 Célébration
- 👥 Communauté
- 📄 Documents
- 🎓 Éducation

### Icônes Réseaux Sociaux
- Snapchat : Fond jaune (#facc15)
- Instagram : Fond teal (#14b8a6)
- Facebook : Fond teal (#14b8a6)
- LinkedIn : Fond teal (#14b8a6)

---

## ✨ Animations & Effets

### Transitions Standard
```css
transition-duration: 300ms;
transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
```

### Effets Hover
```css
/* Boutons */
transform: translateY(-2px);
box-shadow: /* Ombre amplifiée */

/* Cartes */
transform: translateY(-4px);
box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
```

### Animations Spéciales

#### Pulse (Boutons importants)
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
```

#### Bounce (Récompenses)
```css
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}
```

#### Slide Up (Modals)
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

#### Fall (Confettis)
```css
@keyframes fall {
  to {
    transform: translateY(100vh) rotate(360deg);
    opacity: 0;
  }
}
```

### Effets Visuels

#### Glassmorphism (Effet Glace)
```css
background: rgba(255, 255, 255, 0.4);
backdrop-filter: blur(12px);
border: 1px solid rgba(255, 255, 255, 0.3);
```

#### Dégradés
```css
/* Primaire */
background: linear-gradient(to right, #14b8a6, #0d9488);

/* Succès */
background: linear-gradient(to right, #22c55e, #16a34a);

/* Énergie */
background: linear-gradient(to right, #facc15, #f97316);

/* Récompense */
background: linear-gradient(to right, #a855f7, #ec4899);

/* Hero Background */
background: linear-gradient(to bottom right, 
  #f0fdfa, #ffffff, #eff6ff);
```

---

## 📱 Responsive Design

### Breakpoints
```css
/* Mobile First */
--screen-sm:  640px   /* Small devices */
--screen-md:  768px   /* Tablets */
--screen-lg:  1024px  /* Desktops */
--screen-xl:  1280px  /* Large desktops */
--screen-2xl: 1536px  /* Extra large */
```

### Grille
```css
/* Mobile : 1 colonne */
grid-template-columns: 1fr;

/* Tablet : 2 colonnes */
@media (min-width: 768px) {
  grid-template-columns: repeat(2, 1fr);
}

/* Desktop : 3-4 colonnes */
@media (min-width: 1024px) {
  grid-template-columns: repeat(3, 1fr);
}
```

### Espacements

#### Padding Container
```css
/* Mobile */
padding: 1rem;  /* 16px */

/* Tablet */
padding: 1.5rem;  /* 24px */

/* Desktop */
padding: 2rem;  /* 32px */
```

#### Gaps
```css
/* Entre éléments */
--gap-1: 0.25rem  /* 4px */
--gap-2: 0.5rem   /* 8px */
--gap-3: 0.75rem  /* 12px */
--gap-4: 1rem     /* 16px */
--gap-6: 1.5rem   /* 24px */
--gap-8: 2rem     /* 32px */
```

---

## 🎮 États Interactifs

### Boutons
```css
/* Default */
opacity: 1;
cursor: pointer;

/* Hover */
transform: translateY(-2px);
filter: brightness(1.1);

/* Active (Click) */
transform: scale(0.98);

/* Disabled */
opacity: 0.5;
cursor: not-allowed;
pointer-events: none;

/* Loading */
opacity: 0.7;
cursor: wait;
/* + Spinner */
```

### Liens
```css
/* Default */
color: #0d9488;
text-decoration: none;

/* Hover */
color: #0f766e;
text-decoration: underline;

/* Visited */
color: #115e59;
```

### Formulaires
```css
/* Focus */
outline: none;
border-color: #14b8a6;
box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.1);

/* Valid */
border-color: #22c55e;

/* Invalid */
border-color: #ef4444;

/* Disabled */
background: #f3f4f6;
cursor: not-allowed;
```

---

## 🖼️ Illustrations & Images

### Style Général
- Illustrations flat design
- Couleurs cohérentes avec la palette
- Émojis pour la personnalité
- Photos haute qualité (si utilisées)

### Cadeau de Bienvenue
```css
/* Cadeau rouge avec ruban jaune */
Couleurs:
  - Corps: linear-gradient(to bottom right, #dc2626, #b91c1c)
  - Ruban: linear-gradient(to right, #facc15, #eab308)
  - Noeud: Jaune doré avec ombres
```

### Coffre aux Trésors
```css
/* Vide (< 50 points) */
Icon: 🎁
Background: linear-gradient(purple-600, pink-500)

/* Plein (≥ 50 points) */
Icon: 💎
Background: linear-gradient(yellow-400, orange-500)
Animation: pulse + bounce
```

### Badges
```css
🚀 Débutant - Premier login
📚 Assidu - 5 cours
⭐ Expert - 10 cours
🏆 Champion - Niveau complété
```

### Ratios d'Images
- **Hero** : 16:9
- **Cards** : 4:3
- **Avatar** : 1:1 (circle)
- **Thumbnails** : 16:9 ou 4:3

---

## 📐 Espacements & Grille

### Système d'Espacement (Base 4px)
```css
--space-0:  0
--space-1:  0.25rem   /* 4px */
--space-2:  0.5rem    /* 8px */
--space-3:  0.75rem   /* 12px */
--space-4:  1rem      /* 16px */
--space-6:  1.5rem    /* 24px */
--space-8:  2rem      /* 32px */
--space-12: 3rem      /* 48px */
--space-16: 4rem      /* 64px */
--space-24: 6rem      /* 96px */
```

### Marges Sections
```css
/* Mobile */
margin-bottom: 3rem;  /* 48px */

/* Desktop */
margin-bottom: 6rem;  /* 96px */
```

### Rayons de Bordure
```css
--rounded-sm:   0.125rem  /* 2px */
--rounded:      0.25rem   /* 4px */
--rounded-md:   0.375rem  /* 6px */
--rounded-lg:   0.5rem    /* 8px */
--rounded-xl:   0.75rem   /* 12px */
--rounded-2xl:  1rem      /* 16px */
--rounded-3xl:  1.5rem    /* 24px */
--rounded-full: 9999px    /* Cercle parfait */
```

### Ombres (Shadows)
```css
/* Petite */
box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);

/* Moyenne */
box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);

/* Grande */
box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);

/* Extra Large */
box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);

/* 2XL (Modals) */
box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);

/* Couleurs */
/* Teal */
box-shadow: 0 10px 25px -5px rgba(20, 184, 166, 0.4);

/* Green */
box-shadow: 0 10px 25px -5px rgba(34, 197, 94, 0.4);
```

---

## ✅ Checklist d'Application

### Chaque Nouvelle Page Doit :
- [ ] Utiliser les couleurs de la palette
- [ ] Respecter la hiérarchie typographique
- [ ] Être responsive (mobile-first)
- [ ] Avoir des transitions fluides (300ms)
- [ ] Utiliser le système d'espacement (4px base)
- [ ] Inclure les états hover/focus/active
- [ ] Optimiser les images (WebP si possible)
- [ ] Tester l'accessibilité (contraste, focus)

### Chaque Composant Doit :
- [ ] Avoir un padding/margin cohérent
- [ ] Utiliser border-radius standardisé
- [ ] Avoir des ombres appropriées
- [ ] Supporter les états interactifs
- [ ] Être accessible au clavier
- [ ] Avoir un loading state si async
- [ ] Afficher les erreurs clairement

---

## 🎨 Exemples d'Application

### Dashboard Étudiant
- **Couleur dominante** : Green (vert)
- **Onglets actifs** : Green-600 solid
- **Onglets inactifs** : White/40 glassmorphism
- **Cartes** : White avec border teal-100
- **Boutons** : Teal-600 hover:teal-700

### Coffre aux Trésors
- **État vide** : Purple → Pink gradient
- **État plein** : Yellow → Orange gradient
- **Icône** : 🎁 (vide) → 💎 (plein)
- **Animation** : Pulse quand plein

### Cadeau Bienvenue
- **Fond** : Black/60 backdrop-blur
- **Cadeau** : Red-600 → Red-700
- **Ruban** : Yellow-400 → Yellow-500
- **Confettis** : ✨🎉🎊⭐💫 animés
- **Bouton** : Yellow-400 → Orange-500 pulse

### Formulaires
- **Label** : Gray-700 font-medium
- **Input** : Border gray-300
- **Focus** : Border teal-500 + ring teal-100
- **Error** : Border red-500 + text red-600
- **Success** : Border green-500 + icon

---

## 📝 Notes Importantes

### Performance
- Utiliser CSS pour les animations (pas JS)
- Lazy loading pour les images
- Optimiser les dégradés (max 2 couleurs)
- Limiter backdrop-blur (coûteux)

### Accessibilité
- Contraste minimum 4.5:1 (texte normal)
- Contraste minimum 3:1 (texte large)
- Focus visible sur tous les éléments interactifs
- Alt text sur toutes les images
- Labels sur tous les inputs

### Cohérence
- Toujours utiliser les variables CSS
- Ne pas inventer de nouvelles couleurs
- Respecter les espacements standardisés
- Maintenir la hiérarchie typographique

---

## 📞 Contacts Design

**Questions sur la charte :**
- Consulter ce document
- Vérifier les composants existants
- Tester sur mobile ET desktop

**Dernière mise à jour :** 30 Novembre 2024
**Version :** 1.0

---

*Ce document est vivant et doit être mis à jour lors de l'ajout de nouveaux composants ou couleurs.*
