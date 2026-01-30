import React, { useState } from 'react';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from '../components/ui/dialog';
import { toast } from 'sonner';
import { Upload, Download, FileSpreadsheet, CheckCircle, XCircle, AlertCircle, Copy } from 'lucide-react';
import apiClient from '../utils/api';

const ImportStudentsCSV = ({ onImportComplete }) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const downloadTemplate = async () => {
    try {
      const response = await apiClient.get('/admin/csv-template', {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'modele_import_etudiants.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success('Modèle CSV téléchargé!');
    } catch (error) {
      toast.error('Erreur lors du téléchargement du modèle');
    }
  };

  const handleFile = async (file) => {
    if (!file) return;
    
    if (!file.name.endsWith('.csv')) {
      toast.error('Veuillez sélectionner un fichier CSV');
      return;
    }

    setLoading(true);
    setResults(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await apiClient.post('/admin/import-students-csv', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setResults(response.data);
      
      if (response.data.summary.total_imported > 0) {
        toast.success(`${response.data.summary.total_imported} étudiant(s) importé(s)!`);
        if (onImportComplete) {
          onImportComplete();
        }
      } else if (response.data.summary.total_skipped > 0) {
        toast.warning('Aucun nouvel étudiant importé (emails déjà existants)');
      } else {
        toast.error('Aucun étudiant importé - vérifiez le format du fichier');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de l\'import');
    } finally {
      setLoading(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const copyCredentials = (student) => {
    const text = `Email: ${student.email}\nMot de passe: ${student.password}\nCode Digika: ${student.digika_code}`;
    navigator.clipboard.writeText(text);
    toast.success('Credentials copiés!');
  };

  const copyAllCredentials = () => {
    if (!results?.details?.imported?.length) return;
    
    const text = results.details.imported.map(s => 
      `${s.name}\nEmail: ${s.email}\nMot de passe: ${s.password}\nCode: ${s.digika_code}\n`
    ).join('\n---\n');
    
    navigator.clipboard.writeText(text);
    toast.success('Tous les credentials copiés!');
  };

  const resetDialog = () => {
    setResults(null);
    setLoading(false);
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => {
      setOpen(isOpen);
      if (!isOpen) resetDialog();
    }}>
      <DialogTrigger asChild>
        <Button variant="outline" className="border-teal-200 text-teal-700 hover:bg-teal-50">
          <Upload className="w-4 h-4 mr-2" />
          Import CSV
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-teal-600" />
            Importer des Étudiants (CSV)
          </DialogTitle>
          <DialogDescription>
            Importez plusieurs étudiants à la fois depuis un fichier CSV
          </DialogDescription>
        </DialogHeader>

        {!results ? (
          <div className="space-y-4 mt-4">
            {/* Instructions */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-800 mb-2">Format du fichier CSV</h4>
              <p className="text-sm text-blue-700 mb-2">
                Le fichier doit contenir les colonnes suivantes (séparées par <code className="bg-blue-100 px-1 rounded">;</code>) :
              </p>
              <ul className="text-sm text-blue-700 list-disc list-inside space-y-1">
                <li><strong>prenom</strong> (obligatoire)</li>
                <li><strong>nom</strong></li>
                <li><strong>email</strong> (obligatoire)</li>
                <li><strong>telephone</strong></li>
                <li><strong>niveau</strong> (beginner, intermediate, advanced, kkid)</li>
                <li><strong>prix</strong></li>
                <li><strong>devise</strong> (EUR ou FCFA)</li>
              </ul>
              
              <Button 
                variant="outline" 
                size="sm" 
                onClick={downloadTemplate}
                className="mt-3"
              >
                <Download className="w-4 h-4 mr-2" />
                Télécharger le modèle CSV
              </Button>
            </div>

            {/* Zone de drop */}
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`
                border-2 border-dashed rounded-lg p-8 text-center transition-colors
                ${dragActive 
                  ? 'border-teal-500 bg-teal-50' 
                  : 'border-gray-300 hover:border-teal-400 hover:bg-gray-50'
                }
                ${loading ? 'opacity-50 pointer-events-none' : ''}
              `}
            >
              {loading ? (
                <div className="flex flex-col items-center">
                  <div className="w-10 h-10 border-4 border-teal-500 border-t-transparent rounded-full animate-spin mb-3" />
                  <p className="text-gray-600">Import en cours...</p>
                </div>
              ) : (
                <>
                  <Upload className="w-12 h-12 mx-auto text-gray-400 mb-3" />
                  <p className="text-gray-600 mb-2">
                    Glissez-déposez votre fichier CSV ici
                  </p>
                  <p className="text-gray-400 text-sm mb-4">ou</p>
                  <label className="cursor-pointer">
                    <span className="px-4 py-2 bg-teal-600 text-white rounded-md hover:bg-teal-700 transition-colors">
                      Parcourir les fichiers
                    </span>
                    <input
                      type="file"
                      accept=".csv"
                      onChange={handleFileInput}
                      className="hidden"
                    />
                  </label>
                </>
              )}
            </div>
          </div>
        ) : (
          /* Résultats de l'import */
          <div className="space-y-4 mt-4">
            {/* Résumé */}
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
                <CheckCircle className="w-6 h-6 mx-auto text-green-600 mb-1" />
                <p className="text-2xl font-bold text-green-700">{results.summary.total_imported}</p>
                <p className="text-xs text-green-600">Importés</p>
              </div>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-center">
                <AlertCircle className="w-6 h-6 mx-auto text-yellow-600 mb-1" />
                <p className="text-2xl font-bold text-yellow-700">{results.summary.total_skipped}</p>
                <p className="text-xs text-yellow-600">Ignorés</p>
              </div>
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-center">
                <XCircle className="w-6 h-6 mx-auto text-red-600 mb-1" />
                <p className="text-2xl font-bold text-red-700">{results.summary.total_errors}</p>
                <p className="text-xs text-red-600">Erreurs</p>
              </div>
            </div>

            {/* Liste des étudiants importés */}
            {results.details.imported.length > 0 && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex justify-between items-center mb-3">
                  <h4 className="font-medium text-green-800">
                    Étudiants importés ({results.details.imported.length})
                  </h4>
                  <Button size="sm" variant="outline" onClick={copyAllCredentials}>
                    <Copy className="w-3 h-3 mr-1" />
                    Copier tout
                  </Button>
                </div>
                <div className="max-h-48 overflow-y-auto space-y-2">
                  {results.details.imported.map((student, idx) => (
                    <div key={idx} className="bg-white rounded p-2 flex justify-between items-center text-sm">
                      <div>
                        <span className="font-medium">{student.name}</span>
                        <span className="text-gray-500 ml-2">{student.email}</span>
                      </div>
                      <button 
                        onClick={() => copyCredentials(student)}
                        className="text-teal-600 hover:text-teal-800"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Liste des ignorés */}
            {results.details.skipped.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h4 className="font-medium text-yellow-800 mb-2">
                  Ignorés - Emails déjà existants ({results.details.skipped.length})
                </h4>
                <div className="max-h-32 overflow-y-auto space-y-1">
                  {results.details.skipped.map((item, idx) => (
                    <div key={idx} className="text-sm text-yellow-700">
                      Ligne {item.row}: {item.email}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Liste des erreurs */}
            {results.details.errors.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <h4 className="font-medium text-red-800 mb-2">
                  Erreurs ({results.details.errors.length})
                </h4>
                <div className="max-h-32 overflow-y-auto space-y-1">
                  {results.details.errors.map((item, idx) => (
                    <div key={idx} className="text-sm text-red-700">
                      Ligne {item.row}: {item.reason}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2 justify-end pt-2">
              <Button variant="outline" onClick={resetDialog}>
                Importer un autre fichier
              </Button>
              <Button onClick={() => setOpen(false)} className="bg-teal-600 hover:bg-teal-700">
                Fermer
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default ImportStudentsCSV;
