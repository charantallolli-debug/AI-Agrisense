import React, { useState } from 'react';
import { HelpCircle, ChevronDown, ChevronUp, Mail, Phone, MapPin, Send, BookOpen, MessageSquare } from 'lucide-react';

const ARTICLES = [
  {
    title: 'Managing Wheat Rust in Rabi Season',
    description: 'Yellow and Brown Rust can destroy up to 80% of wheat crops. Learn the early symptoms and how temperature influences their spread.',
    symptoms: 'Linear yellow/orange pustules on leaves that rub off as dust on fingers.',
    control: 'Spray Propiconazole 25% EC at 0.1% concentration when first spots are noticed.',
    tag: 'Wheat',
  },
  {
    title: 'Late Blight in Potato & Tomato',
    description: 'Favored by cool, wet weather, late blight is caused by Phytophthora infestans and spreads rapidly via wind-borne spores.',
    symptoms: 'Water-soaked dark lesions on leaves with white fungal growth on undersides during humid mornings.',
    control: 'Apply Copper Oxychloride 50% WP or Mancozeb 75% WP. Avoid overhead sprinkler irrigation.',
    tag: 'Solanaceae',
  },
  {
    title: 'Eco-friendly Neem Oil Spray Guide',
    description: 'Neem oil is a powerful organic pesticide that disrupts the lifecycle of sucking pests like aphids, thrips, and whiteflies.',
    symptoms: 'Leaf curling, sticky honeydew residues, or visual insect clusters on young shoots.',
    control: 'Mix 5ml Neem Oil + 1ml liquid soap per 1 liter of warm water. Spray during evening hours.',
    tag: 'Organic',
  },
];

const FAQS = [
  {
    question: 'How does the AgriSense AI detect crop diseases?',
    answer: 'AgriSense uses a two-stage deep learning pipeline based on the EfficientNet architecture. Stage 1 identifies the crop type and screens out invalid images (non-crops, hands, background). Stage 2 evaluates the crop leaf and matches it against trained disease classes using crop-conditioning to maximize classification accuracy.',
  },
  {
    question: 'What image quality is needed for a scan?',
    answer: 'For best results, upload a clear, close-up photo of a single leaf showing symptoms. Avoid shadows, high glare, background clutter, or scanning multiple different leaves at once. Our built-in leaf detection system will automatically alert you if the leaf quality is insufficient.',
  },
  {
    question: 'How does the Live Weather widget help?',
    answer: 'Different crop pathogens (fungi, bacteria) thrive under specific ranges of temperature and relative humidity. For example, high humidity (>90%) with cool temperatures triggers Late Blight. AgriSense live weather analysis warns you when environmental conditions are prime for disease outbreaks so you can apply preventative sprays.',
  },
  {
    question: 'Is my personal scan history stored online?',
    answer: 'No. To protect your privacy and ensure offline capabilities, your scan logs and analytics are stored directly on your browser using local storage. No farm coordinates or photo uploads are permanently stored on our backend servers.',
  },
];

