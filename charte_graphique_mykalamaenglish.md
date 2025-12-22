# 🎓 Charte Graphique - MyKalama English

## 📌 Identité Visuelle

### Logo
- **Logo principal** : 🎓 MyKalama English
- **Favicon** : Emoji graduation cap 🎓
- **Slogan** : "Votre aventure linguistique commence ici"

---

## 🎨 Palette de Couleurs

### Couleurs Principales
| Nom | Hex | RGB | Utilisation |
|-----|-----|-----|-------------|
| **Teal Primary** | `#0d9488` | rgb(13, 148, 136) | Boutons principaux, liens, accents |
| **Teal Light** | `#14b8a6` | rgb(20, 184, 166) | Dégradés, hover states |
| **Teal Dark** | `#0f766e` | rgb(15, 118, 110) | Textes importants, headers |

### Couleurs Secondaires
| Nom | Hex | RGB | Utilisation |
|-----|-----|-----|-------------|
| **Purple** | `#7c3aed` | rgb(124, 58, 237) | Secrétariat, administration |
| **Blue** | `#3b82f6` | rgb(59, 130, 246) | Étudiants, informations |
| **Green** | `#059669` | rgb(5, 150, 105) | Succès, validations, paiements |
| **Orange** | `#f59e0b` | rgb(245, 158, 11) | Alertes, promotions |
| **Pink** | `#ec4899` | rgb(236, 72, 153) | K-Kids, enfants |

### Couleurs Neutres
| Nom | Hex | Utilisation |
|-----|-----|-------------|
| **Gray 50** | `#f9fafb` | Backgrounds légers |
| **Gray 100** | `#f3f4f6` | Cards backgrounds |
| **Gray 600** | `#4b5563` | Texte secondaire |
| **Gray 900** | `#1f2937` | Texte principal |

---

## 📝 Typographie

### Police Principale
- **Font Family** : `'Segoe UI', Arial, sans-serif`
- **Alternative** : Inter, system-ui

### Hiérarchie des Titres
| Élément | Taille | Poids | Couleur |
|---------|--------|-------|---------|
| H1 | 2.5rem (40px) | Bold (700) | Gray 900 |
| H2 | 2rem (32px) | Semibold (600) | Gray 900 |
| H3 | 1.5rem (24px) | Semibold (600) | Gray 800 |
| H4 | 1.25rem (20px) | Medium (500) | Gray 700 |
| Body | 1rem (16px) | Normal (400) | Gray 600 |
| Small | 0.875rem (14px) | Normal (400) | Gray 500 |

---

## 🔘 Composants UI

### Boutons
```css
/* Bouton Principal */
.btn-primary {
  background: linear-gradient(135deg, #0d9488 0%, #14b8a6 100%);
  color: white;
  border-radius: 0.75rem (12px);
  padding: 12px 24px;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(13, 148, 136, 0.4);
}

/* Bouton Secondaire */
.btn-secondary {
  background: white;
  border: 2px solid #0d9488;
  color: #0d9488;
  border-radius: 0.75rem;
}

/* Bouton Succès */
.btn-success {
  background: #059669;
  color: white;
}

/* Bouton Danger */
.btn-danger {
  background: #dc2626;
  color: white;
}
```

### Cards
```css
.card {
  background: white;
  border-radius: 1rem (16px);
  border: 1px solid #e5e7eb;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.card-header {
  background: linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 100%);
  border-bottom: 1px solid #99f6e4;
}
```

### Inputs
```css
.input {
  border: 1px solid #d1d5db;
  border-radius: 0.5rem (8px);
  padding: 10px 14px;
  font-size: 14px;
}

.input:focus {
  border-color: #0d9488;
  box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.1);
}
```

---

## 📐 Espacements

### Grille
- **Container max-width** : 1280px
- **Gutter** : 24px (gap-6)
- **Padding sections** : 64px vertical, 24px horizontal

### Marges Standards
| Nom | Valeur | Utilisation |
|-----|--------|-------------|
| xs | 4px | Entre icône et texte |
| sm | 8px | Entre éléments proches |
| md | 16px | Entre sections de carte |
| lg | 24px | Entre cartes |
| xl | 48px | Entre sections majeures |

---

## 🎭 Iconographie

### Emojis Officiels
| Contexte | Emoji |
|----------|-------|
| Logo/Brand | 🎓 |
| Étudiants | 👤 👥 |
| Professeurs | 👨‍🏫 👩‍🏫 |
| Admin | 👨‍💼 |
| Secrétaire | 📋 |
| K-Kids | 🦄 ⭐ 🎮 |
| Succès | ✅ ✓ |
| Documents | 📄 📁 |
| Messages | 💬 📧 |
| Paiements | 💰 💸 🧾 |
| Téléphone | 📞 |
| Email | 📧 |
| Calendrier | 📅 |

### Icônes Lucide (lucide-react)
- Navigation : `Home, Users, Settings, LogOut`
- Actions : `Plus, Trash2, Edit, Eye, Download`
- Communication : `MessageCircle, Send, Bell`
- Documents : `FileText, Upload, FolderOpen`

---

## 📱 Responsive Design

### Breakpoints
| Taille | Min-width | Usage |
|--------|-----------|-------|
| Mobile | 0px | Design mobile-first |
| SM | 640px | Petits appareils |
| MD | 768px | Tablettes |
| LG | 1024px | Laptops |
| XL | 1280px | Desktops |

### Règles
1. **Mobile-first** : Toujours commencer par le design mobile
2. **Touch targets** : Minimum 44x44px pour les boutons
3. **Font-size** : Minimum 14px pour la lisibilité
4. **Spacing** : Réduire de 25% sur mobile

---

## 🏢 Informations Société

### Coordonnées
- **Société** : MyKalama English
- **Localisations** : Paris, France / Dakar, Sénégal
- **Téléphone** : +221 78 260 75 49 / 78 528 68 89
- **Email** : mykalamaenglish@gmail.com
- **Site web** : https://mykalamaenglish.com

### Mentions Légales
- TVA : 0% (non applicable)
- Année de création : 2024

---

## ✨ Animations

### Transitions Standards
```css
.transition-default {
  transition: all 0.3s ease;
}

.hover-scale {
  transform: scale(1.02);
}

.hover-shadow {
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
}
```

### Animations Spéciales
- **Pulse** : Pour les promotions et alertes importantes
- **Fade-in** : Pour les modales et dialogues
- **Slide-up** : Pour les toasts et notifications

---

## 📋 Templates Factures

### Facture Professeur
- Numéro : FAC-PROF-XXXXXXXX
- Couleur : Vert (#059669)
- TVA : 0%

### Facture Étudiant
- Numéro : FAC-ETU-XXXXXXXX
- Couleur : Bleu (#3b82f6)
- TVA : 0%

### Facture Prestataire
- Numéro : FAC-PRE-XXXXXXXX
- Couleur : Violet (#7c3aed)
- TVA : 0%

---

© 2025 MyKalama English - Tous droits réservés
