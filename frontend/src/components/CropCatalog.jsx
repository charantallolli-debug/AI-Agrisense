import React from 'react';
import { BookOpen, AlertCircle, ArrowUpRight } from 'lucide-react';

// Friendly descriptions or categories for common crops
const CROP_METADATA = {
  Rice: { category: 'Cereal', origin: 'Kharif', details: 'Requires clayey/loamy soil and heavy rainfall/irrigation.' },
  Wheat: { category: 'Cereal', origin: 'Rabi', details: 'Thrives in cool climates with moderate rainfall.' },
  Maize: { category: 'Cereal', origin: 'Kharif/Rabi', details: 'Needs well-drained fertile soils and warm weather.' },
  Corn: { category: 'Cereal', origin: 'Kharif/Rabi', details: 'Alias of Maize. Highly responsive to nitrogen fertilizers.' },
  Tomato: { category: 'Vegetable', origin: 'Horticulture', details: 'Prefers well-drained, sandy loam soils rich in organic matter.' },
  Potato: { category: 'Tuber', origin: 'Rabi', details: 'Needs cool nights and loose, acidic soil to form large tubers.' },
  Onion: { category: 'Allium', origin: 'Rabi', details: 'Requires shallow cultivation and frequent weed control.' },
  Chilli: { category: 'Spice', origin: 'Kharif/Summer', details: 'Demands warm, humid weather and highly porous soil.' },
  Chili: { category: 'Spice', origin: 'Kharif/Summer', details: 'Alias of Chilli. Susceptible to waterlogging.' },
  Capsicum: { category: 'Vegetable', origin: 'Horticulture', details: 'Grown in greenhouses or shade nets. Needs warm soil.' },
  Cabbage: { category: 'Cruciferous', origin: 'Rabi', details: 'Requires heavy fertilization and consistent soil moisture.' },
  Cauliflower: { category: 'Cruciferous', origin: 'Rabi', details: 'Demands fertile soil and high humidity during curd initiation.' },
  Cucumber: { category: 'Cucurbit', origin: 'Zaid/Summer', details: 'Vining crop. Needs treppising and sandy loam soils.' },
  'Bottle Gourd': { category: 'Cucurbit', origin: 'Zaid/Summer', details: 'Grown for edible gourds. Needs trellis and full sun.' },
  Pea: { category: 'Legume', origin: 'Rabi', details: 'Nitrogen-fixing legume. Requires cool weather and staking.' },
  Cotton: { category: 'Fiber', origin: 'Kharif', details: 'Requires high temperatures, moderate rainfall, and deep soil.' },
  Sugarcane: { category: 'Cash Crop', origin: 'Perennial', details: 'Demands high temperatures, heavy rainfall, and loamy soils.' },
  Brinjal: { category: 'Vegetable', origin: 'Horticulture', details: 'Prefers well-drained sandy loam soil and full sun.' },
  Groundnut: { category: 'Oilseed', origin: 'Kharif', details: 'Thrives in loose sandy soils to allow pods to penetrate.' },
  Soybean: { category: 'Oilseed', origin: 'Kharif', details: 'High protein crop. Thrives in neutral soils.' },
  Mango: { category: 'Fruit', origin: 'Perennial', details: 'Grows in well-drained alluvial or laterite soils.' },
  Banana: { category: 'Fruit', origin: 'Perennial', details: 'Requires rich, acidic soil and high humidity.' },
  Grapes: { category: 'Fruit', origin: 'Horticulture', details: 'Requires pruning and dry sunny climates during ripening.' },
  Apple: { category: 'Fruit', origin: 'Temperate', details: 'Needs high altitudes, chilling hours, and well-drained soil.' },
  Pomegranate: { category: 'Fruit', origin: 'Arid', details: 'Drought-tolerant. Thrives in light loamy soils.' },
  Coconut: { category: 'Plantation', origin: 'Coastal', details: 'Grows in sandy soils. Requires tropical humid climates.' },
  Turmeric: { category: 'Spice', origin: 'Kharif', details: 'Requires hot, humid climate and well-drained clayey soils.' },
  Ginger: { category: 'Spice', origin: 'Kharif', details: 'Needs partial shade, rich humus soil, and warm weather.' },
  Pulses: { category: 'Legume', origin: 'Various', details: 'Dryland crop. Improves soil fertility via nitrogen fixation.' },
  Millets: { category: 'Cereal', origin: 'Kharif', details: 'Climate-resilient superfood. Grows in poor sandy soils.' },
  Mustard: { category: 'Oilseed', origin: 'Rabi', details: 'Requires cool temperatures and light loam soils.' },
  Sunflower: { category: 'Oilseed', origin: 'Zaid/Summer', details: 'Demands deep, fertile soils and full solar exposure.' },
};

export default function CropCatalog({ info }) {
  const modelCrops = info?.model_crops || [
    'Rice', 'Wheat', 'Maize', 'Tomato', 'Potato', 'Onion', 
    'Chilli', 'Cabbage', 'Cauliflower', 'Cucumber', 'Bottle Gourd', 'Pea'
  ];

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 space-y-8">
      {/* Catalog Header */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-sm">
        <h2 className="font-serif text-2xl font-bold text-slate-900 mb-2 flex items-center gap-2">
          <BookOpen className="w-6 h-6 text-primary-600" />
          Supported Crops
        </h2>
        <p className="text-sm text-slate-500">List of crops currently supported by the AgriSense AI classification model. Scan these crops for accurate diagnostics.</p>
        
        {info?.roadmap_note && (
          <div className="mt-4 flex items-start gap-2.5 bg-primary-50 text-primary-800 text-xs px-4 py-3 rounded-xl border border-primary-100">
            <AlertCircle className="w-4.5 h-4.5 text-primary-600 shrink-0 mt-0.5" />
            <p className="font-medium">{info.roadmap_note}</p>
          </div>
        )}
      </div>

      {/* Model Parameters Badge list */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
        {modelCrops.map((crop) => {
          const meta = CROP_METADATA[crop] || { category: 'Crop', origin: 'Indian', details: 'Supported by AgriSense diagnostics.' };
          return (
            <div 
              key={crop}
              className="bg-white border border-slate-200 p-5 rounded-2xl shadow-sm hover:shadow-md hover:border-primary-300 hover:scale-[1.01] transition-all duration-200 flex flex-col justify-between space-y-3"
            >
              <div>
                <div className="flex justify-between items-start">
                  <span className="text-xs font-bold text-slate-400 bg-slate-100 px-2 py-0.5 rounded-md">
                    {meta.category}
                  </span>
                  {meta.origin !== 'Various' && (
                    <span className="text-[10px] font-extrabold text-primary-700 bg-primary-50 px-2 py-0.5 rounded-full">
                      {meta.origin}
                    </span>
                  )}
                </div>
                <h3 className="font-serif text-lg font-bold text-slate-900 mt-2">{crop}</h3>
                <p className="text-xs text-slate-500 leading-relaxed mt-1">{meta.details}</p>
              </div>
              
              <div className="flex items-center text-xs font-bold text-primary-600 gap-0.5 pt-2 cursor-pointer group">
                Scan {crop}
                <ArrowUpRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </div>
            </div>
          );
        })}
      </div>
      
      {info?.architecture && (
        <p className="text-center text-xs text-slate-400 font-semibold uppercase tracking-wider">
          Active Backbone: {info.architecture} · Outputs: {info.model_class_count || 62} Classes
        </p>
      )}
    </div>
  );
}
