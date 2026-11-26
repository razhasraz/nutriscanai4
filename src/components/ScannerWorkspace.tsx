import React, { useEffect, useRef, useState } from 'react';
import {
  AlertCircle,
  ArrowRight,
  Camera,
  Check,
  ImageUp,
  Loader2,
  Plus,
  RefreshCw,
  ScanLine,
  Trash2,
  VideoOff,
} from 'lucide-react';
import {
  CANONICAL_FOOD_CLASSES,
  PortionUnit,
  QUICK_MEAL_PRESETS,
} from '../data/nutritionData';
import {
  DetectionCertainty,
  PlateItemDraft,
  convertToGrams,
  getAvailableUnits,
  getDefaultPortion,
} from '../engine/nutritionEngine';

const HERO_IMAGE_SRC = '/src/assets/images/hero_indian_thali_1795712773089.jpg';

interface ApiDetection {
  matchedCanonicalFood: string;
  rawLabel: string;
  certainty: DetectionCertainty;
  needsVerification: boolean;
  suggestedQuantity: number;
  visualNote: string;
  box2d: [number, number, number, number] | null;
}

interface DetectFoodResponse {
  suggestedMealLabel: string;
  plateSummary: string;
  detections: ApiDetection[];
  error?: string;
}

interface ScannerWorkspaceProps {
  plateItems: PlateItemDraft[];
  onChangePlateItems: React.Dispatch<React.SetStateAction<PlateItemDraft[]>>;
  mealLabel: string;
  onChangeMealLabel: (val: string) => void;
  onAnalyzeMeal: () => void;
  onExploreDatabase: () => void;
  scannerSectionRef: React.RefObject<HTMLDivElement | null>;
}

const uid = () => Math.random().toString(36).slice(2, 10);

/**
 * Downscales any image data URL or image element to a clean JPEG (max 1024px)
 * so AI vision scanning stays fast on mobile networks and well within upload limits.
 */
async function compressImageSourceToJpegBase64(
  imageSrc: string
): Promise<{ base64: string; mimeType: 'image/jpeg'; previewUrl: string }> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      const maxDim = 1024;
      let width = img.naturalWidth || img.width;
      let height = img.naturalHeight || img.height;
      if (width > maxDim || height > maxDim) {
        const scale = maxDim / Math.max(width, height);
        width = Math.round(width * scale);
        height = Math.round(height * scale);
      }
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        reject(new Error('Unable to prepare image canvas.'));
        return;
      }
      ctx.drawImage(img, 0, 0, width, height);
      const dataUrl = canvas.toDataURL('image/jpeg', 0.86);
      const base64 = dataUrl.split(',')[1] || '';
      resolve({ base64, mimeType: 'image/jpeg', previewUrl: dataUrl });
    };
    img.onerror = () => reject(new Error('Could not decode the selected image.'));
    img.src = imageSrc;
  });
}