export default function InfoHub() {
  const [openFaq, setOpenFaq] = useState(null);
  const [formSubmitted, setFormSubmitted] = useState(false);
  const [formState, setFormState] = useState({ name: '', email: '', crop: '', msg: '' });

  const toggleFaq = (idx) => {
    setOpenFaq(openFaq === idx ? null : idx);
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    if (formState.name && formState.email && formState.msg) {
      setFormSubmitted(true);
      setTimeout(() => {
        setFormSubmitted(false);
        setFormState({ name: '', email: '', crop: '', msg: '' });
      }, 5000);
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 space-y-16">
      {/* 1. Disease Awareness Articles */}
      <section className="space-y-6">
        <div>
          <h2 className="font-serif text-2xl font-bold text-slate-900 mb-2 flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-primary-600" />
            Disease Awareness Library
          </h2>
          <p className="text-sm text-slate-500">Expert-verified articles on common crop infections, prevention methods, and natural remedies.</p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {ARTICLES.map((art) => (
            <div key={art.title} className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between hover:shadow-md transition-all">
              <div className="space-y-3">
                <span className="text-[10px] font-extrabold text-primary-700 bg-primary-50 px-2.5 py-1 rounded-full uppercase tracking-wider">
                  {art.tag}
                </span>
                <h3 className="font-serif text-lg font-bold text-slate-900 leading-snug">{art.title}</h3>
                <p className="text-xs text-slate-500 leading-relaxed">{art.description}</p>
                
                <div className="border-t border-slate-100 pt-3 space-y-2 text-xs">
                  <p className="text-slate-700"><strong className="text-slate-900">Symptoms:</strong> {art.symptoms}</p>
                  <p className="text-slate-700"><strong className="text-slate-900">Control:</strong> {art.control}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 2. Accordion FAQs */}
      <section className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1 space-y-2">
          <h2 className="font-serif text-2xl font-bold text-slate-900 flex items-center gap-2">
            <HelpCircle className="w-6 h-6 text-primary-600" />
            Frequently Asked Questions
          </h2>
          <p className="text-sm text-slate-500">Find quick answers to common questions about AgriSense diagnostic models and operations.</p>
        </div>

        <div className="lg:col-span-2 space-y-3">
          {FAQS.map((faq, idx) => {
            const isOpen = openFaq === idx;
            return (
              <div key={idx} className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm transition-all duration-200">
                <button
                  onClick={() => toggleFaq(idx)}
                  className="w-full flex items-center justify-between px-5 py-4 text-left font-bold text-slate-800 hover:bg-slate-50 text-sm sm:text-base transition-colors"
                  style={{ minHeight: '48px' }}
                >
                  <span>{faq.question}</span>
                  {isOpen ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                </button>
                
                {isOpen && (
                  <div className="px-5 pb-5 pt-1 text-sm text-slate-500 border-t border-slate-100/50 leading-relaxed font-medium">
                    {faq.answer}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* 3. Contact and Support Section */}
      <section className="bg-slate-900 text-white rounded-3xl overflow-hidden shadow-xl grid md:grid-cols-5">
        <div className="md:col-span-2 p-8 sm:p-10 bg-slate-950/40 flex flex-col justify-between space-y-8">
          <div>
            <h2 className="font-serif text-2xl font-extrabold text-white flex items-center gap-2">
              <MessageSquare className="w-6 h-6 text-primary-400" />
              Contact & Support
            </h2>
            <p className="text-sm text-slate-400 mt-2">Need assistance with your scans or customized agronomic recommendations? Reach out to our agricultural helpline.</p>
          </div>

          <div className="space-y-4 text-sm text-slate-300">
            <div className="flex items-center gap-3">
              <Phone className="w-5 h-5 text-primary-400 shrink-0" />
              <span>+91 1800 123 4567 (Farmer Helpline)</span>
            </div>
            <div className="flex items-center gap-3">
              <Mail className="w-5 h-5 text-primary-400 shrink-0" />
              <span>support@agrisense.gov.in</span>
            </div>
            <div className="flex items-center gap-3">
              <MapPin className="w-5 h-5 text-primary-400 shrink-0" />
              <span>ICAR Research Complex, Pusa, New Delhi</span>
            </div>
          </div>

          <p className="text-[10px] text-slate-500">Helpline available Mon-Sat, 9:00 AM to 6:00 PM IST.</p>
        </div>

        {/* Contact Form */}
        <div className="md:col-span-3 p-8 sm:p-10 bg-white text-slate-800">
          {formSubmitted ? (
            <div className="h-full flex flex-col items-center justify-center text-center space-y-3 py-8">
              <span className="text-4xl">🎉</span>
              <p className="font-serif text-xl font-bold text-primary-800">Feedback Submitted!</p>
              <p className="text-sm text-slate-500 max-w-[280px]">Thank you for your message. Our agronomists will review and reach out shortly.</p>
            </div>
          ) : (
            <form onSubmit={handleFormSubmit} className="space-y-4">
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="name" className="text-xs font-bold text-slate-500 uppercase">Your Name</label>
                  <input
                    type="text"
                    id="name"
                    required
                    value={formState.name}
                    onChange={(e) => setFormState({ ...formState, name: e.target.value })}
                    className="px-4 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 bg-slate-50/50"
                  />
                </div>
                
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="email" className="text-xs font-bold text-slate-500 uppercase">Email Address</label>
                  <input
                    type="email"
                    id="email"
                    required
                    value={formState.email}
                    onChange={(e) => setFormState({ ...formState, email: e.target.value })}
                    className="px-4 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 bg-slate-50/50"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="crop" className="text-xs font-bold text-slate-500 uppercase">Crop Type (Optional)</label>
                <input
                  type="text"
                  id="crop"
                  value={formState.crop}
                  onChange={(e) => setFormState({ ...formState, crop: e.target.value })}
                  placeholder="e.g. Wheat, Tomato"
                  className="px-4 py-2 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 bg-slate-50/50"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label htmlFor="msg" className="text-xs font-bold text-slate-500 uppercase">Message</label>
                <textarea
                  id="msg"
                  required
                  rows={4}
                  value={formState.msg}
                  onChange={(e) => setFormState({ ...formState, msg: e.target.value })}
                  placeholder="Ask a question or describe your farm symptoms..."
                  className="px-4 py-2.5 text-sm rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 bg-slate-50/50 resize-none"
                />
              </div>

              <button
                type="submit"
                className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-full bg-slate-900 hover:bg-slate-800 text-white text-sm font-bold transition-all shadow-md"
                style={{ minHeight: '44px' }}
              >
                <Send className="w-4 h-4" />
                Send Message
              </button>
            </form>
          )}
        </div>
      </section>
    </div>
  );
}
