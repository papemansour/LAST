import React, { useState } from 'react';
import { Card, CardContent } from './ui/card';
import { Star } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';

const testimonials = [
  {
    name: "Sophie Wane",
    role: "Étudiante en commerce",
    image: "https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg?auto=compress&cs=tinysrgb&w=200",
    content: "Grâce à KALAMAENGLISH, j'ai pu améliorer mon anglais professionnel en seulement 6 mois. Les professeurs sont excellents et très à l'écoute.",
    rating: 4
  },
  {
    name: "Gabriel Da SILVA",
    role: "Ingénieur",
    image: "https://images.pexels.com/photos/1516680/pexels-photo-1516680.jpeg?auto=compress&cs=tinysrgb&w=200",
    content: "La flexibilité des horaires et la qualité des cours m'ont permis de progresser rapidement. Je recommande vivement!",
    rating: 5
  },
  {
    name: "Kadia SY",
    role: "Chef d'entreprise",
    image: "https://images.pexels.com/photos/762020/pexels-photo-762020.jpeg?auto=compress&cs=tinysrgb&w=200",
    content: "Un service exceptionnel! Les cours sont adaptés à mes besoins professionnels et l'équipe est très réactive.",
    rating: 5
  },
  {
    name: "Élodie LEROUX",
    role: "Responsable marketing",
    image: "https://images.pexels.com/photos/1239291/pexels-photo-1239291.jpeg?auto=compress&cs=tinysrgb&w=200",
    content: "J'ai enfin pu atteindre mes objectifs en anglais grâce à un accompagnement personnalisé et des cours de qualité.",
    rating: 5
  }
];

const Testimonials = () => {
  const [selectedTestimonial, setSelectedTestimonial] = useState(null);
  const [showDialog, setShowDialog] = useState(false);

  const handleTestimonialClick = (testimonial) => {
    setSelectedTestimonial(testimonial);
    setShowDialog(true);
  };

  return (
    <>
      <section className="py-12 sm:py-20 px-4 bg-white">
        <div className="container mx-auto max-w-7xl">
          <h2 className="text-2xl sm:text-4xl font-bold text-center mb-2 sm:mb-4">Ce que disent nos étudiants</h2>
          <p className="text-center text-sm sm:text-base text-gray-600 mb-6 sm:mb-12">Découvrez les témoignages de ceux qui ont réussi avec nous</p>
          
          {/* Amélioration du scroll mobile avec indicateurs visuels */}
          <div className="relative">
            {/* Gradient indicateur gauche */}
            <div className="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-white to-transparent z-10 pointer-events-none md:hidden"></div>
            {/* Gradient indicateur droit */}
            <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-white to-transparent z-10 pointer-events-none md:hidden"></div>
            
            <div className="flex md:grid md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 overflow-x-auto snap-x snap-mandatory pb-4 -mx-4 px-4 md:mx-0 md:px-0" style={{ scrollbarWidth: 'thin', scrollbarColor: '#14b8a6 #f3f4f6' }}>
              {testimonials.map((testimonial, index) => (
                <Card 
                  key={index} 
                  className="hover:shadow-xl transition-all border-teal-100 min-w-[280px] w-[280px] sm:min-w-[300px] sm:w-[300px] md:min-w-0 md:w-auto flex-shrink-0 snap-center cursor-pointer hover:scale-105 active:scale-95"
                  onClick={() => handleTestimonialClick(testimonial)}
                >
                  <CardContent className="p-3 sm:p-6">
                    <div className="mb-3">
                      <h3 className="font-bold text-gray-900 text-base sm:text-lg">{testimonial.name}</h3>
                      <p className="text-xs sm:text-sm text-gray-600">{testimonial.role}</p>
                    </div>
                    <div className="flex gap-1 mb-2">
                      {[...Array(testimonial.rating)].map((_, i) => (
                        <Star key={i} className="w-4 h-4 sm:w-5 sm:h-5 fill-green-500 text-green-500" />
                      ))}
                    </div>
                    <p className="text-sm sm:text-base text-gray-700 italic line-clamp-3 overflow-hidden">"{testimonial.content}"</p>
                    <p className="text-xs text-teal-600 mt-2 font-medium">Cliquer pour lire plus →</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
          
          {/* Indicateur de scroll mobile */}
          <p className="text-center text-xs text-gray-500 mt-4 md:hidden">← Faites glisser pour voir plus →</p>
        </div>
      </section>

      {/* Dialog pour afficher le témoignage complet */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold text-teal-800">
              {selectedTestimonial?.name}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-gray-600">{selectedTestimonial?.role}</p>
            <div className="flex gap-1">
              {[...Array(selectedTestimonial?.rating || 0)].map((_, i) => (
                <Star key={i} className="w-5 h-5 fill-green-500 text-green-500" />
              ))}
            </div>
            <p className="text-base text-gray-700 italic">"{selectedTestimonial?.content}"</p>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default Testimonials;
