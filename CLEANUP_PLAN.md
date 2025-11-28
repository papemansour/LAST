# Plan de nettoyage des Documents

## Fichiers à modifier:

### 1. StudentDashboard.js
- Supprimer l'onglet Documents (ligne ~312-317)
- Supprimer TabsContent documents (ligne ~553-645)
- Supprimer states: documents, previewDocument
- Supprimer l'appel API /student/my-documents
- Supprimer Dialog de prévisualisation

### 2. TeacherDashboard.js
- Supprimer l'onglet Documents
- Supprimer toute la gestion d'upload et liste de documents
- Garder uniquement Messages

### 3. AdminDashboard.js
- Supprimer l'onglet Documents
- Supprimer "Documents Reçus"
- Garder uniquement Messages

## Backend endpoints à vérifier:
- /api/student/my-documents
- /api/teacher/my-documents
- /api/documents/{id}
- /api/upload

Ces endpoints peuvent rester pour compatibilité messages avec pièces jointes.
