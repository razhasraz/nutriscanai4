import React, { useState } from 'react';
import { Check, Copy, Download } from 'lucide-react';
import { UPGRADED_STREAMLIT_FILES } from '../data/streamlitBundle';

export const StreamlitRepoView: React.FC = () => {
  const [selectedPath, setSelectedPath] = useState<string>(UPGRADED_STREAMLIT_FILES[0].path);
  const [copiedPath, setCopiedPath] = useState<string | null>(null);

  const activeFile =
    UPGRADED_STREAMLIT_FILES.find((f) => f.path === selectedPath) ?? UPGRADED_STREAMLIT_FILES[0];

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(activeFile.content);
      setCopiedPath(activeFile.path);
      setTimeout(() => setCopiedPath(null), 1800);
    } catch {
      // Clipboard blocked in restricted iframe context
    }
  };

  const handleDownload = () => {
    const blob = new Blob([activeFile.content], { type: 'text/plain;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', activeFile.path.split('/').pop() || 'file.txt');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8">
      {/* Intro */}
      <div className="bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl p-7 sm:p-8">
        <p className="text-xs font-medium text-[#527B60] mb-1.5">
          Preserved Python · Streamlit · YOLO · OpenCV · Pandas · Plotly Architecture
        </p>
        <h1 className="font-editorial text-3xl font-semibold text-[#294C38] tracking-tight">
          Upgraded Streamlit Codebase &amp; Cloud Deployment
        </h1>
        <p className="text-sm text-[#758276] mt-2 leading-relaxed max-w-3xl">
          Your entire Python/Streamlit repository has been upgraded inside{' '}
          <code className="text-[#294C38] bg-[#E8F0E5] px-1.5 py-0.5 rounded">
            nutriscan_streamlit/
          </code>{' '}
          while preserving every existing import, YOLO model-loading workflow, WebRTC camera
          processor, and CSV nutrition calculation. Inspect or download any modified file below.
        </p>

        {/* Deployment Steps */}
        <div className="mt-6 pt-6 border-t border-[#E8F0E5] grid grid-cols-1 md:grid-cols-3 gap-5 text-sm">
          <div>
            <p className="text-xs font-semibold text-[#527B60] mb-1">01. Sync Repository</p>
            <p className="text-xs text-[#25352B] leading-relaxed">
              Copy the upgraded files from <code>nutriscan_streamlit/</code> into your GitHub
              repository, including the new <code>modules/meal_intelligence.py</code>,{' '}
              <code>packages.txt</code>, and <code>.streamlit/config.toml</code>.
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold text-[#527B60] mb-1">02. Model Weights</p>
            <p className="text-xs text-[#25352B] leading-relaxed">
              Commit <code>models/nutriscan_food_yolo.pt</code> (or run{' '}
              <code>python models/download_weights.py</code> for base <code>yolo11n.pt</code>).
              Missing weights degrade gracefully with clear instructions.
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold text-[#527B60] mb-1">
              03. Deploy on Streamlit Cloud
            </p>
            <p className="text-xs text-[#25352B] leading-relaxed">
              Connect your repo on <strong>share.streamlit.io</strong>, set Main file path to{' '}
              <code>app.py</code>, Python 3.11. HTTPS is enabled automatically for mobile rear-camera
              WebRTC scanning.
            </p>
          </div>
        </div>
      </div>

      {/* File Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-4 bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl overflow-hidden">
          <div className="p-4 border-b border-[#E8F0E5]">
            <h2 className="text-sm font-bold text-[#294C38]">
              Modified &amp; Added Files ({UPGRADED_STREAMLIT_FILES.length})
            </h2>
          </div>
          <div className="divide-y divide-[#E8F0E5] max-h-[560px] overflow-y-auto">
            {UPGRADED_STREAMLIT_FILES.map((file) => {
              const selected = file.path === activeFile.path;
              return (
                <button
                  key={file.path}
                  type="button"
                  onClick={() => setSelectedPath(file.path)}
                  className={`w-full text-left px-4 py-3.5 transition-colors ${
                    selected ? 'bg-[#DCEBDD]/50' : 'hover:bg-[#F3F7F0]'
                  }`}
                >
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="text-xs font-mono font-semibold text-[#294C38] truncate">
                      {file.path}
                    </span>
                    <span className="text-[11px] font-medium text-[#527B60] shrink-0">
                      {file.status}
                    </span>
                  </div>
                  <p className="text-xs text-[#758276] mt-1 line-clamp-2">{file.summary}</p>
                </button>
              );
            })}
          </div>
        </div>

        <div className="lg:col-span-8 bg-[#FFFFFF] border border-[#DCE4D9] rounded-2xl overflow-hidden">
          <div className="p-4 sm:p-5 border-b border-[#E8F0E5] flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="font-mono text-sm font-semibold text-[#294C38]">
                {activeFile.path}
              </div>
              <p className="text-xs text-[#758276] mt-0.5">{activeFile.summary}</p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={handleCopy}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-[#294C38] bg-[#E8F0E5] hover:bg-[#DCEBDD] rounded-lg transition-colors"
              >
                {copiedPath === activeFile.path ? (
                  <>
                    <Check className="w-3.5 h-3.5" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    Copy
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={handleDownload}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-[#294C38] hover:bg-[#527B60] rounded-lg transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                Download
              </button>
            </div>
          </div>
          <pre className="p-5 text-xs font-mono text-[#25352B] bg-[#F3F7F0]/70 overflow-x-auto max-h-[520px] leading-relaxed">
            <code>{activeFile.content}</code>
          </pre>
        </div>
      </div>
    </div>
  );
};