export const ScannerWorkspace: React.FC<ScannerWorkspaceProps> = ({
  plateItems,
  onChangePlateItems,
  mealLabel,
  onChangeMealLabel,
  onAnalyzeMeal,
  onExploreDatabase,
  scannerSectionRef,
}) => {
  const [inputMode, setInputMode] = useState<'camera' | 'upload'>('camera');
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [capturedImageUrl, setCapturedImageUrl] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [heroImgFailed, setHeroImgFailed] = useState(false);

  // Live AI vision detection states
  const [isScanning, setIsScanning] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);
  const [plateSummary, setPlateSummary] = useState<string | null>(null);
  const [hoveredUid, setHoveredUid] = useState<string | null>(null);

  // Manual add state
  const [manualFood, setManualFood] = useState<string>('Roti / Chapati');
  const [customFoodMode, setCustomFoodMode] = useState(false);
  const [customFoodName, setCustomFoodName] = useState('');
  const [manualQty, setManualQty] = useState<number>(2);
  const [manualUnit, setManualUnit] = useState<PortionUnit>('Pieces');

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
  };

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const runAiFoodScan = async (imageSrc: string) => {
    setIsScanning(true);
    setScanError(null);
    setPlateSummary(null);

    try {
      const { base64, mimeType, previewUrl } = await compressImageSourceToJpegBase64(imageSrc);
      setCapturedImageUrl(previewUrl);

      const response = await fetch('/api/detect-food', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ imageBase64: base64, mimeType }),
      });

      const data = (await response.json()) as DetectFoodResponse;
      if (!response.ok) {
        throw new Error(
          data.error || 'Unable to scan this image right now. Please try again shortly.'
        );
      }

      setPlateSummary(data.plateSummary || null);
      if (data.suggestedMealLabel) {
        onChangeMealLabel(data.suggestedMealLabel);
      }

      if (!data.detections || data.detections.length === 0) {
        onChangePlateItems([]);
        setScanError(
          data.plateSummary ||
            'No distinct food items were detected in this photograph. Try better lighting or add items manually on the right.'
        );
        return;
      }

      const detectedDrafts: PlateItemDraft[] = data.detections.map((det) => {
        const isMatched = Boolean(det.matchedCanonicalFood);
        const foodName = isMatched ? det.matchedCanonicalFood : det.rawLabel;
        const defPortion = isMatched
          ? getDefaultPortion(foodName)
          : { quantity: det.suggestedQuantity || 1, unit: 'Servings' as PortionUnit };

        const suggestedQty =
          det.suggestedQuantity > 0 ? det.suggestedQuantity : defPortion.quantity;
        const needsVerify = det.needsVerification || !isMatched;

        return {
          uid: uid(),
          foodName,
          originalAiLabel: det.rawLabel || foodName,
          confidence: null,
          detectionCertainty: det.certainty,
          visualNote: det.visualNote,
          box2d: det.box2d,
          isUncertain: needsVerify,
          quantity: suggestedQty,
          unit: defPortion.unit,
          portionSource: 'Estimated default',
          verificationStatus: needsVerify
            ? 'Uncertain — requires verification'
            : 'Confirmed AI prediction',
          confirmed: !needsVerify,
          markerCoords: null,
        };
      });

      onChangePlateItems(detectedDrafts);
    } catch (err) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Detection failed. Please try again or add foods manually.';
      setScanError(msg);
    } finally {
      setIsScanning(false);
    }
  };

  const startCamera = async () => {
    setCameraError(null);
    setScanError(null);
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setCameraError(
        'Live camera access is unavailable in this browser context. Please switch to Upload Photo.'
      );
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });
      streamRef.current = stream;
      setCapturedImageUrl(null);
      setPlateSummary(null);
      setCameraActive(true);
      requestAnimationFrame(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch(() => {});
        }
      });
    } catch (err) {
      const msg =
        err instanceof Error && err.name === 'NotAllowedError'
          ? 'Camera permission was declined. Allow browser camera access or switch to Upload Photo.'
          : 'Unable to open camera device. Check permissions or use Upload Photo below.';
      setCameraError(msg);
      setCameraActive(false);
    }
  };

  const captureAndScanSnapshot = () => {
    const video = videoRef.current;
    if (!video || !video.videoWidth || !video.videoHeight) return;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
    stopCamera();
    void runAiFoodScan(dataUrl);
  };

  const handleFileChange = (file: File | undefined) => {
    setUploadError(null);
    setScanError(null);
    if (!file) return;
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      setUploadError('Please upload a valid JPG, PNG, or WebP meal photograph.');
      return;
    }
    if (file.size > 15 * 1024 * 1024) {
      setUploadError('Image exceeds 15 MB. Please choose a smaller photograph.');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        stopCamera();
        void runAiFoodScan(reader.result);
      }
    };
    reader.onerror = () => {
      setUploadError('Could not read the selected image file.');
    };
    reader.readAsDataURL(file);
  };

  const handleScanSampleThali = () => {
    stopCamera();
    setInputMode('upload');
    setUploadError(null);
    void runAiFoodScan(HERO_IMAGE_SRC);
  };

  const handleManualFoodChange = (foodName: string) => {
    setManualFood(foodName);
    const def = getDefaultPortion(foodName);
    setManualQty(def.quantity);
    setManualUnit(def.unit);
  };

  const handleAddManualItem = () => {
    const chosenName = customFoodMode ? customFoodName.trim() : manualFood;
    if (!chosenName) return;
    const newItem: PlateItemDraft = {
      uid: uid(),
      foodName: chosenName,
      originalAiLabel: null,
      confidence: null,
      detectionCertainty: null,
      box2d: null,
      isUncertain: false,
      quantity: Math.max(0.1, manualQty || 1),
      unit: manualUnit,
      portionSource: 'User-confirmed',
      verificationStatus: 'Manually added',
      confirmed: true,
      markerCoords: null,
    };
    onChangePlateItems((prev) => [...prev, newItem]);
    if (customFoodMode) {
      setCustomFoodName('');
    }
  };

  const handleLoadPreset = (presetId: string) => {
    const preset = QUICK_MEAL_PRESETS.find((p) => p.id === presetId);
    if (!preset) return;
    const entries: PlateItemDraft[] = preset.items.map((item) => ({
      uid: uid(),
      foodName: item.foodName,
      originalAiLabel: null,
      confidence: null,
      detectionCertainty: null,
      box2d: null,
      isUncertain: false,
      quantity: item.quantity,
      unit: item.unit,
      portionSource: 'User-confirmed',
      verificationStatus: 'Manually added',
      confirmed: true,
      markerCoords: null,
    }));
    setCapturedImageUrl(null);
    setPlateSummary(null);
    setScanError(null);
    onChangePlateItems(entries);
    onChangeMealLabel(preset.label);
  };

  const updateItem = (itemUid: string, patch: Partial<PlateItemDraft>) => {
    onChangePlateItems((prev) =>
      prev.map((item) => {
        if (item.uid !== itemUid) return item;
        const updated = { ...item, ...patch };
        if (patch.foodName && patch.foodName !== item.foodName) {
          const def = getDefaultPortion(patch.foodName);
          updated.quantity = def.quantity;
          updated.unit = def.unit;
          updated.portionSource = 'Estimated default';
          updated.isUncertain = false;
          updated.confirmed = true;
          if (item.originalAiLabel) {
            updated.verificationStatus =
              patch.foodName.toLowerCase() !== item.originalAiLabel.toLowerCase()
                ? 'Corrected by user'
                : 'Confirmed AI prediction';
          }
        }
        return updated;
      })
    );
  };

  const removeItem = (itemUid: string) => {
    onChangePlateItems((prev) => prev.filter((item) => item.uid !== itemUid));
  };

  const confirmedCount = plateItems.filter((i) => i.confirmed && i.foodName.trim()).length;
  const manualUnits = customFoodMode
    ? (['Grams (g)', 'Pieces', 'Katoris', 'Cups', 'Millilitres (ml)', 'Servings'] as PortionUnit[])
    : getAvailableUnits(manualFood);

  const renderBoundingBoxes = () =>
    plateItems
      .filter((item) => item.box2d && item.box2d.length === 4)
      .map((item) => {
        const [ymin, xmin, ymax, xmax] = item.box2d!;
        const top = `${ymin / 10}%`;
        const left = `${xmin / 10}%`;
        const height = `${Math.max((ymax - ymin) / 10, 4)}%`;
        const width = `${Math.max((xmax - xmin) / 10, 4)}%`;
        const isHighlighted = hoveredUid === item.uid;
        const borderColor = item.isUncertain ? '#B88446' : '#527B60';
        const tagBg = item.isUncertain ? '#B88446' : '#294C38';

        return (
          <div
            key={item.uid}
            onMouseEnter={() => setHoveredUid(item.uid)}
            onMouseLeave={() => setHoveredUid(null)}
            style={{
              top,
              left,
              width,
              height,
              borderColor,
              backgroundColor: isHighlighted
                ? item.isUncertain
                  ? 'rgba(184, 132, 70, 0.18)'
                  : 'rgba(82, 123, 96, 0.2)'
                : 'transparent',
            }}
            className="absolute border-2 rounded-md transition-colors duration-150"
          >
            <span
              style={{ backgroundColor: tagBg }}
              className="absolute -top-6 left-0 px-2 py-0.5 text-[11px] font-medium text-white rounded whitespace-nowrap shadow-xs"
            >
              {item.foodName}
              {item.isUncertain ? ' · Verify' : ''}
            </span>
          </div>
        );
      });

  return (
    <div className="space-y-10">
      {/* Editorial Hero Section */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
        <div className="lg:col-span-7 bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl p-7 sm:p-10 flex flex-col justify-between shadow-[0_8px_28px_-20px_rgba(41,76,56,0.14)]">
          <div>
            <p className="text-xs font-medium text-[#527B60] tracking-normal mb-3">
              NutriScan AI · Scan. Understand. Nourish.
            </p>
            <h1 className="font-editorial text-3xl sm:text-4xl lg:text-[2.75rem] font-semibold text-[#294C38] leading-[1.15] tracking-tight text-balance">
              What is on your plate, and what does it contain?
            </h1>
            <p className="mt-5 text-[15px] sm:text-base text-[#758276] leading-relaxed max-w-xl">
              Capture a meal with your camera or upload a photo to identify everyday Indian and
              international dishes, confirm familiar portions like katoris and rotis, and unlock
              holistic Meal Intelligence.
            </p>
          </div>

          <div className="mt-8 pt-6 border-t border-[#E8F0E5] flex flex-wrap items-center gap-3.5">
            <button
              type="button"
              onClick={() => {
                scannerSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }}
              className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white bg-[#294C38] hover:bg-[#527B60] rounded-lg transition-colors duration-150 whitespace-nowrap"
            >
              <Camera className="w-4 h-4" />
              Start Scanning
            </button>
            <button
              type="button"
              onClick={() => {
                scannerSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                handleScanSampleThali();
              }}
              className="inline-flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium text-[#294C38] bg-[#DCEBDD] hover:bg-[#C6DBC8] rounded-lg transition-colors duration-150 whitespace-nowrap"
            >
              <ScanLine className="w-4 h-4" />
              Try Live AI Scan
            </button>
            <button
              type="button"
              onClick={onExploreDatabase}
              className="inline-flex items-center gap-1.5 px-3 py-2.5 text-sm font-medium text-[#527B60] hover:text-[#294C38] transition-colors duration-150 whitespace-nowrap"
            >
              40-Food Database
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="lg:col-span-5">
          <div className="relative h-full min-h-[260px] rounded-2xl overflow-hidden border border-[#DCE4D9] bg-[#E8F0E5]">
            {!heroImgFailed ? (
              <img
                src={HERO_IMAGE_SRC}
                alt="Everyday Indian home meal with whole-wheat rotis, yellow toor dal, steamed rice, vegetable sabzi, and fresh salad"
                referrerPolicy="no-referrer"
                onError={() => setHeroImgFailed(true)}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full min-h-[260px] flex flex-col items-center justify-center p-6 text-center bg-[#E8F0E5]">
                <p className="font-editorial text-xl text-[#294C38]">
                  Everyday Indian &amp; Global Meals
                </p>
                <p className="text-xs text-[#758276] mt-1">
                  Roti · Dal · Rice · Sabzi · Paneer · Idli · Dosa · Poha
                </p>
              </div>
            )}
            <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-[#25352B]/80 via-[#25352B]/35 to-transparent p-5">
              <p className="text-xs text-[#F3F7F0]/90">
                Built for everyday plates · Katori, roti, piece, cup &amp; gram references
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Clean Progression Guide */}
      <section
        aria-label="Workflow progression"
        className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 border-y border-[#DCE4D9] py-4 text-xs"
      >
        {[
          { step: '01', title: 'Food Input', desc: 'Camera or photo' },
          { step: '02', title: 'AI Detection', desc: 'Visual boxes & labels' },
          { step: '03', title: 'Verification', desc: 'Confirm or correct' },
          { step: '04', title: 'Portions', desc: 'Katori, piece, grams' },
          { step: '05', title: 'Meal Intelligence', desc: 'Balance & variety' },
          { step: '06', title: 'History', desc: 'Log & trends' },
        ].map((item) => (
          <div key={item.step} className="flex flex-col gap-0.5">
            <span className="font-semibold text-[#527B60] tabular-nums">{item.step}</span>
            <span className="font-semibold text-[#25352B]">{item.title}</span>
            <span className="text-[#758276]">{item.desc}</span>
          </div>
        ))}
      </section>

      {/* Main Scanning & Verification Studio */}
      <section
        ref={scannerSectionRef}
        id="scanner-studio"
        className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start scroll-mt-20"
      >
        {/* Left: Live Camera & Photo AI Scanner */}
        <div className="lg:col-span-7 bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl p-6 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <h2 className="text-lg font-bold text-[#294C38]">AI Food Scanner</h2>
              <p className="text-xs text-[#758276] mt-0.5">
                Capture a live frame or upload a photo to detect dishes automatically.
              </p>
            </div>

            <div className="inline-flex p-1 bg-[#E8F0E5] rounded-lg self-start">
              <button
                type="button"
                onClick={() => setInputMode('camera')}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors whitespace-nowrap ${
                  inputMode === 'camera'
                    ? 'bg-[#FFFFFF] text-[#294C38] shadow-xs'
                    : 'text-[#758276] hover:text-[#25352B]'
                }`}
              >
                Live Camera
              </button>
              <button
                type="button"
                onClick={() => {
                  stopCamera();
                  setInputMode('upload');
                }}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors whitespace-nowrap ${
                  inputMode === 'upload'
                    ? 'bg-[#FFFFFF] text-[#294C38] shadow-xs'
                    : 'text-[#758276] hover:text-[#25352B]'
                }`}
              >
                Upload Photo
              </button>
            </div>
          </div>

          {/* Viewport */}
          {inputMode === 'camera' ? (
            <div className="space-y-4">
              <div className="relative aspect-[16/10] w-full rounded-xl overflow-hidden bg-[#E8F0E5] border border-[#DCE4D9] flex items-center justify-center">
                {cameraActive ? (
                  <video
                    ref={videoRef}
                    playsInline
                    muted
                    className="w-full h-full object-cover"
                  />
                ) : capturedImageUrl ? (
                  <div className="relative w-full h-full">
                    <img
                      src={capturedImageUrl}
                      alt="Captured meal with detected food boxes"
                      className="w-full h-full object-cover"
                    />
                    {renderBoundingBoxes()}
                  </div>
                ) : (
                  <div className="text-center px-6 py-10 max-w-md">
                    <Camera className="w-9 h-9 text-[#527B60] mx-auto mb-3 stroke-[1.6]" />
                    <p className="text-sm font-semibold text-[#294C38]">
                      Point Your Camera at a Meal
                    </p>
                    <p className="text-xs text-[#758276] mt-1.5 leading-relaxed">
                      Mobile browsers automatically prefer the rear camera. Capture a clear frame
                      and NutriScan AI will identify each visible dish for your review.
                    </p>
                  </div>
                )}

                {isScanning && (
                  <div className="absolute inset-0 bg-[#25352B]/55 backdrop-blur-[2px] flex flex-col items-center justify-center text-white p-4 text-center">
                    <Loader2 className="w-7 h-7 animate-spin mb-2.5" />
                    <p className="text-sm font-semibold">Identifying foods on your plate...</p>
                    <p className="text-xs text-[#DCEBDD] mt-1">
                      Detecting dishes and locating bounding regions
                    </p>
                  </div>
                )}
              </div>

              {cameraError && (
                <div
                  role="alert"
                  className="bg-[#F6F0E4] border border-[#E2D3B5] rounded-xl px-4 py-3 text-xs text-[#6B4A1E] flex items-start gap-2.5"
                >
                  <VideoOff className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{cameraError}</span>
                </div>
              )}

              <div className="flex flex-wrap items-center gap-3">
                {!cameraActive ? (
                  <button
                    type="button"
                    disabled={isScanning}
                    onClick={startCamera}
                    className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-[#294C38] hover:bg-[#527B60] disabled:opacity-60 rounded-lg transition-colors whitespace-nowrap"
                  >
                    <Camera className="w-4 h-4" />
                    {capturedImageUrl ? 'Retake Photo' : 'Enable Camera'}
                  </button>
                ) : (
                  <>
                    <button
                      type="button"
                      disabled={isScanning}
                      onClick={captureAndScanSnapshot}
                      className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-[#294C38] hover:bg-[#527B60] disabled:opacity-60 rounded-lg transition-colors whitespace-nowrap"
                    >
                      <ScanLine className="w-4 h-4" />
                      Capture &amp; Scan Meal
                    </button>
                    <button
                      type="button"
                      onClick={stopCamera}
                      className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-[#294C38] bg-[#E8F0E5] hover:bg-[#DCEBDD] rounded-lg transition-colors whitespace-nowrap"
                    >
                      Stop Camera
                    </button>
                  </>
                )}

                {capturedImageUrl && !cameraActive && (
                  <>
                    <button
                      type="button"
                      disabled={isScanning}
                      onClick={() => void runAiFoodScan(capturedImageUrl)}
                      className="inline-flex items-center gap-1.5 px-3.5 py-2.5 text-xs font-medium text-[#294C38] bg-[#E8F0E5] hover:bg-[#DCEBDD] disabled:opacity-60 rounded-lg transition-colors"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      Re-scan Photo
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setCapturedImageUrl(null);
                        setPlateSummary(null);
                        setScanError(null);
                      }}
                      className="px-2.5 py-2 text-xs font-medium text-[#758276] hover:text-[#25352B]"
                    >
                      Clear
                    </button>
                  </>
                )}

                {!cameraActive && !capturedImageUrl && (
                  <button
                    type="button"
                    disabled={isScanning}
                    onClick={handleScanSampleThali}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2.5 text-xs font-medium text-[#294C38] bg-[#E8F0E5] hover:bg-[#DCEBDD] rounded-lg transition-colors"
                  >
                    <ScanLine className="w-3.5 h-3.5" />
                    Test on Sample Thali
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="relative aspect-[16/10] w-full rounded-xl overflow-hidden bg-[#E8F0E5] border border-[#DCE4D9]">
                {capturedImageUrl ? (
                  <div className="relative w-full h-full">
                    <img
                      src={capturedImageUrl}
                      alt="Uploaded meal with AI detection overlays"
                      className="w-full h-full object-cover"
                    />
                    {renderBoundingBoxes()}
                  </div>
                ) : (
                  <div
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      handleFileChange(e.dataTransfer.files?.[0]);
                    }}
                    onClick={() => fileInputRef.current?.click()}
                    className="w-full h-full border border-dashed border-[#A8BCA6] bg-[#F3F7F0] hover:bg-[#E8F0E5]/70 transition-colors flex flex-col items-center justify-center p-6 text-center cursor-pointer rounded-xl"
                  >
                    <ImageUp className="w-9 h-9 text-[#527B60] mb-3 stroke-[1.6]" />
                    <p className="text-sm font-semibold text-[#294C38]">
                      Drop a meal photo here, or browse files
                    </p>
                    <p className="text-xs text-[#758276] mt-1">
                      AI automatically identifies dishes upon upload · JPG, PNG, WebP
                    </p>
                  </div>
                )}

                {isScanning && (
                  <div className="absolute inset-0 bg-[#25352B]/55 backdrop-blur-[2px] flex flex-col items-center justify-center text-white p-4 text-center">
                    <Loader2 className="w-7 h-7 animate-spin mb-2.5" />
                    <p className="text-sm font-semibold">Scanning meal photograph...</p>
                    <p className="text-xs text-[#DCEBDD] mt-1">
                      Matching visible foods to verified Indian &amp; international references
                    </p>
                  </div>
                )}
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={(e) => handleFileChange(e.target.files?.[0])}
                className="hidden"
              />

              {uploadError && (
                <p role="alert" className="text-xs text-[#9A3412] bg-[#FEF2F2] px-3.5 py-2.5 rounded-lg">
                  {uploadError}
                </p>
              )}

              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  disabled={isScanning}
                  onClick={() => fileInputRef.current?.click()}
                  className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-[#294C38] hover:bg-[#527B60] disabled:opacity-60 rounded-lg transition-colors"
                >
                  <ImageUp className="w-4 h-4" />
                  {capturedImageUrl ? 'Upload Another Photo' : 'Select Meal Photo'}
                </button>
                <button
                  type="button"
                  disabled={isScanning}
                  onClick={handleScanSampleThali}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-medium text-[#294C38] bg-[#E8F0E5] hover:bg-[#DCEBDD] disabled:opacity-60 rounded-lg transition-colors"
                >
                  <ScanLine className="w-3.5 h-3.5" />
                  Test on Sample Thali
                </button>
                {capturedImageUrl && (
                  <button
                    type="button"
                    disabled={isScanning}
                    onClick={() => void runAiFoodScan(capturedImageUrl)}
                    className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-[#527B60] hover:text-[#294C38]"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    Re-scan
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Plate Summary or Scan Error */}
          {plateSummary && !scanError && (
            <div className="bg-[#DCEBDD]/50 border border-[#C6DBC8] rounded-xl px-4 py-3 text-xs text-[#25352B] flex items-start gap-2.5">
              <Check className="w-4 h-4 text-[#294C38] shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-[#294C38]">AI Visual Summary:</span>{' '}
                {plateSummary}
              </div>
            </div>
          )}

          {scanError && (
            <div
              role="alert"
              className="bg-[#F6F0E4] border border-[#E2D3B5] rounded-xl px-4 py-3 text-xs text-[#6B4A1E] flex items-start gap-2.5"
            >
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{scanError}</span>
            </div>
          )}

          {/* Everyday Indian Quick Meal Starters */}
          <div className="pt-2 border-t border-[#E8F0E5]">
            <div className="flex items-baseline justify-between mb-3">
              <h3 className="text-xs font-semibold text-[#294C38]">
                Everyday Indian Plate Starters
              </h3>
              <span className="text-xs text-[#758276]">Quick manual meal templates</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {QUICK_MEAL_PRESETS.map((preset) => (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => handleLoadPreset(preset.id)}
                  className="text-left px-3.5 py-2.5 rounded-xl border border-[#DCE4D9] bg-[#FFFFFF] hover:border-[#527B60] hover:bg-[#F3F7F0] transition-colors"
                >
                  <div className="text-sm font-semibold text-[#294C38]">{preset.label}</div>
                  <div className="text-xs text-[#758276] mt-0.5">{preset.subtitle}</div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Food Verification & Portion Confirmation Panel */}
        <div className="lg:col-span-5 bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl p-6 space-y-5">
          <div>
            <h2 className="text-lg font-bold text-[#294C38]">
              Verification &amp; Portion Confirmation
            </h2>
            <p className="text-xs text-[#758276] mt-0.5">
              Verify detected labels, fix uncertain items, and confirm real portions.
            </p>
          </div>

          <div className="bg-[#F6F0E4] border border-[#E7DEC9] rounded-xl p-3.5 text-xs text-[#25352B] leading-relaxed">
            <strong className="text-[#294C38]">Why portion confirmation matters:</strong> An
            ordinary 2D RGB camera cannot reliably measure exact food mass, bowl depth, or cooking
            oil absorption. Your confirmed portions drive all nutritional calculations.
          </div>

          {/* Current Plate Items */}
          <div className="space-y-3">
            <div className="flex items-baseline justify-between">
              <span className="text-xs font-semibold text-[#294C38]">
                Plate Items ({plateItems.length})
              </span>
              {plateItems.length > 0 && (
                <button
                  type="button"
                  onClick={() => onChangePlateItems([])}
                  className="text-xs text-[#758276] hover:text-[#25352B]"
                >
                  Clear all
                </button>
              )}
            </div>

            {plateItems.length === 0 ? (
              <div className="py-7 px-4 text-center border border-[#E8F0E5] rounded-xl bg-[#F3F7F0]/40">
                <p className="text-sm font-medium text-[#294C38]">Waiting for a meal scan</p>
                <p className="text-xs text-[#758276] mt-1">
                  Capture a photo, upload an image, test on the sample thali, or add foods manually
                  below.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-[#E8F0E5] border border-[#DCE4D9] rounded-xl bg-white">
                {plateItems.map((item) => {
                  const units = getAvailableUnits(item.foodName);
                  const { grams, conversionNote } = convertToGrams(
                    item.foodName,
                    item.quantity,
                    item.unit
                  );
                  const isKnown = CANONICAL_FOOD_CLASSES.includes(item.foodName);
                  const certaintyLabel =
                    item.detectionCertainty === 'high'
                      ? 'High visual certainty'
                      : item.detectionCertainty === 'medium'
                      ? 'Medium visual certainty'
                      : item.detectionCertainty === 'low'
                      ? 'Low certainty — verify'
                      : 'Manual entry';

                  return (
                    <div
                      key={item.uid}
                      onMouseEnter={() => setHoveredUid(item.uid)}
                      onMouseLeave={() => setHoveredUid(null)}
                      className={`p-3.5 space-y-2.5 transition-colors ${
                        hoveredUid === item.uid ? 'bg-[#F3F7F0]/80' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0 flex-1">
                          <select
                            aria-label="Verify or correct food label"
                            value={isKnown ? item.foodName : '__unlisted__'}
                            onChange={(e) => {
                              if (e.target.value !== '__unlisted__') {
                                updateItem(item.uid, { foodName: e.target.value });
                              }
                            }}
                            className="w-full text-sm font-semibold text-[#25352B] bg-transparent border-b border-transparent hover:border-[#DCE4D9] focus:border-[#527B60] focus:outline-none pb-0.5"
                          >
                            {!isKnown && (
                              <option value="__unlisted__">
                                {item.foodName} (Unlisted — select match or keep)
                              </option>
                            )}
                            {CANONICAL_FOOD_CLASSES.map((name) => (
                              <option key={name} value={name}>
                                {name}
                              </option>
                            ))}
                          </select>

                          <p className="text-[11px] text-[#758276] mt-0.5">
                            <span
                              className={
                                item.isUncertain
                                  ? 'text-[#9A6421] font-medium'
                                  : 'text-[#294C38] font-medium'
                              }
                            >
                              {item.verificationStatus}
                            </span>{' '}
                            · {certaintyLabel}
                            {!isKnown && ' · Not in nutrition DB'}
                          </p>
                          {item.visualNote && (
                            <p className="text-[11px] text-[#758276] mt-0.5">{item.visualNote}</p>
                          )}
                        </div>

                        <button
                          type="button"
                          aria-label={`Remove ${item.foodName}`}
                          onClick={() => removeItem(item.uid)}
                          className="p-1.5 text-[#758276] hover:text-[#9A3412] rounded-md transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="grid grid-cols-2 gap-2">
                        <input
                          type="number"
                          aria-label={`Quantity for ${item.foodName}`}
                          min={0.1}
                          max={2000}
                          step={item.unit === 'Grams (g)' ? 10 : 0.5}
                          value={item.quantity}
                          onChange={(e) =>
                            updateItem(item.uid, {
                              quantity: Math.max(0.1, parseFloat(e.target.value) || 0.1),
                              portionSource: 'User-confirmed',
                            })
                          }
                          className="px-2.5 py-1.5 text-xs bg-[#F3F7F0] border border-[#DCE4D9] rounded-lg tabular-nums focus:outline-none focus:border-[#527B60]"
                        />
                        <select
                          aria-label={`Unit for ${item.foodName}`}
                          value={item.unit}
                          onChange={(e) =>
                            updateItem(item.uid, {
                              unit: e.target.value as PortionUnit,
                              portionSource: 'User-confirmed',
                            })
                          }
                          className="px-2.5 py-1.5 text-xs bg-[#F3F7F0] border border-[#DCE4D9] rounded-lg text-[#25352B] focus:outline-none focus:border-[#527B60]"
                        >
                          {units.map((u) => (
                            <option key={u} value={u}>
                              {u}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="flex items-center justify-between text-[11px] text-[#758276] tabular-nums">
                        <span>
                          Est. weight: <strong className="text-[#294C38]">{grams} g</strong> (
                          {conversionNote})
                        </span>
                        <label className="inline-flex items-center gap-1.5 cursor-pointer text-[#25352B]">
                          <input
                            type="checkbox"
                            checked={item.confirmed}
                            onChange={(e) =>
                              updateItem(item.uid, {
                                confirmed: e.target.checked,
                                isUncertain: e.target.checked ? false : item.isUncertain,
                                verificationStatus:
                                  e.target.checked &&
                                  item.verificationStatus === 'Uncertain — requires verification'
                                    ? 'Confirmed by user'
                                    : item.verificationStatus,
                              })
                            }
                            className="accent-[#294C38] rounded"
                          />
                          Confirm
                        </label>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Add Missing Food Manually */}
          <div className="border border-[#DCE4D9] rounded-xl p-4 bg-[#F3F7F0]/60 space-y-3">
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs font-semibold text-[#294C38]">
                Add Missing Food Manually
              </span>
              <button
                type="button"
                onClick={() => setCustomFoodMode((v) => !v)}
                className="text-xs text-[#527B60] hover:text-[#294C38] underline underline-offset-2"
              >
                {customFoodMode ? 'Pick from 40-food database' : 'Enter unlisted food'}
              </button>
            </div>

            {customFoodMode ? (
              <input
                type="text"
                value={customFoodName}
                onChange={(e) => setCustomFoodName(e.target.value)}
                placeholder="e.g., Bhindi Masala (unlisted foods omit values)"
                className="w-full px-3 py-2 text-sm bg-white border border-[#DCE4D9] rounded-lg focus:outline-none focus:border-[#527B60]"
              />
            ) : (
              <select
                aria-label="Select food item"
                value={manualFood}
                onChange={(e) => handleManualFoodChange(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-white border border-[#DCE4D9] rounded-lg text-[#25352B] focus:outline-none focus:border-[#527B60]"
              >
                <optgroup label="Indian Staples & Everyday Meals">
                  {CANONICAL_FOOD_CLASSES.slice(0, 20).map((name) => (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  ))}
                </optgroup>
                <optgroup label="International Foods">
                  {CANONICAL_FOOD_CLASSES.slice(20).map((name) => (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  ))}
                </optgroup>
              </select>
            )}

            <div className="grid grid-cols-2 gap-2.5">
              <div>
                <label className="block text-[11px] text-[#758276] mb-1">Quantity</label>
                <input
                  type="number"
                  min={0.1}
                  max={2000}
                  step={manualUnit === 'Grams (g)' ? 10 : 0.5}
                  value={manualQty}
                  onChange={(e) => setManualQty(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 text-sm bg-white border border-[#DCE4D9] rounded-lg tabular-nums focus:outline-none focus:border-[#527B60]"
                />
              </div>
              <div>
                <label className="block text-[11px] text-[#758276] mb-1">Unit</label>
                <select
                  aria-label="Portion unit"
                  value={manualUnit}
                  onChange={(e) => setManualUnit(e.target.value as PortionUnit)}
                  className="w-full px-3 py-2 text-sm bg-white border border-[#DCE4D9] rounded-lg text-[#25352B] focus:outline-none focus:border-[#527B60]"
                >
                  {manualUnits.map((u) => (
                    <option key={u} value={u}>
                      {u}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <button
              type="button"
              onClick={handleAddManualItem}
              className="w-full inline-flex items-center justify-center gap-1.5 px-4 py-2 text-sm font-medium text-[#294C38] bg-[#DCEBDD] hover:bg-[#C6DBC8] rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add to Plate
            </button>
          </div>

          {/* Meal Name & Analyze CTA */}
          {confirmedCount > 0 && (
            <div className="pt-3 border-t border-[#E8F0E5] space-y-3">
              <div>
                <label
                  htmlFor="meal-label-field"
                  className="block text-xs font-medium text-[#758276] mb-1"
                >
                  Meal Label
                </label>
                <input
                  id="meal-label-field"
                  type="text"
                  value={mealLabel}
                  onChange={(e) => onChangeMealLabel(e.target.value)}
                  placeholder="e.g., Home Lunch, Morning Breakfast"
                  className="w-full px-3 py-2 text-sm bg-white border border-[#DCE4D9] rounded-lg focus:outline-none focus:border-[#527B60]"
                />
              </div>
              <button
                type="button"
                onClick={onAnalyzeMeal}
                className="w-full inline-flex items-center justify-center gap-2 px-5 py-3 text-sm font-semibold text-white bg-[#294C38] hover:bg-[#527B60] rounded-lg transition-colors duration-150"
              >
                Analyse Meal ({confirmedCount} Confirmed Item{confirmedCount === 1 ? '' : 's'})
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};
