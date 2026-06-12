import React from 'react';
import { Camera, ShieldCheck, HeartPulse, BarChart, CloudSun, MessagesSquare } from 'lucide-react';
import heroImage from '../assets/hero_agriculture_banner.png';

export default function Hero({ onStartScan, onSwitchTab }) {
  const features = [
    {
      name: 'AI Disease Detection',
      description: 'Upload a leaf photo to diagnose crop diseases within seconds with over 90% confidence.',
      icon: Camera,
      color: 'bg-primary-50 text-primary-700 ring-primary-600/10',
    },
    {
      name: 'Integrated Treatments',
      description: 'Get immediate chemical, organic, and prevention measures to protect your crop yield.',
      icon: ShieldCheck,
      color: 'bg-emerald-50 text-emerald-700 ring-emerald-600/10',
    },
    {
      name: 'Farmer AI Assistant',
      description: 'Chat with our AI chatbot to ask specific crop care questions or clarify diagnosis details.',
      icon: MessagesSquare,
      color: 'bg-indigo-50 text-indigo-700 ring-indigo-600/10',
    },
    {
      name: 'Analytics & History',
      description: 'Track your local scan history and review charts on most common diseases in your farm.',
      icon: BarChart,
      color: 'bg-amber-50 text-amber-700 ring-amber-600/10',
    },
    {
      name: 'Live Weather Tips',
      description: 'View real-time local weather forecasts paired with daily agronomic farming tips.',
      icon: CloudSun,
      color: 'bg-sky-50 text-sky-700 ring-sky-600/10',
    },
    {
      name: 'Crop Health Monitoring',
      description: 'Keep your farm healthy with regular leaf scouting tips, severity scales, and alerts.',
      icon: HeartPulse,
      color: 'bg-rose-50 text-rose-700 ring-rose-600/10',
    },
  ];

  return (
    <div className="relative isolate overflow-hidden bg-white">
      {/* Hero section */}
      <div className="relative px-6 pt-10 pb-20 lg:px-8 bg-slate-900 overflow-hidden">
        {/* Background Image with Overlay */}
        <div className="absolute inset-0 z-0 opacity-40 mix-blend-multiply filter brightness-75">
          <img
            src={heroImage}
            alt="Agri-Tech Field Banner"
            className="h-full w-full object-cover object-center"
          />
        </div>
        
        {/* Background subtle gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-900/60 to-transparent z-0"></div>

        <div className="relative mx-auto max-w-4xl text-center z-10 py-12 sm:py-20">
          <span className="inline-flex items-center rounded-full bg-primary-500/10 px-3 py-1 text-sm font-semibold leading-6 text-primary-400 ring-1 ring-inset ring-primary-500/20 mb-6">
            🌾 Modern Smart Farming
          </span>
          <h2 className="font-serif text-4xl font-extrabold tracking-tight text-white sm:text-6xl">
            AI-Powered Crop Disease Detection for Smart Farming
          </h2>
          <p className="mt-6 text-lg leading-8 text-slate-300 max-w-2xl mx-auto">
            Scan leaf images to instantly diagnose plant diseases, access expert treatment recommendations, monitor weather parameters, and chat with our farmer assistant.
          </p>
          <div className="mt-10 flex items-center justify-center gap-x-6">
            <button
              onClick={onStartScan}
              className="rounded-full bg-primary-600 px-8 py-4 text-base font-bold text-white shadow-lg shadow-primary-700/30 hover:bg-primary-500 hover:scale-105 transition-all duration-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
            >
              🔬 Start Crop Scan
            </button>
            <button
              onClick={() => onSwitchTab('weather')}
              className="text-sm font-bold leading-6 text-white hover:text-primary-300 transition-colors flex items-center gap-1"
            >
              Check Weather Tips <span aria-hidden="true">→</span>
            </button>
          </div>
        </div>
      </div>

      {/* Features section */}
      <div className="mx-auto max-w-7xl px-6 py-24 sm:py-32 lg:px-8">
        <div className="mx-auto max-w-2xl lg:text-center">
          <h3 className="font-serif text-base font-bold leading-7 text-primary-600">Smart Farming Tools</h3>
          <p className="mt-2 font-serif text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Everything you need to protect your harvest
          </p>
          <p className="mt-6 text-lg leading-8 text-slate-600">
            AgriSense combines state-of-the-art computer vision models with real-time agronomic weather advice to help Indian farmers protect their crops from pests and disease.
          </p>
        </div>
        <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
          <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
            {features.map((feature) => (
              <div key={feature.name} className="flex flex-col bg-white border border-slate-100 p-8 rounded-3xl shadow-sm hover:shadow-md transition-all duration-200">
                <dt className="flex items-center gap-x-3 text-base font-bold leading-7 text-slate-900">
                  <div className={`p-2.5 rounded-2xl ring-1 ${feature.color}`}>
                    <feature.icon className="h-6 w-6" aria-hidden="true" />
                  </div>
                  {feature.name}
                </dt>
                <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-slate-600">
                  <p className="flex-auto">{feature.description}</p>
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </div>
  );
}
