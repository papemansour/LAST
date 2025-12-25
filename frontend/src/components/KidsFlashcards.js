import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { toast } from 'sonner';
import { Heart, X, Check, RotateCcw, Star, ChevronLeft, ChevronRight, Volume2, Sparkles } from 'lucide-react';

// Données des flashcards par catégorie
const flashcardData = {
  alphabet: {
    title: "🔤 L'Alphabet",
    emoji: "🔤",
    color: "blue",
    cards: [
      { id: 'a1', front: 'A', back: 'Apple', image: '🍎', audio: 'A - Apple' },
      { id: 'a2', front: 'B', back: 'Ball', image: '⚽', audio: 'B - Ball' },
      { id: 'a3', front: 'C', back: 'Cat', image: '🐱', audio: 'C - Cat' },
      { id: 'a4', front: 'D', back: 'Dog', image: '🐕', audio: 'D - Dog' },
      { id: 'a5', front: 'E', back: 'Elephant', image: '🐘', audio: 'E - Elephant' },
      { id: 'a6', front: 'F', back: 'Fish', image: '🐟', audio: 'F - Fish' },
      { id: 'a7', front: 'G', back: 'Giraffe', image: '🦒', audio: 'G - Giraffe' },
      { id: 'a8', front: 'H', back: 'House', image: '🏠', audio: 'H - House' },
      { id: 'a9', front: 'I', back: 'Ice cream', image: '🍦', audio: 'I - Ice cream' },
      { id: 'a10', front: 'J', back: 'Juice', image: '🧃', audio: 'J - Juice' },
      { id: 'a11', front: 'K', back: 'Kite', image: '🪁', audio: 'K - Kite' },
      { id: 'a12', front: 'L', back: 'Lion', image: '🦁', audio: 'L - Lion' },
      { id: 'a13', front: 'M', back: 'Moon', image: '🌙', audio: 'M - Moon' },
      { id: 'a14', front: 'N', back: 'Nest', image: '🪹', audio: 'N - Nest' },
      { id: 'a15', front: 'O', back: 'Orange', image: '🍊', audio: 'O - Orange' },
      { id: 'a16', front: 'P', back: 'Pig', image: '🐷', audio: 'P - Pig' },
      { id: 'a17', front: 'Q', back: 'Queen', image: '👸', audio: 'Q - Queen' },
      { id: 'a18', front: 'R', back: 'Rainbow', image: '🌈', audio: 'R - Rainbow' },
      { id: 'a19', front: 'S', back: 'Sun', image: '☀️', audio: 'S - Sun' },
      { id: 'a20', front: 'T', back: 'Tree', image: '🌳', audio: 'T - Tree' },
      { id: 'a21', front: 'U', back: 'Umbrella', image: '☂️', audio: 'U - Umbrella' },
      { id: 'a22', front: 'V', back: 'Violin', image: '🎻', audio: 'V - Violin' },
      { id: 'a23', front: 'W', back: 'Water', image: '💧', audio: 'W - Water' },
      { id: 'a24', front: 'X', back: 'Xylophone', image: '🎹', audio: 'X - Xylophone' },
      { id: 'a25', front: 'Y', back: 'Yellow', image: '💛', audio: 'Y - Yellow' },
      { id: 'a26', front: 'Z', back: 'Zebra', image: '🦓', audio: 'Z - Zebra' }
    ]
  },
  numbers: {
    title: "🔢 Les Chiffres",
    emoji: "🔢",
    color: "green",
    cards: [
      { id: 'n1', front: '1', back: 'One', image: '1️⃣', audio: 'One' },
      { id: 'n2', front: '2', back: 'Two', image: '2️⃣', audio: 'Two' },
      { id: 'n3', front: '3', back: 'Three', image: '3️⃣', audio: 'Three' },
      { id: 'n4', front: '4', back: 'Four', image: '4️⃣', audio: 'Four' },
      { id: 'n5', front: '5', back: 'Five', image: '5️⃣', audio: 'Five' },
      { id: 'n6', front: '6', back: 'Six', image: '6️⃣', audio: 'Six' },
      { id: 'n7', front: '7', back: 'Seven', image: '7️⃣', audio: 'Seven' },
      { id: 'n8', front: '8', back: 'Eight', image: '8️⃣', audio: 'Eight' },
      { id: 'n9', front: '9', back: 'Nine', image: '9️⃣', audio: 'Nine' },
      { id: 'n10', front: '10', back: 'Ten', image: '🔟', audio: 'Ten' },
      { id: 'n11', front: '11', back: 'Eleven', image: '1️⃣1️⃣', audio: 'Eleven' },
      { id: 'n12', front: '12', back: 'Twelve', image: '1️⃣2️⃣', audio: 'Twelve' },
      { id: 'n13', front: '13', back: 'Thirteen', image: '1️⃣3️⃣', audio: 'Thirteen' },
      { id: 'n14', front: '14', back: 'Fourteen', image: '1️⃣4️⃣', audio: 'Fourteen' },
      { id: 'n15', front: '15', back: 'Fifteen', image: '1️⃣5️⃣', audio: 'Fifteen' },
      { id: 'n16', front: '16', back: 'Sixteen', image: '1️⃣6️⃣', audio: 'Sixteen' },
      { id: 'n17', front: '17', back: 'Seventeen', image: '1️⃣7️⃣', audio: 'Seventeen' },
      { id: 'n18', front: '18', back: 'Eighteen', image: '1️⃣8️⃣', audio: 'Eighteen' },
      { id: 'n19', front: '19', back: 'Nineteen', image: '1️⃣9️⃣', audio: 'Nineteen' },
      { id: 'n20', front: '20', back: 'Twenty', image: '2️⃣0️⃣', audio: 'Twenty' }
    ]
  },
  family: {
    title: "👨‍👩‍👧‍👦 La Famille",
    emoji: "👨‍👩‍👧‍👦",
    color: "purple",
    cards: [
      { id: 'f1', front: 'Maman', back: 'Mother / Mom', image: '👩', audio: 'Mother' },
      { id: 'f2', front: 'Papa', back: 'Father / Dad', image: '👨', audio: 'Father' },
      { id: 'f3', front: 'Frère', back: 'Brother', image: '👦', audio: 'Brother' },
      { id: 'f4', front: 'Sœur', back: 'Sister', image: '👧', audio: 'Sister' },
      { id: 'f5', front: 'Grand-mère', back: 'Grandmother / Grandma', image: '👵', audio: 'Grandmother' },
      { id: 'f6', front: 'Grand-père', back: 'Grandfather / Grandpa', image: '👴', audio: 'Grandfather' },
      { id: 'f7', front: 'Oncle', back: 'Uncle', image: '👨‍🦱', audio: 'Uncle' },
      { id: 'f8', front: 'Tante', back: 'Aunt', image: '👩‍🦱', audio: 'Aunt' },
      { id: 'f9', front: 'Cousin', back: 'Cousin (boy)', image: '🧒', audio: 'Cousin' },
      { id: 'f10', front: 'Cousine', back: 'Cousin (girl)', image: '👧', audio: 'Cousin' },
      { id: 'f11', front: 'Bébé', back: 'Baby', image: '👶', audio: 'Baby' },
      { id: 'f12', front: 'Famille', back: 'Family', image: '👨‍👩‍👧‍👦', audio: 'Family' }
    ]
  },
  colors: {
    title: "🎨 Les Couleurs",
    emoji: "🎨",
    color: "pink",
    cards: [
      { id: 'c1', front: 'Rouge', back: 'Red', image: '🔴', audio: 'Red' },
      { id: 'c2', front: 'Bleu', back: 'Blue', image: '🔵', audio: 'Blue' },
      { id: 'c3', front: 'Vert', back: 'Green', image: '🟢', audio: 'Green' },
      { id: 'c4', front: 'Jaune', back: 'Yellow', image: '🟡', audio: 'Yellow' },
      { id: 'c5', front: 'Orange', back: 'Orange', image: '🟠', audio: 'Orange' },
      { id: 'c6', front: 'Violet', back: 'Purple', image: '🟣', audio: 'Purple' },
      { id: 'c7', front: 'Rose', back: 'Pink', image: '💗', audio: 'Pink' },
      { id: 'c8', front: 'Noir', back: 'Black', image: '⚫', audio: 'Black' },
      { id: 'c9', front: 'Blanc', back: 'White', image: '⚪', audio: 'White' },
      { id: 'c10', front: 'Marron', back: 'Brown', image: '🟤', audio: 'Brown' },
      { id: 'c11', front: 'Gris', back: 'Gray', image: '🩶', audio: 'Gray' },
      { id: 'c12', front: 'Or', back: 'Gold', image: '⭐', audio: 'Gold' }
    ]
  },
  animals: {
    title: "🦁 Les Animaux",
    emoji: "🦁",
    color: "orange",
    cards: [
      { id: 'an1', front: 'Chat', back: 'Cat', image: '🐱', audio: 'Cat' },
      { id: 'an2', front: 'Chien', back: 'Dog', image: '🐕', audio: 'Dog' },
      { id: 'an3', front: 'Oiseau', back: 'Bird', image: '🐦', audio: 'Bird' },
      { id: 'an4', front: 'Poisson', back: 'Fish', image: '🐟', audio: 'Fish' },
      { id: 'an5', front: 'Lion', back: 'Lion', image: '🦁', audio: 'Lion' },
      { id: 'an6', front: 'Éléphant', back: 'Elephant', image: '🐘', audio: 'Elephant' },
      { id: 'an7', front: 'Girafe', back: 'Giraffe', image: '🦒', audio: 'Giraffe' },
      { id: 'an8', front: 'Singe', back: 'Monkey', image: '🐵', audio: 'Monkey' },
      { id: 'an9', front: 'Lapin', back: 'Rabbit', image: '🐰', audio: 'Rabbit' },
      { id: 'an10', front: 'Tortue', back: 'Turtle', image: '🐢', audio: 'Turtle' },
      { id: 'an11', front: 'Papillon', back: 'Butterfly', image: '🦋', audio: 'Butterfly' },
      { id: 'an12', front: 'Abeille', back: 'Bee', image: '🐝', audio: 'Bee' }
    ]
  }
};

