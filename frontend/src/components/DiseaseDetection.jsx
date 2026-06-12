import React, { useState, useRef, useEffect } from 'react';
import { Camera, Upload, AlertCircle, Scan } from 'lucide-react';

export default function DiseaseDetection({ onAnalyze, isLoading, errorMsg, clearError }) {
  const [previewUrl, setPreviewUrl] = useState(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [statusHint, setStatusHint] = useState('Step 1: Upload an image or start the camera, then analyze.');
  const [canAnalyze, setCanAnalyze] = useState(false);
  
  const videoRef = useRef(null);
  const fileInputRef = useRef(null);
  const streamRef = useRef(null);

  // Stop camera stream on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const startCamera = async () => {
    try {
      stopCamera();
      setStatusHint('Starting camera...');
      clearError();

      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
      });
      
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.hidden = false;
      }
      setPreviewUrl(null);
      setCameraActive(true);
      setCanAnalyze(false);
      setStatusHint('Step 2: Capture a clear photo of the leaf, then Analyze.');
    } catch (err) {
      console.error('Camera access error:', err);
      setCameraActive(false);
      setStatusHint('Camera not available. Please allow permissions or select Upload instead.');
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
      videoRef.current.hidden = true;
    }
    setCameraActive(false);
  };

  const capturePhoto = () => {
    if (!cameraActive || !videoRef.current) return;
    
    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
    setPreviewUrl(dataUrl);
    stopCamera();
    setCanAnalyze(true);
    setStatusHint('Photo captured! Tap "Analyze Leaf" below to scan.', true);
  };

  const handleFileChange = (e) => {
    const file = e.target.files && e.target.files[0];
    if (file) loadFile(file);
  };

  const loadFile = (file) => {
    if (!file.type.startsWith('image/')) {
      alert('Please choose a valid image file.');
      return;
    }
    clearError();
    const reader = new FileReader();
    reader.onload = () => {
      stopCamera();
      setPreviewUrl(reader.result);
      setCanAnalyze(true);
      setStatusHint('Image loaded! Tap "Analyze Leaf" below to scan.', true);
    };
    reader.onerror = () => {
      setStatusHint('Error loading image file.', false);
    };
    reader.readAsDataURL(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files && e.dataTransfer.files[0];
    if (file) loadFile(file);
  };

  const triggerAnalyze = () => {
    if (!previewUrl) return;
    onAnalyze(previewUrl);
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-sm">
        <h2 className="font-serif text-2xl font-bold text-slate-900 mb-2">Analyze Crop Leaf</h2>
        <p className="text-sm text-slate-500 mb-6">Upload or capture a close-up, well-lit photo of a single crop leaf showing symptoms.</p>
        
        {/* Error Alert Box */}
        {errorMsg && (
          <div className="mb-6 flex items-start gap-3 rounded-2xl bg-rose-50 p-4 ring-1 ring-rose-200 text-rose-800 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0 text-rose-500" />
            <div className="flex-1">
              <p className="font-bold">Scan Error</p>
              <p className="mt-1">{errorMsg}</p>
            </div>
            <button onClick={clearError} className="font-semibold text-rose-600 hover:text-rose-900">Dismiss</button>
          </div>
        )}

        {/* Upload/Preview Zone */}
        <div 
          onClick={() => !cameraActive && fileInputRef.current?.click()}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative flex flex-col items-center justify-center min-h-[300px] border-2 border-dashed rounded-2xl overflow-hidden cursor-pointer transition-all duration-300 ${
            cameraActive ? 'border-primary-500 ring-2 ring-primary-100' :
            isDragOver ? 'border-primary-500 bg-primary-50/30 ring-2 ring-primary-100 animate-pulse-border' :
            previewUrl ? 'border-slate-200' : 'border-slate-300 hover:border-primary-400 hover:bg-slate-50/50'
          }`}
        >
          {/* Active Camera Video Feed */}
          <video 
            ref={videoRef} 
            autoplay 
            playsinline 
            muted 
            hidden
            className="w-full max-h-[400px] object-cover bg-black"
          />

          {/* Captured Image Preview */}
          {previewUrl && (
            <img 
              src={previewUrl} 
              alt="Leaf Preview" 
              className="w-full max-h-[400px] object-contain bg-slate-50"
            />
          )}

          {/* Empty Placeholder */}
          {!cameraActive && !previewUrl && (
            <div className="flex flex-col items-center p-6 text-center">
              <div className="p-4 rounded-full bg-primary-50 text-primary-600 mb-4 ring-1 ring-primary-100">
                <Upload className="w-8 h-8" />
              </div>
              <p className="font-bold text-slate-700 text-base mb-1">Drag & drop your leaf photo</p>
              <p className="text-xs text-slate-400 mb-3">Supports JPG, PNG, WebP up to 10MB</p>
              <span className="text-sm font-semibold text-primary-600 hover:text-primary-800">or browse files</span>
            </div>
          )}

          {/* AI Scan Overlay */}
          {isLoading && (
            <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-[2px] flex flex-col items-center justify-center text-white z-10 transition-opacity">
              <div className="relative">
                <Scan className="w-16 h-16 text-primary-400 animate-pulse" />
                <div className="absolute top-0 bottom-0 left-0 right-0 border-t-2 border-primary-400 animate-[bounce_2s_infinite]"></div>
              </div>
              <p className="mt-4 font-serif text-lg font-bold">AI Model Analyzing Leaf...</p>
              <p className="text-xs text-slate-300 mt-1">Filtering non-crops & checking severity</p>
            </div>
          )}
        </div>

        {/* Input Control Element */}
        <input 
          ref={fileInputRef}
          type="file" 
          id="file-upload" 
          accept="image/*"
          className="hidden" 
          onChange={handleFileChange}
        />

        {/* Actions Button Panel */}
        <div className="mt-6 flex flex-col gap-4">
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={startCamera}
              className={`flex-1 flex items-center justify-center gap-2 px-5 py-3 rounded-full text-sm font-bold border transition-all duration-200 ${
                cameraActive 
                  ? 'bg-slate-100 border-slate-300 text-slate-700' 
                  : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-50'
              }`}
              style={{ minHeight: '48px' }}
            >
              <Camera className="w-4 h-4" />
              📸 Camera
            </button>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="flex-1 flex items-center justify-center gap-2 px-5 py-3 rounded-full text-sm font-bold border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 transition-all"
              style={{ minHeight: '48px' }}
            >
              <Upload className="w-4 h-4" />
              📁 Upload
            </button>
            <button
              type="button"
              onClick={capturePhoto}
              disabled={!cameraActive}
              className={`flex-1 flex items-center justify-center gap-2 px-5 py-3 rounded-full text-sm font-bold border transition-all ${
                cameraActive 
                  ? 'bg-primary-600 border-primary-600 text-white shadow-md shadow-primary-200 hover:bg-primary-500' 
                  : 'bg-slate-100 border-slate-200 text-slate-400 cursor-not-allowed'
              }`}
              style={{ minHeight: '48px' }}
            >
              Capture
            </button>
          </div>

          <button
            type="button"
            onClick={triggerAnalyze}
            disabled={!canAnalyze || isLoading}
            className={`w-full flex items-center justify-center gap-2 px-6 py-4 rounded-full text-base font-bold transition-all duration-200 ${
              canAnalyze && !isLoading
                ? 'bg-accent-500 text-slate-900 shadow-md shadow-accent-200 hover:bg-accent-400 hover:scale-[1.01]'
                : 'bg-slate-100 text-slate-400 cursor-not-allowed'
            }`}
            style={{ minHeight: '52px' }}
          >
            🔬 Analyze Leaf
          </button>
          
          <p className="text-center text-xs text-slate-400 mt-2 font-medium">{statusHint}</p>
        </div>
      </div>
    </div>
  );
}
