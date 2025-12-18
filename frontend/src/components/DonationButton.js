import React from 'react';
import { Button } from './ui/button';
import { Heart } from 'lucide-react';

const DonationButton = ({ variant = 'default', size = 'default', className = '' }) => {
  const handleDonation = () => {
    // Open Stripe donation link in new tab
    window.open('https://buy.stripe.com/5kQeVdbDR1937RB3lWenS09', '_blank');
  };

  return (
    <Button
      onClick={handleDonation}
      variant={variant}
      size={size}
      className={`bg-gradient-to-r from-pink-500 to-red-500 hover:from-pink-600 hover:to-red-600 text-white font-semibold shadow-lg transition-all duration-300 hover:shadow-xl ${className}`}
    >
      <Heart className="w-4 h-4 mr-2 fill-current" />
      Faire un don (1€)
    </Button>
  );
};

export default DonationButton;