// Couleurs par catégorie
const colorClasses = {
  blue: {
    bg: 'from-blue-400 to-cyan-400',
    card: 'border-blue-300 bg-gradient-to-br from-blue-50 to-cyan-50',
    button: 'bg-blue-500 hover:bg-blue-600',
    text: 'text-blue-700'
  },
  green: {
    bg: 'from-green-400 to-emerald-400',
    card: 'border-green-300 bg-gradient-to-br from-green-50 to-emerald-50',
    button: 'bg-green-500 hover:bg-green-600',
    text: 'text-green-700'
  },
  purple: {
    bg: 'from-purple-400 to-pink-400',
    card: 'border-purple-300 bg-gradient-to-br from-purple-50 to-pink-50',
    button: 'bg-purple-500 hover:bg-purple-600',
    text: 'text-purple-700'
  },
  pink: {
    bg: 'from-pink-400 to-rose-400',
    card: 'border-pink-300 bg-gradient-to-br from-pink-50 to-rose-50',
    button: 'bg-pink-500 hover:bg-pink-600',
    text: 'text-pink-700'
  },
  orange: {
    bg: 'from-orange-400 to-amber-400',
    card: 'border-orange-300 bg-gradient-to-br from-orange-50 to-amber-50',
    button: 'bg-orange-500 hover:bg-orange-600',
    text: 'text-orange-700'
  }
};

