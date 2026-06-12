import React from 'react';
import { AlertTriangle, CheckCircle2, ShieldAlert, Sparkles, TrendingUp } from 'lucide-react';

const HARM_BADGES = {
  Low: 'bg-green-50 text-green-700 ring-green-600/10 border border-green-200',
  Medium: 'bg-yellow-50 text-yellow-700 ring-yellow-600/10 border border-yellow-200',
  High: 'bg-orange-50 text-orange-700 ring-orange-600/10 border border-orange-200',
  Critical: 'bg-red-50 text-red-700 ring-red-600/10 border border-red-200',
};

const HARM_BAR_COLORS = {
  Low: 'bg-green-500',
  Medium: 'bg-yellow-500',
  High: 'bg-orange-500',
  Critical: 'bg-red-500',
};

export default function PredictionDashboard({ result, onFetchLlmPlan, llmPlanLoading, llmPlanContent }) {
  if (!result || result.status !== 'success') return null;

  const isHealthy = result.is_healthy;
  const severity = result.severity_percent ?? 0;
  const harmColorClass = HARM_BADGES[result.harmfulness] || HARM_BADGES.Medium;
  const barColorClass = HARM_BAR_COLORS[result.harmfulness] || HARM_BAR_COLORS.Medium;

  return (
    <div className="mx-auto max-w-3xl px-4 pb-12">
      <div className="bg-white border border-slate-200 rounded-3xl overflow-hidden shadow-sm">
        {/* Results Header Card */}
        <div className={`p-6 sm:p-8 text-white ${isHealthy ? 'bg-gradient-to-br from-primary-600 to-emerald-700' : 'bg-gradient-to-br from-slate-900 via-slate-800 to-primary-950'}`}>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-bold tracking-widest uppercase bg-white/10 px-2.5 py-1 rounded-full">Diagnosis Result</span>
            {result.pipeline === 'two_stage' && (
              <span className="text-xs font-semibold bg-primary-500/30 px-2 py-0.5 rounded-full text-primary-200">2-Stage AI Pipeline</span>
            )}
          </div>
          
          <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
            <div>
              <p className="text-sm text-slate-300 font-semibold mb-1">Crop: <span className="text-white text-base font-bold">{result.crop}</span></p>
              <h3 className="font-serif text-2xl sm:text-3xl font-extrabold">{result.prediction || result.message}</h3>
            </div>
            <div className="shrink-0 text-left sm:text-right mt-2 sm:mt-0">
              <span className="text-2xl sm:text-3xl font-black">{result.confidence}%</span>
              <p className="text-[10px] text-slate-300 tracking-wider font-semibold uppercase">Confidence Score</p>
            </div>
          </div>
        </div>

        {/* Warning Indicator */}
        {result.confidence_warning && (
          <div className="flex items-center gap-3 bg-amber-50 px-6 py-4 border-b border-amber-100 text-amber-800 text-sm">
            <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0" />
            <p className="font-medium">
              Moderate confidence ({result.confidence}%). Consider scanning a closer, clearer photo of a single leaf under brighter lighting.
            </p>
          </div>
        )}

        <div className="p-6 sm:p-8 space-y-8">
          {/* Severity & Impact Dashboard */}
          {!isHealthy && (
            <div className="bg-slate-50 border border-slate-100 p-6 rounded-2xl">
              <h4 className="font-serif text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-primary-600" />
                Disease Severity & Impact
              </h4>
              
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between text-sm font-bold text-slate-700 mb-1.5">
                    <span>Severity Meter</span>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${harmColorClass}`}>
                      {result.harmfulness} Risk
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                    <div 
                      className={`h-full rounded-full transition-all duration-500 ${barColorClass}`}
                      style={{ width: `${severity}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[10px] text-slate-400 font-semibold mt-1">
                    <span>0% (Mild)</span>
                    <span>{severity}% Severity</span>
                    <span>100% (Severe)</span>
                  </div>
                </div>

                <div className="border-t border-slate-200 pt-4">
                  <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Impact Analysis</p>
                  <p className="text-sm text-slate-700 leading-relaxed font-medium">{result.impact}</p>
                </div>
              </div>
            </div>
          )}

          {/* Model Reasoning Explainer */}
          {result.explanation && (
            <div className="space-y-4">
              <div className="border-b border-slate-100 pb-2">
                <h4 className="font-serif text-lg font-bold text-slate-900 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-accent-500" />
                  Model Explanation & Diagnostics
                </h4>
              </div>
              <p className="text-sm text-slate-600 leading-relaxed">{result.explanation.summary}</p>
              
              <div className="grid md:grid-cols-2 gap-6 pt-2">
                {/* Diagnostics Pipeline steps */}
                <div>
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Model Analysis Steps</p>
                  <ul className="space-y-2">
                    {(result.explanation.reasoning || []).map((step, idx) => (
                      <li key={idx} className="flex gap-2.5 text-sm text-slate-600">
                        <span className="text-xs font-bold bg-slate-100 text-slate-500 w-5 h-5 flex items-center justify-center rounded-full shrink-0 mt-0.5">{idx + 1}</span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Alternate Top Matches */}
                {result.explanation.top_predictions && result.explanation.top_predictions.length > 0 && (
                  <div>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Top Alternative Matches</p>
                    <div className="space-y-2">
                      {result.explanation.top_predictions.map((match, idx) => (
                        <div key={idx} className="flex items-center justify-between text-sm bg-slate-50 border border-slate-100 px-4 py-2 rounded-xl">
                          <span className="font-medium text-slate-700 flex items-center gap-2">
                            <span className="text-xs font-bold text-slate-400">#{idx + 1}</span>
                            {match.label}
                          </span>
                          <span className="font-bold text-slate-500 text-xs bg-slate-200/50 px-2 py-0.5 rounded-md">{match.confidence}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Solution Database Segment */}
          {result.solution && (
            <div className="border-t border-slate-100 pt-6 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h4 className="font-serif text-lg font-bold text-slate-900">Recommended Treatment Plan</h4>
                  <p className="text-xs text-slate-400 font-semibold uppercase mt-0.5">Primary database solution</p>
                </div>
                
                {/* LLM Advisory Treatment Action */}
                {!isHealthy && (
                  <button
                    onClick={onFetchLlmPlan}
                    disabled={llmPlanLoading}
                    className="flex items-center gap-1.5 px-5 py-2.5 rounded-full bg-primary-600 hover:bg-primary-500 disabled:bg-slate-100 text-white disabled:text-slate-400 text-sm font-bold transition-all shadow-sm"
                    style={{ minHeight: '40px' }}
                  >
                    <Sparkles className="w-4 h-4" />
                    {llmPlanLoading ? 'Generating Plan...' : '✨ Get AI Treatment Plan'}
                  </button>
                )}
              </div>

              {/* LLM Plan Panel */}
              {llmPlanContent && (
                <div className="bg-gradient-to-br from-primary-50 to-primary-100/50 border border-primary-200 p-6 rounded-2xl space-y-3">
                  <div className="flex items-center gap-1.5 text-primary-800 font-bold text-sm">
                    <Sparkles className="w-4 h-4 text-primary-600" />
                    Interactive AI Advice:
                  </div>
                  <pre className="text-xs text-slate-700 leading-relaxed font-sans whitespace-pre-wrap overflow-x-auto bg-white/70 border border-primary-100 p-4 rounded-xl max-h-[400px]">
                    {llmPlanContent}
                  </pre>
                  <p className="text-[10px] text-slate-400 italic">Plan generated combining diagnosis weather state and crop profiles.</p>
                </div>
              )}

              {/* Standard Database Solutions Layout */}
              <div className="grid md:grid-cols-2 gap-6 pt-2">
                {/* Left Solutions Column */}
                <div className="space-y-6">
                  {result.solution.cause && (
                    <div className="space-y-1">
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Cause / Pathogen</span>
                      <p className="text-sm text-slate-700 leading-relaxed font-medium bg-slate-50/50 border border-slate-100 p-3.5 rounded-xl">{result.solution.cause}</p>
                    </div>
                  )}

                  {result.solution.symptoms && result.solution.symptoms.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Visual Symptoms</span>
                      <ul className="list-disc pl-5 text-sm text-slate-600 space-y-1 font-medium">
                        {result.solution.symptoms.map((item, idx) => <li key={idx}>{item}</li>)}
                      </ul>
                    </div>
                  )}

                  {result.solution.prevention && result.solution.prevention.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Preventive Measures</span>
                      <ul className="list-disc pl-5 text-sm text-slate-600 space-y-1 font-medium">
                        {result.solution.prevention.map((item, idx) => <li key={idx}>{item}</li>)}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Right Solutions Column */}
                <div className="space-y-6">
                  {result.solution.pesticides && result.solution.pesticides.length > 0 && (
                    <div className="space-y-2">
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Chemical Pesticides / Fungicides</span>
                      <div className="space-y-1.5">
                        {result.solution.pesticides.map((item, idx) => (
                          <div key={idx} className="flex gap-2 text-sm text-slate-700 bg-rose-50/50 border border-rose-100/50 px-3.5 py-2.5 rounded-xl">
                            <span className="text-rose-500 font-bold shrink-0 mt-0.5">•</span>
                            <span className="font-semibold text-slate-800">{item}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {result.solution.organic_solutions && result.solution.organic_solutions.length > 0 && (
                    <div className="space-y-2">
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Organic / Biological Treatments</span>
                      <div className="space-y-1.5">
                        {result.solution.organic_solutions.map((item, idx) => (
                          <div key={idx} className="flex gap-2 text-sm text-slate-700 bg-emerald-50/50 border border-emerald-100/50 px-3.5 py-2.5 rounded-xl">
                            <span className="text-emerald-500 font-bold shrink-0 mt-0.5">•</span>
                            <span className="font-semibold text-slate-800">{item}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {result.solution.recommended_actions && result.solution.recommended_actions.length > 0 && (
                    <div className="space-y-1.5">
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Immediate Actions (Dos & Don'ts)</span>
                      <div className="space-y-1.5">
                        {result.solution.recommended_actions.map((item, idx) => (
                          <div key={idx} className="text-xs leading-relaxed font-semibold bg-amber-50/50 border border-amber-100/50 text-slate-700 px-3.5 py-2.5 rounded-xl">
                            {item}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
