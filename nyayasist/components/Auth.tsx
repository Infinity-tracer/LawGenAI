
import React, { useState } from 'react';
import { LawIcon } from './Icons';
import { registerUser, loginUser } from '../utils/apiService';

interface AuthProps {
  onSuccess: (userData: any) => void;
  onBack: () => void;
}

const Auth: React.FC<AuthProps> = ({ onSuccess, onBack }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    otp: ''
  });
  const [errors, setErrors] = useState<string[]>([]);
  const [otpSent, setOtpSent] = useState(false);
  const [otpMessage, setOtpMessage] = useState('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const validateSignup = () => {
    const newErrors: string[] = [];

    if (!/^[a-zA-Z\s]+$/.test(formData.fullName)) {
      newErrors.push("Name must contain only alphabets and spaces.");
    }

    if (!formData.email.includes('@')) {
      newErrors.push("Email must be valid (contain @).");
    }

    if (!/^\d{10}$/.test(formData.phone)) {
      newErrors.push("Phone number must be exactly 10 digits.");
    }

    if (formData.password.length < 8) {
      newErrors.push("Password must be at least 8 characters.");
    }
    if (!/[A-Z]/.test(formData.password)) {
      newErrors.push("Password must contain at least one uppercase letter.");
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(formData.password)) {
      newErrors.push("Password must contain at least one special character.");
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.push("Passwords do not match.");
    }

    return newErrors;
  };

  const handleSendOtp = async () => {
    const validationErrors = validateSignup();
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsLoading(true);
    setErrors([]);

    try {
      const response = await import('../utils/apiService').then(m => m.sendVerificationOTP(formData.email));
      if (response.success) {
        setOtpSent(true);
        setOtpMessage('Verification code sent to your email.');
      }
    } catch (error: any) {
      setErrors([error.message || 'Failed to send verification code.']);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors([]);
    setIsLoading(true);

    try {
      if (isLogin) {
        // Call API for login
        const response = await loginUser({
          email: formData.email,
          password: formData.password
        });

        if (response.success) {
          // Store user in localStorage for session persistence
          const userData = {
            user_uuid: response.user_uuid,
            fullName: response.full_name,
            email: response.email
          };
          localStorage.setItem('currentUser', JSON.stringify(userData));
          onSuccess(userData);
        }
      } else {
        // Registration Flow
        if (!otpSent) {
          // Send OTP First
          await handleSendOtp();
          return;
        }

        // Verify OTP and Register
        if (!formData.otp || formData.otp.length !== 6) {
          setErrors(['Please enter the 6-digit verification code sent to your email.']);
          setIsLoading(false);
          return;
        }

        // Call API for registration
        const response = await registerUser({
          full_name: formData.fullName,
          email: formData.email,
          phone: formData.phone,
          password: formData.password,
          otp: formData.otp
        });

        if (response.success) {
          // Store user in localStorage for session persistence
          const userData = {
            user_uuid: response.user_uuid,
            fullName: response.full_name,
            email: response.email
          };
          localStorage.setItem('currentUser', JSON.stringify(userData));
          onSuccess(userData);
        }
      }
    } catch (error: any) {
      setErrors([error.message || 'An error occurred. Please try again.']);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0b0d0c] p-6 relative">
      {/* College Logo - Top Left Corner */}
      <div className="absolute top-4 left-4 z-50">
        <div className="border-2 border-[#d4af37] p-0.5">
          <img
            src="/college-logo.png"
            alt="College Logo"
            className="h-14 w-14 object-contain"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.style.display = 'none';
            }}
          />
        </div>
      </div>

      <div className="w-full max-w-md">
        <div className="text-center mb-10">
          <div className="flex justify-center mb-4 text-[#d4af37]">
            <LawIcon className="w-14 h-14" />
          </div>
          <h2 className="text-4xl font-bold tracking-tight mb-2 serif">NYAYASIST</h2>
          <p className="text-[#d4af37] tracking-[0.3em] uppercase text-[10px] font-medium">Authored for Justice</p>
        </div>

        <div className="bg-[#1a1c1b] border border-[#3d2b1f] p-8 shadow-2xl">
          <h3 className="text-2xl mb-8 serif text-[#f5f5f5]">
            {isLogin ? 'Counsel Login' : 'Register for Access'}
          </h3>

          <form onSubmit={handleSubmit} className="space-y-6">
            {!isLogin && (
              <>
                <div>
                  <label className="block text-xs uppercase tracking-widest text-[#d4af37] mb-2 font-semibold">Full Name</label>
                  <input
                    type="text"
                    name="fullName"
                    value={formData.fullName}
                    onChange={handleInputChange}
                    className="w-full bg-[#0b0d0c] border border-[#3d2b1f] text-[#f5f5f5] p-3 outline-none focus:border-[#d4af37] font-light"
                    placeholder="Advocate Name"
                    disabled={otpSent}
                  />
                </div>
                <div>
                  <label className="block text-xs uppercase tracking-widest text-[#d4af37] mb-2 font-semibold">Phone Number</label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleInputChange}
                    className="w-full bg-[#0b0d0c] border border-[#3d2b1f] text-[#f5f5f5] p-3 outline-none focus:border-[#d4af37] font-light"
                    placeholder="10 Digits"
                    disabled={otpSent}
                  />
                </div>
              </>
            )}

            <div>
              <label className="block text-xs uppercase tracking-widest text-[#d4af37] mb-2 font-semibold">Email Address</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                className="w-full bg-[#0b0d0c] border border-[#3d2b1f] text-[#f5f5f5] p-3 outline-none focus:border-[#d4af37] font-light"
                placeholder="email@court.gov.in"
                disabled={otpSent || (isLogin && isLoading)}
              />
            </div>

            <div>
              <label className="block text-xs uppercase tracking-widest text-[#d4af37] mb-2 font-semibold">Password</label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                className="w-full bg-[#0b0d0c] border border-[#3d2b1f] text-[#f5f5f5] p-3 outline-none focus:border-[#d4af37] font-light"
                placeholder="********"
                disabled={otpSent || (isLogin && isLoading)}
              />
            </div>

            {!isLogin && !otpSent && (
              <div>
                <label className="block text-xs uppercase tracking-widest text-[#d4af37] mb-2 font-semibold">Confirm Password</label>
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  className="w-full bg-[#0b0d0c] border border-[#3d2b1f] text-[#f5f5f5] p-3 outline-none focus:border-[#d4af37] font-light"
                  placeholder="********"
                />
              </div>
            )}

            {otpSent && !isLogin && (
              <div className="animate-pulse-once">
                <div className="bg-green-900/20 border-l-4 border-green-500 p-4 mb-4">
                  <p className="text-green-400 text-xs">{otpMessage}</p>
                </div>
                <label className="block text-xs uppercase tracking-widest text-[#d4af37] mb-2 font-semibold">Verification Code</label>
                <input
                  type="text"
                  name="otp"
                  value={formData.otp}
                  onChange={handleInputChange}
                  className="w-full bg-[#0b0d0c] border border-[#3d2b1f] text-[#f5f5f5] p-3 outline-none focus:border-[#d4af37] font-light text-center tracking-[0.5em] text-xl"
                  placeholder="------"
                  maxLength={6}
                />
              </div>
            )}

            {errors.length > 0 && (
              <div className="bg-red-900/20 border-l-4 border-red-500 p-4">
                <ul className="list-disc list-inside text-red-400 text-sm space-y-1">
                  {errors.map((err, i) => (
                    <li key={i}>{err}</li>
                  ))}
                </ul>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-[#3d2b1f] border border-[#d4af37] text-[#f5f5f5] py-4 text-sm tracking-[0.3em] font-bold hover:bg-[#4d3b2f] uppercase transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'PROCESSING...' : (isLogin ? 'ENTER CHAMBERS' : (otpSent ? 'VERIFY & ACCESS' : 'SEND CODE'))}
            </button>
          </form>

          <div className="mt-8 pt-8 border-t border-[#3d2b1f] text-center">
            <button
              onClick={() => {
                setIsLogin(!isLogin);
                setErrors([]);
              }}
              className="text-[#d4af37] text-sm hover:underline font-light"
            >
              {isLogin ? "No access? Register here" : "Already registered? Login here"}
            </button>
          </div>
        </div>

        <button
          onClick={onBack}
          className="mt-8 text-[#f5f5f5] opacity-30 text-xs w-full hover:opacity-100 tracking-[0.2em] uppercase transition-opacity"
        >
          ← Return to Home
        </button>
      </div>
    </div>
  );
};

export default Auth;