const KidsFlashcards = () => {
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [knownCards, setKnownCards] = useState([]);
  const [unknownCards, setUnknownCards] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [swipeDirection, setSwipeDirection] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [touchStart, setTouchStart] = useState(null);
  const cardRef = useRef(null);

  // Load saved progress from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('kkid_flashcard_progress');
    if (saved) {
      try {
        const data = JSON.parse(saved);
        if (data.known) setKnownCards(data.known);
        if (data.unknown) setUnknownCards(data.unknown);
        if (data.favorites) setFavorites(data.favorites);
      } catch (e) {
        console.log('Error loading flashcard progress:', e);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Save progress
  useEffect(() => {
    if (knownCards.length > 0 || unknownCards.length > 0 || favorites.length > 0) {
      localStorage.setItem('kkid_flashcard_progress', JSON.stringify({
        known: knownCards,
        unknown: unknownCards,
        favorites: favorites
      }));
    }
  }, [knownCards, unknownCards, favorites]);

  const currentCards = selectedCategory ? flashcardData[selectedCategory].cards : [];
  const currentCard = currentCards[currentIndex];
  const colors = selectedCategory ? colorClasses[flashcardData[selectedCategory].color] : colorClasses.blue;

  // Text-to-speech function
  const speak = (text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'en-US';
      utterance.rate = 0.8;
      utterance.pitch = 1.1;
      speechSynthesis.speak(utterance);
    }
  };

  // Handle card actions
  const handleKnown = () => {
    if (!currentCard) return;
    setSwipeDirection('right');
    setKnownCards(prev => [...prev.filter(id => id !== currentCard.id), currentCard.id]);
    setUnknownCards(prev => prev.filter(id => id !== currentCard.id));
    toast.success('Super ! Tu connais ce mot ! 🌟', { duration: 1500 });
    
    setTimeout(() => {
      setSwipeDirection(null);
      setIsFlipped(false);
      if (currentIndex < currentCards.length - 1) {
        setCurrentIndex(prev => prev + 1);
      } else {
        setShowResult(true);
      }
    }, 300);
  };

  const handleUnknown = () => {
    if (!currentCard) return;
    setSwipeDirection('left');
    setUnknownCards(prev => [...prev.filter(id => id !== currentCard.id), currentCard.id]);
    setKnownCards(prev => prev.filter(id => id !== currentCard.id));
    toast.info('Pas de souci, on va réviser ! 📚', { duration: 1500 });
    
    setTimeout(() => {
      setSwipeDirection(null);
      setIsFlipped(false);
      if (currentIndex < currentCards.length - 1) {
        setCurrentIndex(prev => prev + 1);
      } else {
        setShowResult(true);
      }
    }, 300);
  };

  const handleFavorite = () => {
    if (!currentCard) return;
    if (favorites.includes(currentCard.id)) {
      setFavorites(prev => prev.filter(id => id !== currentCard.id));
      toast.info('Retiré des favoris', { duration: 1500 });
    } else {
      setFavorites(prev => [...prev, currentCard.id]);
      toast.success('Ajouté aux favoris ! ⭐', { duration: 1500 });
    }
  };

  const handleFlip = () => {
    setIsFlipped(!isFlipped);
    if (!isFlipped && currentCard) {
      speak(currentCard.back);
    }
  };

  // Touch handlers for swipe
  const handleTouchStart = (e) => {
    setTouchStart(e.touches[0].clientX);
  };

  const handleTouchEnd = (e) => {
    if (!touchStart) return;
    const touchEnd = e.changedTouches[0].clientX;
    const diff = touchStart - touchEnd;
    
    if (Math.abs(diff) > 50) {
      if (diff > 0) {
        handleUnknown(); // Swipe left = don't know
      } else {
        handleKnown(); // Swipe right = know
      }
    }
    setTouchStart(null);
  };

  const resetCategory = () => {
    setCurrentIndex(0);
    setIsFlipped(false);
    setShowResult(false);
  };

  const goBack = () => {
    setSelectedCategory(null);
    setCurrentIndex(0);
    setIsFlipped(false);
    setShowResult(false);
  };

  // Category selection view
  if (!selectedCategory) {
    return (
      <div className="space-y-6">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-pink-700 mb-2">🃏 Jeu de Flashcards</h2>
          <p className="text-gray-600">Choisis une catégorie pour commencer !</p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {Object.entries(flashcardData).map(([key, data]) => {
            const categoryColors = colorClasses[data.color];
            const categoryKnown = data.cards.filter(c => knownCards.includes(c.id)).length;
            const progress = (categoryKnown / data.cards.length) * 100;
            
            return (
              <Card 
                key={key}
                className={`${categoryColors.card} hover:shadow-xl transition-all cursor-pointer transform hover:scale-105 border-2`}
                onClick={() => setSelectedCategory(key)}
              >
                <CardContent className="p-4 text-center">
                  <div className="text-5xl mb-3 animate-bounce">{data.emoji}</div>
                  <h3 className={`font-bold text-lg ${categoryColors.text}`}>{data.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{data.cards.length} cartes</p>
                  
                  {/* Progress bar */}
                  <div className="mt-3">
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className={`h-full bg-gradient-to-r ${categoryColors.bg} transition-all duration-500`}
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{categoryKnown}/{data.cards.length} appris</p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Favorites Section */}
        {favorites.length > 0 && (
          <Card className="border-amber-200 bg-gradient-to-r from-amber-50 to-yellow-50 mt-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-amber-700">
                <Star className="w-5 h-5 fill-amber-400 text-amber-400" />
                Mes Favoris ({favorites.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {favorites.map(favId => {
                  // Find the card across all categories
                  for (const [, data] of Object.entries(flashcardData)) {
                    const card = data.cards.find(c => c.id === favId);
                    if (card) {
                      return (
                        <span 
                          key={favId} 
                          className="px-3 py-1 bg-amber-100 rounded-full text-sm flex items-center gap-1"
                        >
                          {card.image} {card.back}
                        </span>
                      );
                    }
                  }
                  return null;
                })}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  // Results view
  if (showResult) {
    const categoryKnown = currentCards.filter(c => knownCards.includes(c.id)).length;
    const categoryUnknown = currentCards.filter(c => unknownCards.includes(c.id)).length;
    const percentage = Math.round((categoryKnown / currentCards.length) * 100);
    
    return (
      <div className="text-center space-y-6">
        <Card className={`${colors.card} border-2 max-w-md mx-auto`}>
          <CardContent className="p-8">
            <div className="text-6xl mb-4">
              {percentage >= 80 ? '🏆' : percentage >= 50 ? '⭐' : '💪'}
            </div>
            <h2 className={`text-2xl font-bold ${colors.text} mb-4`}>
              {percentage >= 80 ? 'Excellent !' : percentage >= 50 ? 'Bien joué !' : 'Continue comme ça !'}
            </h2>
            
            <div className="space-y-4 mb-6">
              <div className="flex items-center justify-between p-3 bg-green-100 rounded-lg">
                <span className="flex items-center gap-2">
                  <Check className="w-5 h-5 text-green-600" />
                  <span className="text-green-700">Je connais</span>
                </span>
                <span className="font-bold text-green-700">{categoryKnown}</span>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-red-100 rounded-lg">
                <span className="flex items-center gap-2">
                  <X className="w-5 h-5 text-red-600" />
                  <span className="text-red-700">À réviser</span>
                </span>
                <span className="font-bold text-red-700">{categoryUnknown}</span>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-amber-100 rounded-lg">
                <span className="flex items-center gap-2">
                  <Heart className="w-5 h-5 text-amber-600 fill-amber-500" />
                  <span className="text-amber-700">Favoris</span>
                </span>
                <span className="font-bold text-amber-700">
                  {currentCards.filter(c => favorites.includes(c.id)).length}
                </span>
              </div>
            </div>
            
            <div className="text-4xl font-bold text-gray-700 mb-2">{percentage}%</div>
            <p className="text-gray-500">de bonnes réponses</p>
          </CardContent>
        </Card>
        
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button 
            onClick={resetCategory}
            className={`${colors.button} text-white`}
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Recommencer
          </Button>
          <Button variant="outline" onClick={goBack}>
            <ChevronLeft className="w-4 h-4 mr-2" />
            Autres catégories
          </Button>
        </div>
      </div>
    );
  }

  // Flashcard game view
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" size="sm" onClick={goBack}>
          <ChevronLeft className="w-4 h-4 mr-1" />
          Retour
        </Button>
        <div className="text-center">
          <h2 className={`font-bold ${colors.text}`}>
            {flashcardData[selectedCategory].emoji} {flashcardData[selectedCategory].title}
          </h2>
          <p className="text-xs text-gray-500">
            Carte {currentIndex + 1} / {currentCards.length}
          </p>
        </div>
        <Button 
          variant="ghost" 
          size="sm"
          onClick={handleFavorite}
          className={favorites.includes(currentCard?.id) ? 'text-amber-500' : 'text-gray-400'}
        >
          <Star className={`w-5 h-5 ${favorites.includes(currentCard?.id) ? 'fill-amber-400' : ''}`} />
        </Button>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div 
          className={`h-full bg-gradient-to-r ${colors.bg} transition-all duration-300`}
          style={{ width: `${((currentIndex + 1) / currentCards.length) * 100}%` }}
        />
      </div>

      {/* Flashcard */}
      <div 
        className="flex justify-center items-center min-h-[300px]"
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        <div
          ref={cardRef}
          className={`relative w-full max-w-sm h-[300px] cursor-pointer perspective-1000 transition-all duration-300 transform
            ${swipeDirection === 'left' ? '-translate-x-full opacity-0 rotate-[-20deg]' : ''}
            ${swipeDirection === 'right' ? 'translate-x-full opacity-0 rotate-[20deg]' : ''}
          `}
          onClick={handleFlip}
        >
          <div className={`relative w-full h-full transition-transform duration-500 transform-style-preserve-3d ${isFlipped ? 'rotate-y-180' : ''}`}>
            {/* Front of card */}
            <Card className={`absolute w-full h-full ${colors.card} border-4 shadow-xl backface-hidden`}>
              <CardContent className="flex flex-col items-center justify-center h-full p-6">
                <div className="text-8xl mb-4 animate-pulse">{currentCard?.image}</div>
                <h3 className={`text-3xl font-bold ${colors.text}`}>{currentCard?.front}</h3>
                <p className="text-sm text-gray-500 mt-4">👆 Touche pour voir la réponse</p>
              </CardContent>
            </Card>
            
            {/* Back of card */}
            <Card className={`absolute w-full h-full ${colors.card} border-4 shadow-xl backface-hidden rotate-y-180`}>
              <CardContent className="flex flex-col items-center justify-center h-full p-6">
                <div className="text-6xl mb-4">{currentCard?.image}</div>
                <h3 className={`text-2xl font-bold ${colors.text} mb-2`}>{currentCard?.back}</h3>
                <Button 
                  size="sm" 
                  variant="ghost"
                  className="mt-2"
                  onClick={(e) => {
                    e.stopPropagation();
                    speak(currentCard?.back);
                  }}
                >
                  <Volume2 className="w-5 h-5 mr-1" />
                  Écouter
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Swipe instructions */}
      <div className="text-center text-sm text-gray-500 mb-2">
        👈 Glisse à gauche = Je ne connais pas | Glisse à droite = Je connais 👉
      </div>

      {/* Action buttons */}
      <div className="flex justify-center gap-4">
        <Button 
          size="lg"
          variant="outline"
          className="rounded-full w-16 h-16 border-2 border-red-300 bg-red-50 hover:bg-red-100 text-red-600"
          onClick={handleUnknown}
        >
          <X className="w-8 h-8" />
        </Button>
        
        <Button 
          size="lg"
          variant="outline"
          className={`rounded-full w-16 h-16 border-2 ${
            favorites.includes(currentCard?.id) 
              ? 'border-amber-400 bg-amber-100 text-amber-600' 
              : 'border-amber-300 bg-amber-50 hover:bg-amber-100 text-amber-600'
          }`}
          onClick={handleFavorite}
        >
          <Heart className={`w-8 h-8 ${favorites.includes(currentCard?.id) ? 'fill-amber-500' : ''}`} />
        </Button>
        
        <Button 
          size="lg"
          variant="outline"
          className="rounded-full w-16 h-16 border-2 border-green-300 bg-green-50 hover:bg-green-100 text-green-600"
          onClick={handleKnown}
        >
          <Check className="w-8 h-8" />
        </Button>
      </div>

      {/* Button labels */}
      <div className="flex justify-center gap-4 text-xs text-gray-500">
        <span className="w-16 text-center">Je ne<br/>connais pas</span>
        <span className="w-16 text-center">Favori</span>
        <span className="w-16 text-center">Je<br/>connais</span>
      </div>

      {/* Navigation arrows */}
      <div className="flex justify-between mt-4">
        <Button 
          variant="ghost" 
          size="sm"
          disabled={currentIndex === 0}
          onClick={() => {
            setCurrentIndex(prev => prev - 1);
            setIsFlipped(false);
          }}
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          Précédent
        </Button>
        <Button 
          variant="ghost" 
          size="sm"
          disabled={currentIndex === currentCards.length - 1}
          onClick={() => {
            setCurrentIndex(prev => prev + 1);
            setIsFlipped(false);
          }}
        >
          Suivant
          <ChevronRight className="w-4 h-4 ml-1" />
        </Button>
      </div>

      {/* CSS for 3D transforms */}
      <style>{`
        .perspective-1000 {
          perspective: 1000px;
        }
        .transform-style-preserve-3d {
          transform-style: preserve-3d;
        }
        .backface-hidden {
          backface-visibility: hidden;
        }
        .rotate-y-180 {
          transform: rotateY(180deg);
        }
      `}</style>
    </div>
  );
};

export default KidsFlashcards;
