import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { CurrencyToggle, useCurrency } from '../components/CurrencySelector';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { Calendar } from '../components/ui/calendar';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../components/ui/card';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '../components/ui/popover';
import { toast } from 'sonner';
import axios from 'axios';
import { ChevronRight, Users, BookOpen, Clock, Calendar as CalendarIcon, X } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import Testimonials from '../components/Testimonials';
import HowItWorks from '../components/HowItWorks';
import DonationButton from '../components/DonationButton';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const timeSlots = [
  '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', 
  '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00'
];

const HomePage = () => {
  const navigate = useNavigate();
  const { currency, formatPrice, formatPriceWithSmallFCFA, EUR_TO_FCFA } = useCurrency();
  const [courseType, setCourseType] = useState('individual'); // 'individual' ou 'group'
  const [additionalMembers, setAdditionalMembers] = useState([]);  // Membres additionnels (juste nom/prénom)
  const [groupCode, setGroupCode] = useState('');
  const [groupCodeInfo, setGroupCodeInfo] = useState(null);
  const [validatingCode, setValidatingCode] = useState(false);
  const [numberOfStudents, setNumberOfStudents] = useState(2);
  const [sharedLoginCode, setSharedLoginCode] = useState(null);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [pricingData, setPricingData] = useState({
    kkid_eur: 30,
    kkid_discount: 0,
    beginner_eur: 60,
    beginner_discount: 0,
    intermediate_eur: 90,
    intermediate_discount: 0,
    advanced_eur: 120,
    advanced_discount: 0
  });
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    country_code: '+33',
    level: '',
    preferred_slots: '',
    referral_source: '',
    join_kalama_club: false
  });
  const [loading, setLoading] = useState(false);
  const [selectedDates, setSelectedDates] = useState([]);
  const [selectedTimeSlots, setSelectedTimeSlots] = useState({});
  const [showCalendar, setShowCalendar] = useState(false);
  const [showRegistrationModal, setShowRegistrationModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [contactForm, setContactForm] = useState({
    name: '',
    email: '',
    message: ''
  });
  const [sendingContact, setSendingContact] = useState(false);
  const [showWavePaymentModal, setShowWavePaymentModal] = useState(false);
  const [registrationSuccess, setRegistrationSuccess] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('stripe'); // 'stripe' ou 'wave'
  // Promo code is always KALAMA15 - no need for validation states
  const [groupMembers, setGroupMembers] = useState([{ 
    first_name: '', 
    last_name: '', 
    email: '', 
    phone: '', 
    country_code: '+33', 
    level: '' 
  }]);

  const handleDateSelect = (date) => {
    const dateStr = format(date, 'yyyy-MM-dd');
    if (selectedDates.find(d => d === dateStr)) {
      setSelectedDates(selectedDates.filter(d => d !== dateStr));
      const newSlots = { ...selectedTimeSlots };
      delete newSlots[dateStr];
      setSelectedTimeSlots(newSlots);
    } else {
      setSelectedDates([...selectedDates, dateStr]);
    }
  };

  const handleTimeSlotSelect = (dateStr, time) => {
    const currentSlots = selectedTimeSlots[dateStr] || [];
    if (currentSlots.includes(time)) {
      setSelectedTimeSlots({
        ...selectedTimeSlots,
        [dateStr]: currentSlots.filter(t => t !== time)
      });
    } else {
      setSelectedTimeSlots({
        ...selectedTimeSlots,
        [dateStr]: [...currentSlots, time]
      });
    }
  };

  // Charger les prix depuis l'API
  useEffect(() => {
    const fetchPricing = async () => {
      try {
        const response = await axios.get(`${API}/pricing`);
        setPricingData(response.data);
      } catch (error) {
        console.error('Error fetching pricing:', error);
      }
    };
    fetchPricing();

    // Ouvrir automatiquement la modale d'inscription si paramètre URL
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('openRegister') === 'true') {
      setTimeout(() => {
        // Ouvrir avec le pack intermédiaire par défaut
        openRegistrationModal({ 
          name: 'Pack Intermédiaire', 
          level: 'intermediate', 
          price: pricingData.intermediate_eur - pricingData.intermediate_discount 
        });
        // Nettoyer l'URL
        window.history.replaceState({}, '', '/');
      }, 500);
    }
  }, []);

  const formatPreferredSlots = () => {
    const slots = [];
    Object.keys(selectedTimeSlots).forEach(dateStr => {
      const times = selectedTimeSlots[dateStr];
      if (times && times.length > 0) {
        const date = new Date(dateStr);
        const dayName = format(date, 'EEEE', { locale: fr });
        slots.push(`${dayName} ${times.join(', ')}`);
      }
    });
    return slots.join(' | ');
  };

  const handleAddGroupMember = () => {
    if (groupMembers.length < 3) {
      setGroupMembers([...groupMembers, { 
        first_name: '', 
        last_name: '', 
        email: '', 
        phone: '', 
        country_code: '+33', 
        level: '' 
      }]);
    } else {
      toast.error('Maximum 3 personnes pour un cours groupé');
    }
  };

  const handleRemoveGroupMember = (index) => {
    if (groupMembers.length > 1) {
      setGroupMembers(groupMembers.filter((_, i) => i !== index));
    }
  };

  const handleGroupMemberChange = (index, field, value) => {
    const updated = [...groupMembers];
    updated[index][field] = value;
    setGroupMembers(updated);
  };


  // Fonction pour valider le code de groupe
  const validateGroupCode = async (code) => {
    if (!code || code.trim().length === 0) {
      setGroupCodeInfo(null);
      return;
    }

    setValidatingCode(true);
    try {
      const response = await axios.get(`${API}/auth/validate-code/${code.trim().toUpperCase()}`);
      setGroupCodeInfo(response.data);
      toast.success(`Code valide ! Groupe "${response.data.group_name}" trouvé`);
    } catch (error) {
      setGroupCodeInfo(null);
      if (error.response?.status === 404) {
        toast.error('Code invalide. Vérifiez le code fourni par votre professeur.');
      } else if (error.response?.status === 400) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Erreur lors de la validation du code');
      }
    } finally {
      setValidatingCode(false);
    }
  };

  // Validation automatique quand le code change
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (groupCode && groupCode.length >= 4) {
        validateGroupCode(groupCode);
      } else {
        setGroupCodeInfo(null);
      }
    }, 500); // Délai de 500ms pour éviter trop d'appels API

    return () => clearTimeout(timeoutId);
  }, [groupCode]);

  // Fonction pour obtenir le lien Stripe selon le pack et KALAMA CLUB
  // Promo code KALAMA15 is always applied automatically on backend

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation pour cours groupé
    if (courseType === 'group') {
      if (!formData.first_name || !formData.last_name || !formData.email || !formData.phone || !formData.level) {
        toast.error('Veuillez remplir tous les champs obligatoires');
        return;
      }
      if (additionalMembers.length === 0) {
        toast.error('Pour un cours groupé, vous devez ajouter au moins une personne supplémentaire');
        return;
      }
      // Validate additional members
      const hasInvalidMember = additionalMembers.some(member => 
        !member.first_name || !member.last_name
      );
      if (hasInvalidMember) {
        toast.error('Veuillez remplir le nom et prénom de tous les membres');
        return;
      }
    } else {
      if (!formData.level) {
        toast.error('Veuillez sélectionner votre niveau');
        return;
      }
    }

    setLoading(true);

    try {
      if (courseType === 'group') {
        // Inscription de groupe (sans code magique - sera généré par l'admin)
        const fullPhone = `${formData.country_code}${formData.phone}`;
        const preferredSlots = formatPreferredSlots();
        const response = await axios.post(`${API}/auth/register-group`, {
          first_name: formData.first_name,
          last_name: formData.last_name,
          email: formData.email,
          phone: fullPhone,
          country_code: formData.country_code,
          level: formData.level,
          additional_members: additionalMembers,
          preferred_slots: preferredSlots || '',
          referral_source: formData.referral_source || ''
        });
        
        toast.success(response.data.message);
      } else {
        // Inscription individuelle
        const fullPhone = `${formData.country_code}${formData.phone}`;
        const preferredSlots = formatPreferredSlots();
        await axios.post(`${API}/auth/register`, {
          ...formData,
          phone: fullPhone,
          preferred_slots: preferredSlots || formData.preferred_slots,
          course_type: 'individual'
        });
        toast.success('Inscription envoyée avec succès! Attendez l\'approbation de l\'administrateur.');
      }
      
      // Reset form
      setFormData({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        country_code: '+33',
        level: '',
        preferred_slots: '',
        referral_source: '',
        join_kalama_club: false
      });
      setAdditionalMembers([]);
      setGroupCode('');
      setGroupCodeInfo(null);
      setNumberOfStudents(2);
      setSelectedDates([]);
      setSelectedTimeSlots({});
      setShowRegistrationModal(false);
      setRegistrationSuccess(true);
      
      // Show payment options modal
      if (selectedPlan) {
        setTimeout(() => {
          setShowWavePaymentModal(true);
        }, 500);
      } else {
        toast.success('Inscription envoyée avec succès!');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de l\'inscription');
    } finally {
      setLoading(false);
    }
  };

  const handleContactSubmit = async (e) => {
    e.preventDefault();
    
    if (!contactForm.name || !contactForm.email || !contactForm.message) {
      toast.error('Veuillez remplir tous les champs');
      return;
    }

    setSendingContact(true);

    try {
      await axios.post(`${API}/contact/send`, contactForm);
      toast.success('Message envoyé avec succès! Nous vous répondrons bientôt.');
      setContactForm({
        name: '',
        email: '',
        message: ''
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de l\'envoi du message');
    } finally {
      setSendingContact(false);
    }
  };

  const handleDirectPayment = async (plan) => {
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
      const API = `${BACKEND_URL}/api`;
      
      toast.info('Redirection vers le paiement Stripe...');
      
      // Call backend to create Stripe checkout session with promo code
      const response = await axios.post(`${API}/payments/create-checkout`, {
        plan_name: plan.name,
        plan_level: plan.level,
        amount: plan.price,
        currency: currency,
        promo_code: 'promo_1SYGM3I4faCc3GWYbdYRPXX8'
      });
      
      // Redirect to Stripe Checkout
      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url;
      }
    } catch (error) {
      toast.error('Erreur lors de la création de la session de paiement');
      console.error(error);
    }
  };

  const openRegistrationModal = (plan = null) => {
    setSelectedPlan(plan);
    if (plan) {
      setFormData({ ...formData, level: plan.level });
    }
    setShowRegistrationModal(true);
  };

  const handleStripePayment = async (plan) => {
    // Use the level and join_kalama_club from formData
    const level = plan?.level || formData.level;
    const joinKalamaClub = formData.join_kalama_club;
    
    console.log('Stripe payment:', { level, joinKalamaClub });
    
    try {
      toast.info('Redirection vers Stripe...');
      
      // Get pack details
      const packMapping = {
        'kkid': { name: 'Pack K-Kid', amount: 15000 },
        'beginner': { name: joinKalamaClub ? 'Pack K-Débutant + Club' : 'Pack K-Débutant', amount: joinKalamaClub ? 20000 : 15000 },
        'intermediate': { name: joinKalamaClub ? 'Pack K-Intermédiaire + Club' : 'Pack K-Intermédiaire', amount: joinKalamaClub ? 25000 : 20000 },
        'advanced': { name: joinKalamaClub ? 'Pack K-Avancé + Club' : 'Pack K-Avancé', amount: joinKalamaClub ? 30000 : 25000 }
      };
      
      const packInfo = packMapping[level];
      
      if (!packInfo) {
        toast.error('Erreur : Pack non trouvé');
        return;
      }
      
      // Call backend to create Stripe session with promo code
      const response = await axios.post(`${API}/payments/create-checkout`, {
        plan_name: packInfo.name,
        plan_level: level,
        amount: packInfo.amount,
        currency: currency,
        promo_code: 'promo_1SYGM3I4faCc3GWYbdYRPXX8'
      });
      
      // Redirect to Stripe Checkout
      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url;
      } else {
        toast.error('Erreur lors de la création de la session de paiement');
      }
    } catch (error) {
      console.error('Payment error:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors de la redirection vers le paiement');
    }
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-white shadow-sm fixed w-full top-0 z-50">
        <div className="container mx-auto px-4 py-3 md:py-4 flex justify-between items-center">
          <div className="flex flex-col">
            <h1 className="text-lg sm:text-xl md:text-2xl font-bold text-teal-600">My KALAMA</h1>
            <span className="text-xs sm:text-sm text-gray-600 font-semibold uppercase tracking-wide">English</span>
          </div>
          <Link to="/login">
            <Button variant="outline" data-testid="login-nav-button" className="border-teal-600 text-teal-600 hover:bg-teal-50 text-sm md:text-base px-3 py-1 md:px-4 md:py-2">
              Connexion
            </Button>
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center pt-16 md:pt-0">
        <div className="absolute inset-0">
          <img
            src="https://images.pexels.com/photos/4050315/pexels-photo-4050315.jpeg?auto=compress&cs=tinysrgb&w=1920"
            alt="Maîtrisez votre anglais"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-black/70 to-black/50"></div>
        </div>
        <div className="relative z-10 container mx-auto px-4 py-12 md:py-20">
          <div className="max-w-3xl">
            <div className="grid grid-cols-3 gap-2 sm:gap-4 mb-6 md:mb-8">
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-2 sm:p-4 hover:bg-white/20 transition-colors">
                <div className="text-2xl sm:text-3xl md:text-4xl font-bold text-teal-400 mb-1 md:mb-2">95%</div>
                <p className="text-gray-200 text-xs sm:text-sm">Taux de réussite</p>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-2 sm:p-4 hover:bg-white/20 transition-colors">
                <div className="text-2xl sm:text-3xl md:text-4xl font-bold text-teal-400 mb-1 md:mb-2">+200</div>
                <p className="text-gray-200 text-xs sm:text-sm">Heures de cours</p>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-lg p-2 sm:p-4 hover:bg-white/20 transition-colors">
                <div className="text-2xl sm:text-3xl md:text-4xl font-bold text-teal-400 mb-1 md:mb-2">24/7</div>
                <p className="text-gray-200 text-xs sm:text-sm">Accès aux cours</p>
              </div>
            </div>
            <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-4 md:mb-6 leading-tight">
              Apprenez l'anglais facilement avec des méthodes innovantes
            </h1>
            <p className="text-sm sm:text-base lg:text-lg text-gray-200 mb-6 md:mb-8 leading-relaxed">
              My KALAMA ENGLISH rend l'apprentissage de l'anglais accessible à tous ! Que vous soyez étudiant, professionnel, ou simplement désireux d'apprendre, nos cours sont conçus pour une progression rapide et efficace.
            </p>
            <button 
              onClick={() => openRegistrationModal()}
              className="inline-flex items-center px-4 sm:px-6 py-2 sm:py-3 bg-teal-600 text-white rounded-full font-semibold hover:bg-teal-700 transition duration-300 text-sm sm:text-base"
            >
              Commencer à apprendre
            </button>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-12 md:py-16 px-4 bg-white">
        <div className="container mx-auto max-w-7xl">
          <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4 md:gap-8">
            <div className="bg-teal-50 p-4 md:p-6 rounded-lg hover:shadow-md transition-shadow">
              <div className="p-3 md:p-4 bg-white rounded-lg inline-block mb-3 md:mb-4">
                <BookOpen className="w-6 h-6 md:w-8 md:h-8 text-teal-600" />
              </div>
              <h3 className="text-lg md:text-xl font-bold mb-2 md:mb-3 text-teal-800">Apprentissage personnalisé</h3>
              <p className="text-sm md:text-base text-gray-700">Des cours adaptés à votre niveau et à vos objectifs spécifiques</p>
            </div>

            <div className="bg-teal-50 p-4 md:p-6 rounded-lg hover:shadow-md transition-shadow">
              <div className="p-3 md:p-4 bg-white rounded-lg inline-block mb-3 md:mb-4">
                <Users className="w-6 h-6 md:w-8 md:h-8 text-teal-600" />
              </div>
              <h3 className="text-lg md:text-xl font-bold mb-2 md:mb-3 text-teal-800">Professeurs qualifiés</h3>
              <p className="text-sm md:text-base text-gray-700">Une équipe d'experts passionnés par l'enseignement de l'anglais</p>
            </div>

            <div className="bg-teal-50 p-4 md:p-6 rounded-lg hover:shadow-md transition-shadow sm:col-span-2 md:col-span-1">
              <div className="p-3 md:p-4 bg-white rounded-lg inline-block mb-3 md:mb-4">
                <Clock className="w-6 h-6 md:w-8 md:h-8 text-teal-600" />
              </div>
              <h3 className="text-lg md:text-xl font-bold mb-2 md:mb-3 text-teal-800">Flexibilité totale</h3>
              <p className="text-sm md:text-base text-gray-700">Apprenez à votre rythme avec des horaires adaptés à votre emploi du temps</p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-12 md:py-20 px-4 bg-gradient-to-b from-teal-50 to-white">
        <div className="container mx-auto max-w-7xl">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-center mb-3 md:mb-4">Tarifs & Niveaux</h2>
          
          <div className="flex justify-center mb-4 md:mb-6">
            <CurrencyToggle />
          </div>
          
          <p className="text-center text-base sm:text-lg md:text-xl text-red-600 font-semibold mb-3 md:mb-4 px-4">
            🎄 Promo Noël & Nouvel An - Valable jusqu'au 14 janvier 2025
          </p>
          <div className="text-center mb-8 md:mb-12 px-4">
            <p className="text-base sm:text-lg md:text-xl font-semibold text-gray-800 mb-2">
              🎯 <span className="bg-gradient-to-r from-teal-600 to-blue-600 bg-clip-text text-transparent">Votre formation, votre rythme</span>
            </p>
            <p className="text-sm sm:text-base text-gray-600 flex items-center justify-center gap-2 flex-wrap">
              <span className="inline-flex items-center gap-1 bg-teal-50 px-3 py-1 rounded-full border border-teal-200">
                <span className="text-lg">👤</span> 
                <span className="font-medium text-teal-700">Solo</span>
              </span>
              <span className="text-gray-400">ou</span>
              <span className="inline-flex items-center gap-1 bg-blue-50 px-3 py-1 rounded-full border border-blue-200">
                <span className="text-lg">👥</span> 
                <span className="font-medium text-blue-700">En trio</span>
                <span className="text-xs text-blue-600">(max 3)</span>
              </span>
            </p>
          </div>

          <div className="relative">
            {/* Gradient indicateur gauche */}
            <div className="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-teal-50 to-transparent z-10 pointer-events-none md:hidden"></div>
            {/* Gradient indicateur droit */}
            <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-teal-50 to-transparent z-10 pointer-events-none md:hidden"></div>
            
            <div className="flex overflow-x-auto gap-4 md:gap-6 pb-4 snap-x snap-mandatory -mx-4 px-4 md:mx-0 md:px-0" style={{ scrollbarWidth: 'thin', scrollbarColor: '#14b8a6 #f3f4f6' }}>
            {/* Pack K-Kid - Enfants */}
            <div className="relative overflow-hidden rounded-2xl border-2 border-pink-300 bg-white/60 backdrop-blur-lg hover:shadow-xl transition-all min-w-[280px] sm:min-w-[320px] flex-shrink-0 snap-center">
              <div className="bg-gradient-to-br from-pink-50 to-pink-100 p-4 md:p-6">
                <h3 className="text-xl md:text-2xl font-bold text-pink-800">Pack K-Kid</h3>
                <p className="text-sm md:text-base text-pink-600">Enfants 3-9 ans</p>
              </div>
              <div className="p-4 md:p-6">
                <div className="text-center mb-4 md:mb-6">
                  {pricingData.kkid_discount > 0 && (
                    <div className="text-gray-400 line-through text-lg md:text-xl">
                      {formatPrice(pricingData.kkid_eur, pricingData.kkid_fcfa)}
                    </div>
                  )}
                  <div className="text-2xl md:text-3xl font-bold text-pink-600">
                    {formatPriceWithSmallFCFA(
                      pricingData.kkid_eur - (pricingData.kkid_discount || 0),
                      (pricingData.kkid_fcfa || 0) - (pricingData.kkid_discount_fcfa || 0)
                    )}
                  </div>
                  {pricingData.kkid_discount > 0 && (
                    <div className="text-green-600 font-semibold mt-1 md:mt-2 text-sm md:text-base">
                      💰 Économisez {formatPrice(pricingData.kkid_discount, pricingData.kkid_discount_fcfa)}
                    </div>
                  )}
                </div>
                <ul className="space-y-2 md:space-y-3 text-sm md:text-base">
                  <li className="flex items-center gap-2">
                    <ChevronRight className="w-4 h-4 md:w-5 md:h-5 text-pink-600 flex-shrink-0" />
                    <span>Vidéos et jeux interactifs pré-fabriqués</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <ChevronRight className="w-4 h-4 md:w-5 md:h-5 text-pink-600 flex-shrink-0" />
                    <span>Limite le temps d'écran bleu</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <ChevronRight className="w-4 h-4 md:w-5 md:h-5 text-pink-600 flex-shrink-0" />
                    <span>Favorise les interactions réelles</span>
                  </li>
                </ul>
                <Button 
                  className="w-full mt-4 md:mt-6 bg-pink-600 hover:bg-pink-700 text-sm md:text-base py-2 md:py-3" 
                  data-testid="pay-kkid"
                  onClick={() => openRegistrationModal({ 
                    name: 'Pack K-Kid', 
                    level: 'kkid', 
                    price: pricingData.kkid_eur - (pricingData.kkid_discount || 0)
                  })}
                >
                  Inscrire mon enfant
                </Button>
                <p className="text-xs text-center mt-2">
                  <span className="text-red-600 font-bold">*</span> Option déplacement à domicile (frais en sus)
                </p>
                <p className="text-xs text-center text-gray-500 mt-2 md:mt-3">
                  🎈 Cours spécialement conçus pour les enfants
                </p>
              </div>
            </div>

            <div className="relative overflow-hidden rounded-2xl border-2 border-teal-200 bg-white/60 backdrop-blur-lg hover:shadow-xl transition-all min-w-[280px] sm:min-w-[320px] flex-shrink-0 snap-center">
              <div className="bg-gradient-to-br from-teal-50 to-teal-100 p-4 md:p-6">
                <h3 className="text-xl md:text-2xl font-bold text-teal-800">Pack K-Débutant</h3>
                <p className="text-sm md:text-base text-teal-600">Parfait pour commencer</p>
              </div>
              <div className="p-4 md:p-6">
                <div className="text-center mb-4 md:mb-6">
                  {pricingData.beginner_discount > 0 && (
                    <div className="text-gray-400 line-through text-lg md:text-xl">
                      {formatPrice(pricingData.beginner_eur, pricingData.beginner_fcfa)}
                    </div>
                  )}
                  <div className="text-2xl md:text-3xl font-bold text-teal-600">
                    {formatPriceWithSmallFCFA(
                      pricingData.beginner_eur - pricingData.beginner_discount,
                      (pricingData.beginner_fcfa || 0) - (pricingData.beginner_discount_fcfa || 0)
                    )}
                  </div>
                  {pricingData.beginner_discount > 0 && (
                    <div className="text-green-600 font-semibold mt-1 md:mt-2 text-sm md:text-base">
                      💰 Économisez {formatPrice(pricingData.beginner_discount, pricingData.beginner_discount_fcfa)}
                    </div>
                  )}
                </div>
                <ul className="space-y-2 md:space-y-3 text-sm md:text-base">
                  <li className="flex items-center gap-2">
                    <ChevronRight className="w-4 h-4 md:w-5 md:h-5 text-teal-600 flex-shrink-0" />
                    <span>Cours adaptés débutants</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <ChevronRight className="w-4 h-4 md:w-5 md:h-5 text-teal-600 flex-shrink-0" />
                    <span>Support pédagogique</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <ChevronRight className="w-4 h-4 md:w-5 md:h-5 text-teal-600 flex-shrink-0" />
                    <span>Accès bibliothèque</span>
                  </li>
                </ul>
                <Button 
                  className="w-full mt-4 md:mt-6 bg-teal-600 hover:bg-teal-700 text-sm md:text-base py-2 md:py-3" 
                  data-testid="pay-beginner"
                  onClick={() => openRegistrationModal({ 
                    name: 'Pack Débutant', 
                    level: 'beginner', 
                    price: pricingData.beginner_eur - pricingData.beginner_discount 
                  })}
                >
                  Payer maintenant
                </Button>
                <p className="text-xs text-center text-gray-500 mt-2 md:mt-3">
                  💳 Paiement sécurisé par Stripe (PCI Niveau 1)
                </p>
              </div>
            </div>

            <div className="relative overflow-hidden rounded-2xl border-2 border-teal-300 bg-white/60 backdrop-blur-lg hover:shadow-xl transition-all min-w-[280px] sm:min-w-[320px] flex-shrink-0 snap-center lg:transform lg:hover:scale-105">
              <div className="absolute top-3 md:top-4 right-3 md:right-4">
                <span className="bg-teal-600 text-white px-2 md:px-3 py-1 rounded-full text-xs md:text-sm font-semibold">Populaire</span>
              </div>
              <div className="bg-gradient-to-br from-teal-100 to-teal-200 p-4 md:p-6">
                <h3 className="text-xl md:text-2xl font-bold text-teal-800">Pack K-Intermédiaire</h3>
                <p className="text-sm md:text-base text-teal-700">Le plus choisi</p>
              </div>
              <div className="p-4 md:p-6">
                <div className="text-center mb-4 md:mb-6">
                  {pricingData.intermediate_discount > 0 && (
                    <div className="text-gray-400 line-through text-lg md:text-xl">
                      {formatPrice(pricingData.intermediate_eur, pricingData.intermediate_fcfa)}
                    </div>
                  )}
                  <div className="text-2xl md:text-3xl font-bold text-teal-600">
                    {formatPriceWithSmallFCFA(
                      pricingData.intermediate_eur - pricingData.intermediate_discount,
                      (pricingData.intermediate_fcfa || 0) - (pricingData.intermediate_discount_fcfa || 0)
                    )}
                  </div>
                  {pricingData.intermediate_discount > 0 && (
                    <div className="text-green-600 font-semibold mt-1 md:mt-2 text-sm md:text-base">
                      💰 Économisez {formatPrice(pricingData.intermediate_discount, pricingData.intermediate_discount_fcfa)}
                    </div>
                  )}
                </div>
                <ul className="space-y-2 md:space-y-3 text-sm md:text-base">
                  <li className="flex items-center gap-2">
                    <ChevronRight className="w-4 h-4 md:w-5 md:h-5 text-teal-600 flex-shrink-0" />
                    <span>Cours intermédiaires</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <ChevronRight className="w-4 h-4 md:w-5 md:h-5 text-teal-600 flex-shrink-0" />
                    <span>Pratique conversationnelle</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <ChevronRight className="w-4 h-4 md:w-5 md:h-5 text-teal-600 flex-shrink-0" />
                    <span>Exercices avancés</span>
                  </li>
                </ul>
                <Button 
                  className="w-full mt-4 md:mt-6 bg-teal-600 hover:bg-teal-700 text-sm md:text-base py-2 md:py-3" 
                  data-testid="pay-intermediate"
                  onClick={() => openRegistrationModal({ 
                    name: 'Pack Intermédiaire', 
                    level: 'intermediate', 
                    price: pricingData.intermediate_eur - pricingData.intermediate_discount 
                  })}
                >
                  Payer maintenant
                </Button>
                <p className="text-xs text-center text-gray-500 mt-2 md:mt-3">
                  💳 Paiement sécurisé par Stripe (PCI Niveau 1)
                </p>
              </div>
            </div>

            <div className="relative overflow-hidden rounded-2xl border-2 border-teal-200 bg-white/60 backdrop-blur-lg hover:shadow-xl transition-all w-[280px] sm:w-[320px] min-w-[280px] sm:min-w-[320px] max-w-[280px] sm:max-w-[320px] flex-shrink-0 snap-center">
              <div className="bg-gradient-to-br from-teal-50 to-teal-100 p-4 md:p-6">
                <h3 className="text-xl md:text-2xl font-bold text-teal-800">Pack K-Professionnel</h3>
                <p className="text-sm md:text-base text-teal-600">Formation d'anglais professionnel, intense ou accélérée</p>
              </div>
              <div className="p-4 md:p-6">
                <div className="text-center mb-4 md:mb-6">
                  {pricingData.advanced_discount > 0 && (
                    <div className="text-gray-400 line-through text-lg md:text-xl">
                      {formatPrice(pricingData.advanced_eur, pricingData.advanced_fcfa)}
                    </div>
                  )}
                  <div className="text-2xl md:text-3xl font-bold text-teal-600">
                    {formatPriceWithSmallFCFA(
                      pricingData.advanced_eur - pricingData.advanced_discount,
                      (pricingData.advanced_fcfa || 0) - (pricingData.advanced_discount_fcfa || 0)
                    )}
                  </div>
                  {pricingData.advanced_discount > 0 && (
                    <div className="text-green-600 font-semibold mt-1 md:mt-2 text-sm md:text-base">
                      💰 Économisez {formatPrice(pricingData.advanced_discount, pricingData.advanced_discount_fcfa)}
                    </div>
                  )}
                </div>
                <ul className="space-y-2 md:space-y-3 text-sm md:text-base">
                  <li className="flex items-center gap-2">
                    <ChevronRight className="w-4 h-4 md:w-5 md:h-5 text-teal-600 flex-shrink-0" />
                    <span>Contenu riche et intense</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <ChevronRight className="w-4 h-4 md:w-5 md:h-5 text-teal-600 flex-shrink-0" />
                    <span>Apprentissage rapide</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <ChevronRight className="w-4 h-4 md:w-5 md:h-5 text-teal-600 flex-shrink-0" />
                    <span>Efficacité garantie</span>
                  </li>
                </ul>
                <Button 
                  className="w-full mt-4 md:mt-6 bg-teal-600 hover:bg-teal-700 text-sm md:text-base py-2 md:py-3" 
                  data-testid="pay-advanced"
                  onClick={() => openRegistrationModal({ 
                    name: 'Pack professionnel', 
                    level: 'advanced', 
                    price: pricingData.advanced_eur - pricingData.advanced_discount 
                  })}
                >
                  Payer maintenant
                </Button>
                <p className="text-xs text-center text-gray-500 mt-2 md:mt-3">
                  💳 Paiement sécurisé par Stripe (PCI Niveau 1)
                </p>
              </div>
            </div>
            </div>
          </div>
          
          {/* Indicateur de scroll mobile */}
          <p className="text-center text-xs text-gray-500 mt-4 md:hidden">← Faites glisser pour voir plus →</p>
        </div>
      </section>

      {/* How It Works */}
      <HowItWorks />

      {/* CTA Button */}
      <section className="py-12 px-4 bg-white">
        <div className="container mx-auto max-w-7xl text-center">
          <button 
            onClick={() => openRegistrationModal()}
            className="inline-flex items-center px-8 py-4 bg-teal-600 text-white rounded-full font-semibold text-lg hover:bg-teal-700 transition duration-300 animate-bounce shadow-lg hover:shadow-xl"
            data-testid="cta-start-learning"
          >
            Commencer à apprendre
          </button>
        </div>
      </section>

      {/* Testimonials */}
      <Testimonials />

      {/* Test Section */}
      <section className="py-12 md:py-20 px-4 bg-gradient-to-b from-teal-50 to-white">
        <div className="container mx-auto max-w-7xl">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-center mb-3 md:mb-4">Évaluez votre niveau d'anglais</h2>
          <p className="text-center text-sm sm:text-base text-gray-600 mb-8 md:mb-12 px-4">Passez un test gratuit pour connaître votre niveau</p>

          <div className="flex md:grid md:grid-cols-3 gap-4 md:gap-8 overflow-x-auto snap-x snap-mandatory scrollbar-hide pb-4">
            <Card className="hover:shadow-xl transition-shadow border-teal-100 min-w-[280px] w-[280px] sm:min-w-0 sm:w-auto flex-shrink-0 snap-center">
              <CardHeader>
                <CardTitle className="text-teal-800">Test Débutant</CardTitle>
                <CardDescription>Parfait pour ceux qui débutent leur apprentissage</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">20 questions - 15 minutes</p>
                <Link to="/test/beginner">
                  <Button className="w-full bg-teal-600 hover:bg-teal-700" data-testid="test-beginner-button">
                    Commencer le test
                  </Button>
                </Link>
              </CardContent>
            </Card>

            <Card className="hover:shadow-xl transition-shadow border-teal-100 min-w-[280px] w-[280px] sm:min-w-0 sm:w-auto flex-shrink-0 snap-center">
              <CardHeader>
                <CardTitle className="text-teal-800">Test Intermédiaire</CardTitle>
                <CardDescription>Pour ceux qui ont une bonne base</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">20 questions - 20 minutes</p>
                <Link to="/test/intermediate">
                  <Button className="w-full bg-teal-600 hover:bg-teal-700" data-testid="test-intermediate-button">
                    Commencer le test
                  </Button>
                </Link>
              </CardContent>
            </Card>

            <Card className="hover:shadow-xl transition-shadow border-teal-100 min-w-[280px] w-[280px] sm:min-w-0 sm:w-auto flex-shrink-0 snap-center">
              <CardHeader>
                <CardTitle className="text-teal-800">Test professionnel</CardTitle>
                <CardDescription>Pour les utilisateurs expérimentés</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">20 questions - 25 minutes</p>
                <Link to="/test/advanced">
                  <Button className="w-full bg-teal-600 hover:bg-teal-700" data-testid="test-advanced-button">
                    Commencer le test
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Registration Modal */}
      <Dialog open={showRegistrationModal} onOpenChange={setShowRegistrationModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl text-teal-800">
              {selectedPlan ? `Inscription - ${selectedPlan.name}` : 'Rejoignez My KALAMA English'}
            </DialogTitle>
            <DialogDescription>
              {selectedPlan ? `Inscrivez-vous et payez ${formatPrice(selectedPlan.price)}` : 'Inscrivez-vous maintenant et commencez votre parcours d\'apprentissage'}
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
                {/* Type de cours */}
                <div className="bg-teal-50 p-4 rounded-lg">
                  <Label className="text-base font-semibold mb-2 block">Type de cours *</Label>
                  <div className="flex gap-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="courseType"
                        value="individual"
                        checked={courseType === 'individual'}
                        onChange={(e) => setCourseType(e.target.value)}
                        className="w-4 h-4 text-teal-600"
                      />
                      <span>Cours Individuel</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="courseType"
                        value="group"
                        checked={courseType === 'group'}
                        onChange={(e) => setCourseType(e.target.value)}
                        className="w-4 h-4 text-teal-600"
                      />
                      <span>Cours Groupé (max 3 personnes)</span>
                    </label>
                  </div>
                </div>

                {courseType === 'individual' ? (
                  /* Formulaire cours individuel */
                  <>
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="first_name">Prénom *</Label>
                        <Input
                          id="first_name"
                          required
                          value={formData.first_name}
                          onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                          className="border-gray-200"
                        />
                      </div>
                      <div>
                        <Label htmlFor="last_name">Nom *</Label>
                        <Input
                          id="last_name"
                          required
                          value={formData.last_name}
                          onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                          className="border-gray-200"
                        />
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="email">Email de contact *</Label>
                      <Input
                        id="email"
                        type="email"
                        required
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        className="border-gray-200"
                      />
                    </div>

                    <div>
                      <Label htmlFor="phone">Téléphone *</Label>
                      <div className="flex gap-2">
                        <Select
                          value={formData.country_code}
                          onValueChange={(value) => setFormData({ ...formData, country_code: value })}
                        >
                          <SelectTrigger className="w-[140px]">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="+33">🇫🇷 +33</SelectItem>
                            <SelectItem value="+221">🇸🇳 +221</SelectItem>
                            <SelectItem value="+1">🇺🇸 +1</SelectItem>
                          </SelectContent>
                        </Select>
                        <Input
                          id="phone"
                          required
                          value={formData.phone}
                          onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                          placeholder="6 12 34 56 78"
                          className="flex-1"
                        />
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="level">Niveau d'anglais *</Label>
                      <Select
                        value={formData.level}
                        onValueChange={(value) => setFormData({ ...formData, level: value })}
                      >
                        <SelectTrigger className="border-gray-200">
                          <SelectValue placeholder="Sélectionnez votre niveau" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="beginner">Débutant</SelectItem>
                          <SelectItem value="intermediate">Intermédiaire</SelectItem>
                          <SelectItem value="advanced">Pack professionnel</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </>
                ) : (
                  /* Formulaire cours groupé - personne principale + membres additionnels */
                  <>
                    <div className="bg-blue-50 p-4 rounded-lg border-2 border-blue-200">
                      <p className="text-sm text-gray-700">
                        <strong>📝 Inscription de groupe :</strong> Remplissez vos informations complètes, puis ajoutez les autres membres (nom et prénom uniquement).
                        L'admin générera un code de connexion partagé après validation.
                      </p>
                    </div>

                    <h3 className="font-semibold text-lg border-b pb-2 mt-6">Vos informations (personne principale)</h3>
                    
                    <div className="space-y-4 mt-4">
                      <div className="grid md:grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="first_name">Prénom *</Label>
                          <Input
                            id="first_name"
                            required
                            value={formData.first_name}
                            onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                            className="border-gray-200"
                          />
                        </div>
                        <div>
                          <Label htmlFor="last_name">Nom *</Label>
                          <Input
                            id="last_name"
                            required
                            value={formData.last_name}
                            onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                            className="border-gray-200"
                          />
                        </div>
                      </div>

                      <div>
                        <Label htmlFor="email">Email de contact *</Label>
                        <Input
                          id="email"
                          type="email"
                          required
                          value={formData.email}
                          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                          className="border-gray-200"
                        />
                      </div>

                      <div>
                        <Label htmlFor="phone">Téléphone *</Label>
                        <div className="flex gap-2">
                          <Select
                            value={formData.country_code}
                            onValueChange={(value) => setFormData({ ...formData, country_code: value })}
                          >
                            <SelectTrigger className="w-[140px]">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="+33">🇫🇷 +33</SelectItem>
                              <SelectItem value="+221">🇸🇳 +221</SelectItem>
                              <SelectItem value="+1">🇺🇸 +1</SelectItem>
                            </SelectContent>
                          </Select>
                          <Input
                            id="phone"
                            required
                            value={formData.phone}
                            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                            placeholder="6 12 34 56 78"
                            className="flex-1"
                          />
                        </div>
                      </div>

                      <div>
                        <Label htmlFor="level">Niveau d'anglais *</Label>
                        <Select
                          value={formData.level}
                          onValueChange={(value) => setFormData({ ...formData, level: value })}
                        >
                          <SelectTrigger className="border-gray-200">
                            <SelectValue placeholder="Sélectionnez votre niveau" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="beginner">Débutant</SelectItem>
                            <SelectItem value="intermediate">Intermédiaire</SelectItem>
                            <SelectItem value="advanced">Pack professionnel</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    {/* Section Membres Additionnels pour cours groupe */}
                    <div className="space-y-4 p-4 bg-gradient-to-br from-yellow-50 to-orange-50 rounded-xl border-2 border-yellow-200 mt-6">
                      <div className="flex justify-between items-center">
                        <div>
                          <h3 className="font-semibold text-lg text-gray-800">👥 Membres additionnels du groupe</h3>
                          <p className="text-sm text-gray-600">Ajoutez 1 à 2 personnes (nom et prénom uniquement)</p>
                        </div>
                        {additionalMembers.length < 2 && (
                          <Button
                            type="button"
                            onClick={() => setAdditionalMembers([...additionalMembers, { first_name: '', last_name: '' }])}
                            variant="outline"
                            className="border-orange-400 text-orange-600 hover:bg-orange-50"
                          >
                            <span className="text-lg mr-2">+</span> Ajouter une personne
                          </Button>
                        )}
                      </div>

                      {additionalMembers.length === 0 && (
                        <div className="text-center py-6 text-gray-500">
                          <p className="mb-2">Aucun membre additionnel</p>
                          <p className="text-sm">Cliquez sur "Ajouter une personne" pour commencer</p>
                        </div>
                      )}

                      {additionalMembers.map((member, index) => (
                        <div key={index} className="p-4 bg-white rounded-lg border-2 border-orange-200">
                          <div className="flex justify-between items-center mb-3">
                            <h4 className="font-semibold text-gray-800">Personne {index + 2}</h4>
                            <Button
                              type="button"
                              onClick={() => setAdditionalMembers(additionalMembers.filter((_, i) => i !== index))}
                              variant="ghost"
                              size="sm"
                              className="text-red-600 hover:bg-red-50"
                            >
                              ✕ Retirer
                            </Button>
                          </div>
                          <div className="grid md:grid-cols-2 gap-3">
                            <div>
                              <Label>Prénom *</Label>
                              <Input
                                value={member.first_name}
                                onChange={(e) => {
                                  const updated = [...additionalMembers];
                                  updated[index].first_name = e.target.value;
                                  setAdditionalMembers(updated);
                                }}
                                placeholder="Ex: Jean"
                                required
                                className="border-gray-200"
                              />
                            </div>
                            <div>
                              <Label>Nom *</Label>
                              <Input
                                value={member.last_name}
                                onChange={(e) => {
                                  const updated = [...additionalMembers];
                                  updated[index].last_name = e.target.value;
                                  setAdditionalMembers(updated);
                                }}
                                placeholder="Ex: Dupont"
                                required
                                className="border-gray-200"
                              />
                            </div>
                          </div>
                        </div>
                      ))}

                      {additionalMembers.length > 0 && (
                        <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                          <p className="text-sm text-gray-700">
                            <strong>ℹ️ Important :</strong> Après validation par l'admin, un code de connexion unique sera généré pour tout le groupe. Tous les membres utiliseront le même code pour se connecter.
                          </p>
                        </div>
                      )}
                    </div>
                  </>
                )}

                {/* Créneaux (facultatif) */}
                <div>
                  <Label className="flex items-center gap-2 mb-2">
                    <CalendarIcon className="w-4 h-4 text-teal-600" />
                    Créneaux préférés (facultatif)
                  </Label>
                  <Popover open={showCalendar} onOpenChange={setShowCalendar}>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-left font-normal"
                        type="button"
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {selectedDates.length > 0 ? `${selectedDates.length} date(s) sélectionnée(s)` : 'Choisir des créneaux'}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <div className="p-4">
                        <Calendar
                          mode="multiple"
                          selected={selectedDates.map(d => new Date(d))}
                          onSelect={(dates) => {
                            if (dates && dates.length > 0) {
                              const lastDate = dates[dates.length - 1];
                              handleDateSelect(lastDate);
                            }
                          }}
                          disabled={(date) => date < new Date()}
                          className="rounded-md border"
                        />
                        <Button
                          type="button"
                          onClick={() => setShowCalendar(false)}
                          className="w-full mt-4 bg-teal-600"
                        >
                          Confirmer
                        </Button>
                      </div>
                    </PopoverContent>
                  </Popover>
                </div>

                {/* Comment nous avez connus (facultatif) */}
                <div>
                  <Label>Comment avez-vous connu My KALAMA English ? (facultatif)</Label>
                  <Select
                    value={formData.referral_source}
                    onValueChange={(value) => setFormData({ ...formData, referral_source: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Sélectionnez" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="google">Google</SelectItem>
                      <SelectItem value="facebook">Facebook</SelectItem>
                      <SelectItem value="instagram">Instagram</SelectItem>
                      <SelectItem value="word_of_mouth">Bouche à oreille</SelectItem>
                      <SelectItem value="other">Autre</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* KALAMA CLUB Option - Mobile Optimized */}
                <div className="bg-gradient-to-r from-cyan-50 to-teal-50 p-3 sm:p-4 rounded-lg border-2 border-cyan-200">
                  <label 
                    className="flex items-start gap-2 sm:gap-3 cursor-pointer"
                    onClick={(e) => {
                      // Allow checkbox to be toggled by clicking anywhere on the label (mobile-friendly)
                      if (e.target.tagName !== 'INPUT') {
                        setFormData({ ...formData, join_kalama_club: !formData.join_kalama_club });
                      }
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={formData.join_kalama_club}
                      onChange={(e) => setFormData({ ...formData, join_kalama_club: e.target.checked })}
                      className="w-5 h-5 sm:w-6 sm:h-6 text-cyan-600 mt-0.5 flex-shrink-0 cursor-pointer"
                    />
                    <div className="flex-1 min-w-0">
                      <span className="font-semibold text-cyan-900 block text-sm sm:text-base">
                        ✨ Rejoindre le KALAMA CLUB
                      </span>
                      <span className="text-xs sm:text-sm text-cyan-700 block mt-1 leading-relaxed">
                        Accès au forum communautaire, événements exclusifs, classement et badge d'excellence !
                      </span>
                    </div>
                  </label>
                </div>

                {/* Code Promo Section - Fixed Display */}
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-4 rounded-lg border-2 border-green-200">
                  <Label className="font-semibold text-green-900 mb-3 block">
                    🎁 Code de réduction actif
                  </Label>
                  <div className="bg-white p-4 rounded-lg border-2 border-green-300 flex items-center justify-between">
                    <div className="flex-1">
                      <p className="text-xs text-gray-600 mb-1">Code promo</p>
                      <p className="text-2xl font-bold text-green-600 tracking-wider font-mono">KALAMA15</p>
                      <p className="text-sm text-green-700 mt-1">✅ 15% de réduction automatique</p>
                    </div>
                    <Button
                      type="button"
                      onClick={() => {
                        navigator.clipboard.writeText('KALAMA15');
                        toast.success('Code copié !');
                      }}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      Copier
                    </Button>
                  </div>
                  
                  {/* FCFA Discount Notice */}
                  {currency === 'FCFA' && (
                    <div className="mt-3 bg-blue-50 p-3 rounded-lg border border-blue-200">
                      <p className="text-sm text-blue-800 font-medium">
                        💰 Une remise de 10% est appliquée pour les paiements en FCFA
                      </p>
                    </div>
                  )}
                </div>

                <Button
                  type="submit"
                  className="w-full bg-teal-600 hover:bg-teal-700"
                  disabled={loading || (courseType === 'group' && !groupCodeInfo)}
                >
                  {loading ? 'Envoi en cours...' : courseType === 'group' ? 'Rejoindre le groupe' : 'Confirmer mon inscription'}
                </Button>

            <p className="text-sm text-gray-500 text-center">
              En vous inscrivant, vous acceptez nos conditions d'utilisation et notre politique de confidentialité.
            </p>
          </form>
        </DialogContent>
      </Dialog>

      {/* Payment Method Modal */}
      <Dialog open={showWavePaymentModal} onOpenChange={setShowWavePaymentModal}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl text-teal-800">
              ✅ Inscription réussie ! Choisissez votre mode de paiement
            </DialogTitle>
            <DialogDescription>
              Sélectionnez la méthode de paiement qui vous convient
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-6 mt-4">
            {/* Option 1: Stripe (Carte bancaire) */}
            <div 
              className={`border-2 rounded-lg p-6 cursor-pointer transition-all ${
                paymentMethod === 'stripe' ? 'border-teal-600 bg-teal-50' : 'border-gray-200 hover:border-teal-300'
              }`}
              onClick={() => setPaymentMethod('stripe')}
            >
              <div className="flex items-start gap-4">
                <input
                  type="radio"
                  name="paymentMethod"
                  value="stripe"
                  checked={paymentMethod === 'stripe'}
                  onChange={() => setPaymentMethod('stripe')}
                  className="mt-1 w-5 h-5 text-teal-600 cursor-pointer"
                />
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-teal-800 mb-2">
                    💳 Paiement par carte bancaire (Stripe)
                  </h3>
                  <p className="text-sm text-gray-600 mb-3">
                    Paiement sécurisé en ligne avec votre carte bancaire (Visa, Mastercard, etc.)
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded-full">
                      ✓ Instantané
                    </span>
                    <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded-full">
                      ✓ Sécurisé PCI Niveau 1
                    </span>
                    <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded-full">
                      ✓ International
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Option 2: Wave FCFA */}
            <div 
              className={`border-2 rounded-lg p-6 cursor-pointer transition-all ${
                paymentMethod === 'wave' ? 'border-teal-600 bg-teal-50' : 'border-gray-200 hover:border-teal-300'
              }`}
              onClick={() => setPaymentMethod('wave')}
            >
              <div className="flex items-start gap-4">
                <input
                  type="radio"
                  name="paymentMethod"
                  value="wave"
                  checked={paymentMethod === 'wave'}
                  onChange={() => setPaymentMethod('wave')}
                  className="mt-1 w-5 h-5 text-teal-600 cursor-pointer"
                />
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-teal-800 mb-2">
                    📱 Paiement Wave (FCFA - Sénégal)
                  </h3>
                  <p className="text-sm text-gray-600 mb-3">
                    Paiement mobile avec Wave pour le Sénégal et l'Afrique de l'Ouest
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <span className="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded-full">
                      🇸🇳 Sénégal
                    </span>
                    <span className="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded-full">
                      💰 FCFA
                    </span>
                    <span className="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded-full">
                      📱 Mobile Money
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Instructions pour Wave si sélectionné */}
            {paymentMethod === 'wave' && (
              <div className="bg-gradient-to-br from-blue-50 to-teal-50 border-2 border-teal-300 rounded-lg p-6 animate-in slide-in-from-top duration-300">
                <h4 className="text-lg font-bold text-teal-800 mb-4 flex items-center gap-2">
                  <span className="text-2xl">📋</span>
                  Instructions de paiement Wave Sénégal
                </h4>
                
                <div className="space-y-4">
                  <div className="bg-white rounded-lg p-4 shadow-sm">
                    <p className="text-sm font-semibold text-gray-700 mb-2">
                      💰 Montant à payer en FCFA : 
                      <span className="text-2xl text-teal-600 font-bold ml-2">
                        {selectedPlan ? `${Math.round(selectedPlan.price * EUR_TO_FCFA).toLocaleString('fr-FR')} FCFA` : ''}
                      </span>
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      (Équivalent à {selectedPlan ? formatPrice(selectedPlan.price) : ''})
                    </p>
                  </div>

                  <div className="bg-white rounded-lg p-4 shadow-sm">
                    <p className="text-sm font-semibold text-gray-700 mb-3">
                      👤 Bénéficiaire du transfert :
                    </p>
                    <div className="space-y-2">
                      <div className="flex items-center gap-3 bg-teal-50 p-3 rounded-md">
                        <div className="flex-1">
                          <p className="text-xs text-gray-600">Nom complet</p>
                          <p className="text-lg font-bold text-teal-800">Mouhamadou Mansour DIAGNE</p>
                        </div>
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-teal-600 text-teal-600 hover:bg-teal-600 hover:text-white"
                          onClick={() => {
                            navigator.clipboard.writeText('Mouhamadou Mansour DIAGNE');
                            toast.success('Nom copié !');
                          }}
                        >
                          Copier
                        </Button>
                      </div>
                      <div className="flex items-center gap-3 bg-blue-50 p-3 rounded-md">
                        <div className="flex-1">
                          <p className="text-xs text-gray-600">Numéro Wave</p>
                          <p className="text-lg font-bold text-blue-800">77 494 65 61</p>
                        </div>
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-blue-600 text-blue-600 hover:bg-blue-600 hover:text-white"
                          onClick={() => {
                            navigator.clipboard.writeText('77 494 65 61');
                            toast.success('Numéro copié !');
                          }}
                        >
                          Copier
                        </Button>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-4 shadow-sm">
                    <p className="text-sm font-semibold text-gray-700 mb-3">
                      📝 Étapes à suivre :
                    </p>
                    <ol className="space-y-3 text-sm text-gray-700">
                      <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-teal-600 text-white rounded-full flex items-center justify-center text-xs font-bold">1</span>
                        <span>Ouvrez votre application <strong>Wave</strong> sur votre téléphone</span>
                      </li>
                      <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-teal-600 text-white rounded-full flex items-center justify-center text-xs font-bold">2</span>
                        <span>Sélectionnez <strong>"Transfert"</strong></span>
                      </li>
                      <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-teal-600 text-white rounded-full flex items-center justify-center text-xs font-bold">3</span>
                        <span>Cliquez sur <strong>"Saisir un nouveau numéro"</strong></span>
                      </li>
                      <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-teal-600 text-white rounded-full flex items-center justify-center text-xs font-bold">4</span>
                        <span>Dans "Nom complet", entrez : <strong>Mouhamadou Mansour DIAGNE</strong></span>
                      </li>
                      <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-teal-600 text-white rounded-full flex items-center justify-center text-xs font-bold">5</span>
                        <span>Entrez le numéro : <strong>77 494 65 61</strong></span>
                      </li>
                      <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-teal-600 text-white rounded-full flex items-center justify-center text-xs font-bold">6</span>
                        <span>Entrez le montant : <strong>{selectedPlan ? `${Math.round(selectedPlan.price * EUR_TO_FCFA).toLocaleString('fr-FR')} FCFA` : ''}</strong></span>
                      </li>
                      <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-teal-600 text-white rounded-full flex items-center justify-center text-xs font-bold">7</span>
                        <span>Cliquez sur <strong>"Envoyer"</strong> pour finaliser le transfert</span>
                      </li>
                    </ol>
                  </div>

                  <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-lg">
                    <p className="text-sm text-yellow-800">
                      <strong>⚠️ Important :</strong> Votre compte sera activé dans les <strong>24 heures</strong> après vérification de votre paiement. Vous recevrez un email de confirmation.
                    </p>
                  </div>

                  <div className="bg-teal-50 border-l-4 border-teal-400 p-4 rounded-lg">
                    <p className="text-sm text-teal-800">
                      <strong>💡 Astuce :</strong> Prenez une capture d'écran de cette page ou notez ces informations pour faciliter votre paiement.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Boutons d'action */}
            <div className="space-y-3 pt-4">
              <div className="flex gap-3">
                {paymentMethod === 'stripe' ? (
                  <Button
                    className="flex-1 bg-teal-600 hover:bg-teal-700 text-lg py-6"
                    onClick={() => {
                      setShowWavePaymentModal(false);
                      if (selectedPlan) {
                        toast.info('Redirection vers Stripe...');
                        setTimeout(() => handleStripePayment(selectedPlan), 500);
                      }
                    }}
                  >
                    💳 Procéder au paiement Stripe
                  </Button>
                ) : (
                  <Button
                    className="flex-1 bg-teal-600 hover:bg-teal-700 text-lg py-6"
                    onClick={() => {
                      setShowWavePaymentModal(false);
                      toast.success('Instructions enregistrées ! Procédez au paiement Wave.', {
                        duration: 5000
                      });
                    }}
                  >
                    📱 J'ai compris, je vais payer via Wave
                  </Button>
                )}
              </div>
              
              <Button
                variant="outline"
                className="w-full border-2 border-gray-300 hover:border-teal-500 hover:bg-teal-50 text-gray-700 py-6 text-lg"
                onClick={() => {
                  setShowWavePaymentModal(false);
                  toast.info('Vous pourrez payer plus tard depuis votre espace étudiant.', {
                    duration: 5000
                  });
                }}
              >
                ⏰ Payer plus tard
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Success Modal with Shared Login Code */}
      <Dialog open={showSuccessModal} onOpenChange={setShowSuccessModal}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <div className="flex items-center justify-center mb-4">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-4xl">🎉</span>
              </div>
            </div>
            <DialogTitle className="text-center text-2xl font-bold text-green-800">
              Inscription Réussie !
            </DialogTitle>
            <DialogDescription className="text-center text-base">
              Votre compte de groupe a été créé avec succès
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-6 py-4">
            {/* Shared Login Code Display */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl border-2 border-blue-300">
              <div className="text-center mb-3">
                <p className="text-sm text-gray-700 font-semibold mb-2">🔑 Code de Connexion Partagé</p>
                <p className="text-xs text-gray-600 mb-3">
                  Partagez ce code avec les {numberOfStudents - 1} autre(s) membre(s) de votre groupe
                </p>
              </div>
              
              <div className="bg-white p-4 rounded-lg border-2 border-blue-400 mb-3">
                <p className="text-4xl font-bold text-center text-blue-600 tracking-widest font-mono">
                  {sharedLoginCode}
                </p>
              </div>
              
              <Button
                onClick={() => {
                  navigator.clipboard.writeText(sharedLoginCode || '');
                  toast.success('Code copié dans le presse-papiers !');
                }}
                variant="outline"
                className="w-full border-blue-400 text-blue-600 hover:bg-blue-50"
              >
                📋 Copier le code
              </Button>
            </div>
            
            {/* Instructions */}
            <div className="bg-yellow-50 p-4 rounded-lg border-2 border-yellow-200">
              <h4 className="font-semibold text-gray-800 mb-2">📌 Instructions importantes :</h4>
              <ul className="text-sm text-gray-700 space-y-2">
                <li className="flex items-start gap-2">
                  <span className="text-yellow-600 font-bold">1.</span>
                  <span>Conservez ce code en lieu sûr</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-yellow-600 font-bold">2.</span>
                  <span>Tous les membres du groupe utiliseront <strong>la même adresse email</strong> ({formData.email}) et <strong>ce code</strong> pour se connecter</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-yellow-600 font-bold">3.</span>
                  <span>Attendez l'approbation de l'administrateur avant de pouvoir vous connecter</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-yellow-600 font-bold">4.</span>
                  <span>Vous recevrez un email de confirmation à {formData.email}</span>
                </li>
              </ul>
            </div>
            
            {/* Group Info Summary */}
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <h4 className="font-semibold text-gray-800 mb-2">📋 Récapitulatif :</h4>
              <div className="text-sm text-gray-700 space-y-1">
                <p><strong>Groupe :</strong> {groupCodeInfo?.group_name}</p>
                <p><strong>Professeur :</strong> {groupCodeInfo?.teacher_name}</p>
                <p><strong>Nombre de personnes :</strong> {numberOfStudents}</p>
                <p><strong>Email de connexion :</strong> {formData.email}</p>
              </div>
            </div>
          </div>
          
          <div className="flex gap-3">
            <Button
              onClick={() => {
                setShowSuccessModal(false);
                setSharedLoginCode(null);
                // Reset form
                setFormData({
                  first_name: '',
                  last_name: '',
                  email: '',
                  phone: '',
                  country_code: '+33',
                  level: '',
                  preferred_slots: '',
                  referral_source: '',
                  join_kalama_club: false
                });
                setGroupCode('');
                setGroupCodeInfo(null);
                setNumberOfStudents(2);
              }}
              className="flex-1 bg-blue-600 hover:bg-blue-700"
            >
              J'ai compris
            </Button>
          </div>
        </DialogContent>
      </Dialog>


      {/* Footer */}
      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12 md:py-16 px-4">
        <div className="container mx-auto max-w-7xl">
          <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-6 md:gap-8 mb-8 md:mb-12">
            {/* À propos */}
            <div>
              <div className="mb-4">
                <h3 className="text-xl font-bold text-teal-400">My KALAMA</h3>
                <span className="text-sm text-gray-500 uppercase tracking-wide">English</span>
              </div>
              <p className="text-gray-400">
                Plateforme d'apprentissage de l'anglais en ligne adaptée à tous les niveaux.
              </p>
            </div>
            
            {/* Liens rapides */}
            <div>
              <h4 className="text-lg font-semibold mb-4 text-teal-400">Liens rapides</h4>
              <ul className="space-y-2">
                <li><a href="#" onClick={(e) => { e.preventDefault(); window.scrollTo({top: 0, behavior: 'smooth'}); }} className="text-gray-400 hover:text-teal-400 transition cursor-pointer">Accueil</a></li>
                <li><Link to="/login" className="text-gray-400 hover:text-teal-400 transition">Connexion</Link></li>
                <li><a href="#" onClick={(e) => { e.preventDefault(); openRegistrationModal(); }} className="text-gray-400 hover:text-teal-400 transition cursor-pointer">Inscription</a></li>
              </ul>
            </div>
            
            {/* Contact */}
            <div>
              <h4 className="text-lg font-semibold mb-4 text-teal-400">Contactez-nous</h4>
              <form onSubmit={handleContactSubmit} className="space-y-4">
                <Input
                  type="text"
                  placeholder="Votre nom"
                  value={contactForm.name}
                  onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
                  required
                  className="bg-gray-800 border-gray-700 text-white"
                />
                <Input
                  type="email"
                  placeholder="Votre email"
                  value={contactForm.email}
                  onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
                  required
                  className="bg-gray-800 border-gray-700 text-white"
                />
                <Textarea
                  placeholder="Votre message"
                  value={contactForm.message}
                  onChange={(e) => setContactForm({ ...contactForm, message: e.target.value })}
                  required
                  className="bg-gray-800 border-gray-700 text-white"
                  rows={4}
                />
                <Button type="submit" className="w-full bg-teal-600 hover:bg-teal-700" disabled={sendingContact}>
                  {sendingContact ? 'Envoi...' : 'Envoyer'}
                </Button>
              </form>
            </div>
            
            {/* Réseaux sociaux */}
            <div>
              <h4 className="text-lg font-semibold mb-4 text-teal-400">Suivez-nous</h4>
              <div className="flex gap-4 mb-6">
                <a href="#" className="w-10 h-10 bg-teal-600 rounded-full flex items-center justify-center hover:bg-teal-700 transition">
                  <span className="sr-only">Facebook</span>
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M9 8h-3v4h3v12h5v-12h3.642l.358-4h-4v-1.667c0-.955.192-1.333 1.115-1.333h2.885v-5h-3.808c-3.596 0-5.192 1.583-5.192 4.615v3.385z"/></svg>
                </a>
                <a href="https://www.instagram.com/mykalamaenglish/" target="_blank" rel="noopener noreferrer" className="w-10 h-10 bg-teal-600 rounded-full flex items-center justify-center hover:bg-teal-700 transition">
                  <span className="sr-only">Instagram</span>
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073z"/><path d="M12 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
                </a>
                <a href="#" className="w-10 h-10 bg-teal-600 rounded-full flex items-center justify-center hover:bg-teal-700 transition">
                  <span className="sr-only">LinkedIn</span>
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M4.98 3.5c0 1.381-1.11 2.5-2.48 2.5s-2.48-1.119-2.48-2.5c0-1.38 1.11-2.5 2.48-2.5s2.48 1.12 2.48 2.5zm.02 4.5h-5v16h5v-16zm7.982 0h-4.968v16h4.969v-8.399c0-4.67 6.029-5.052 6.029 0v8.399h4.988v-10.131c0-7.88-8.922-7.593-11.018-3.714v-2.155z"/></svg>
                </a>
                <a href="#" className="w-10 h-10 bg-yellow-400 rounded-full flex items-center justify-center hover:bg-yellow-500 transition">
                  <span className="sr-only">Snapchat</span>
                  <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M12.206.793c.99 0 4.347.276 5.93 3.821.529 1.193.403 3.219.299 4.847l-.003.06c-.012.18-.022.345-.03.51.075.045.203.09.401.09.3-.016.659-.12 1.033-.301.165-.088.344-.104.464-.104.182 0 .359.029.509.09.45.149.734.479.734.838 0 .179-.09.36-.255.495-.12.104-.329.208-.539.208-.209 0-.375-.074-.539-.149-.12-.074-.24-.134-.389-.134-.104 0-.209.03-.329.074l-.135.06c-.254.119-.574.239-.929.239-.225 0-.434-.045-.614-.134-.209-.104-.419-.179-.614-.209l-.076-.016c-.044-.015-.074-.015-.104-.015 0 .09-.045.181-.09.27l-.9 1.35c-.165.254-.375.509-.704.509h-.06c-.195 0-.404-.074-.584-.194-.181-.119-.301-.314-.301-.509l.06-1.02c0-.105.044-.226.119-.346.074-.105.149-.21.254-.285l.226-.165c.209-.135.419-.27.584-.404.209-.165.344-.285.449-.375.029-.029.044-.074.044-.119 0-.074-.029-.12-.089-.12h-.135c-.21.029-.42.104-.629.254-.195.135-.405.27-.629.33-.136.044-.27.074-.42.074-.449 0-.854-.21-1.168-.569-.21-.24-.375-.524-.449-.838-.09-.345-.135-.704-.135-1.05v-.015c0-.405.09-.794.239-1.168.195-.479.524-.898.914-1.198.405-.314.869-.509 1.378-.509z"/></svg>
                </a>
              </div>
              
              {/* Donation Button */}
              <div className="mt-4">
                <h5 className="text-sm font-semibold mb-2 text-gray-300">Soutenez-nous</h5>
                <DonationButton size="sm" className="w-full" />
                <p className="text-xs text-gray-500 mt-2">Aidez notre communauté à grandir</p>
              </div>
            </div>
          </div>
          
          <div className="border-t border-gray-800 pt-8">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
              <p className="text-gray-500">© 2025 My KALAMA English. Tous droits réservés.</p>
              <div className="flex gap-6">
                <Link to="/cgu" className="text-gray-400 hover:text-teal-400 transition">CGU</Link>
                <Link to="/privacy" className="text-gray-400 hover:text-teal-400 transition">Politique de confidentialité</Link>
                <Link to="/legal" className="text-gray-400 hover:text-teal-400 transition">Mentions légales</Link>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
