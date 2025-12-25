/**
 * Utility function to construct proper file URLs for uploads
 * Handles the /api/uploads/ routing required for Kubernetes ingress
 */

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export const getFileUrl = (fileUrl) => {
  if (!fileUrl) return '';
  if (fileUrl.startsWith('http')) return fileUrl;
  
  // Les fichiers sont servis via /api/uploads/ pour passer par l'ingress Kubernetes
  // Remplacer /uploads/ par /api/uploads/ si nécessaire
  if (fileUrl.startsWith('/uploads/')) {
    return `${BACKEND_URL}${fileUrl.replace('/uploads/', '/api/uploads/')}`;
  }
  
  // Si l'URL commence par / mais pas par /uploads/, ajouter /api
  if (fileUrl.startsWith('/')) {
    return `${BACKEND_URL}/api${fileUrl}`;
  }
  
  return `${BACKEND_URL}/api/uploads/${fileUrl}`;
};

export default getFileUrl;
