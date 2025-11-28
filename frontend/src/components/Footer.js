import React from 'react';
import { Mail, Phone, MapPin, Globe } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="bg-gradient-to-br from-teal-900 via-teal-800 to-teal-900 text-white">
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          {/* À Propos */}
          <div>
            <h3 className="text-2xl font-bold mb-4 flex items-center gap-2">
              <Globe className="w-6 h-6" />
              À Propos
            </h3>
            <p className="text-teal-100 leading-relaxed mb-4">
              <strong>My KALAMA ENGLISH</strong> a pour objectif de rendre l'apprentissage de l'anglais accessible à tous, avec des méthodes innovantes et personnalisées qui garantissent une progression rapide et efficace.
            </p>
            <p className="text-teal-200 text-sm italic">
              "Que vous soyez étudiant, professionnel, ou simplement désireux d'apprendre, nos cours sont conçus pour une progression rapide et efficace."
            </p>
          </div>

          {/* Contact */}
          <div>
            <h3 className="text-2xl font-bold mb-4">Contact</h3>
            <div className="space-y-3">
              <div className="flex items-start gap-3 text-teal-100">
                <Mail className="w-5 h-5 mt-1 flex-shrink-0" />
                <div>
                  <p className="font-medium">Email</p>
                  <a href="mailto:mykalamaenglish@gmail.com" className="hover:text-white transition">
                    mykalamaenglish@gmail.com
                  </a>
                </div>
              </div>
              <div className="flex items-start gap-3 text-teal-100">
                <Phone className="w-5 h-5 mt-1 flex-shrink-0" />
                <div>
                  <p className="font-medium">Téléphone</p>
                  <a href="tel:+221777010101" className="hover:text-white transition">
                    +221 77 701 01 01
                  </a>
                </div>
              </div>
              <div className="flex items-start gap-3 text-teal-100">
                <MapPin className="w-5 h-5 mt-1 flex-shrink-0" />
                <div>
                  <p className="font-medium">Localisation</p>
                  <p>Dakar, Sénégal</p>
                </div>
              </div>
            </div>
          </div>

          {/* Liens Rapides */}
          <div>
            <h3 className="text-2xl font-bold mb-4">Liens Rapides</h3>
            <ul className="space-y-2 text-teal-100">
              <li>
                <a href="#packs" className="hover:text-white transition hover:pl-2 inline-block duration-200">
                  → Nos Packs
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-white transition hover:pl-2 inline-block duration-200">
                  → Comment ça marche
                </a>
              </li>
              <li>
                <a href="#testimonials" className="hover:text-white transition hover:pl-2 inline-block duration-200">
                  → Témoignages
                </a>
              </li>
              <li>
                <a href="#contact" className="hover:text-white transition hover:pl-2 inline-block duration-200">
                  → Nous Contacter
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Créateur & Copyright */}
        <div className="border-t border-teal-700 pt-8 mt-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-center md:text-left">
              <p className="text-teal-100 mb-1">
                Créé avec ❤️ par <span className="font-bold text-white">DIAGNE Mouhamadou Mansour</span>
              </p>
              <p className="text-sm text-teal-300">
                Développeur Full Stack & Fondateur de My KALAMA ENGLISH
              </p>
            </div>
            <div className="text-center md:text-right">
              <p className="text-teal-200 text-sm">
                © {new Date().getFullYear()} My KALAMA ENGLISH
              </p>
              <p className="text-teal-300 text-xs">
                Tous droits réservés
              </p>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
