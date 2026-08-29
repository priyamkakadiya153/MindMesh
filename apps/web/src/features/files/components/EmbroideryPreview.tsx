import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, RotateCcw, ZoomIn, ZoomOut, Maximize2, Loader2, Eye, EyeOff, Info, Scissors, Layers, CheckCircle } from 'lucide-react';
import { AttachmentItem } from '../files-api';
import { parseDST, DSTParsedData } from '../utils/dstParser';

interface EmbroideryPreviewProps {
  item: AttachmentItem;
  onDownload: () => void;
  isDownloading: boolean;
}

// Deterministic visualization color palette for thread color sections
const VISUALIZATION_PALETTE = [
  '#4F46E5', // Indigo
  '#10B981', // Emerald
  '#EC4899', // Pink
  '#F59E0B', // Amber
  '#06B6D4', // Cyan
  '#8B5CF6', // Purple
  '#EF4444', // Red
  '#14B8A6', // Teal
  '#6366F1', // Blue-Indigo
  '#84CC16'  // Lime
];

export function EmbroideryPreview({ item, onDownload, isDownloading }: EmbroideryPreviewProps) {
  const [data, setData] = useState<DSTParsedData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [showJumps, setShowJumps] = useState(true);

  // Animation State
  const [isPlaying, setIsPlaying] = useState(false);
  const [animProgress, setAnimProgress] = useState<number | null>(null); // null = show full design
  const [speed, setSpeed] = useState<number>(2); // 1x, 2x, 5x, 10x

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animFrameRef = useRef<number | null>(null);
  const isDraggingRef = useRef(false);
  const dragStartRef = useRef({ x: 0, y: 0 });

  // 1. Fetch and Parse DST Binary Data
  useEffect(() => {
    let active = true;
    setIsLoading(true);
    setError(null);

    const token = localStorage.getItem('token') || '';
    const headers: HeadersInit = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const urlWithToken = token ? `${item.preview_url}?token=${encodeURIComponent(token)}` : item.preview_url;

    fetch(urlWithToken, { headers })
      .then(async (res) => {
        if (!res.ok) throw new Error('Failed to load embroidery file binary');
        const buffer = await res.arrayBuffer();
        if (!active) return;
        const parsed = parseDST(buffer);
        setData(parsed);
      })
      .catch((err) => {
        console.error('DST parse error:', err);
        if (active) setError(err.message || 'Error parsing Tajima DST embroidery design file');
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [item.id, item.preview_url]);

  // 2. Render Canvas Design
  useEffect(() => {
    if (!data || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    // Grid Background Pattern
    ctx.fillStyle = '#18181B';
    ctx.fillRect(0, 0, width, height);

    ctx.strokeStyle = '#27272A';
    ctx.lineWidth = 1;
    const gridSize = 20;
    for (let x = 0; x < width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    const { bounds, allStitches } = data;
    if (allStitches.length === 0) return;

    const designWidth = Math.max(bounds.widthMm, 1);
    const designHeight = Math.max(bounds.heightMm, 1);

    // Calculate Fit Scale
    const padding = 40;
    const scaleX = (width - padding * 2) / designWidth;
    const scaleY = (height - padding * 2) / designHeight;
    const fitScale = Math.min(scaleX, scaleY);
    const finalScale = fitScale * zoom;

    const centerX = width / 2 + pan.x;
    const centerY = height / 2 + pan.y;

    const midX = (bounds.minX + bounds.maxX) / 2;
    const midY = (bounds.minY + bounds.maxY) / 2;

    ctx.save();
    ctx.translate(centerX, centerY);
    // In DST coordinates Y goes upwards, canvas Y goes downwards
    ctx.scale(finalScale, -finalScale);
    ctx.translate(-midX, -midY);

    const maxStitchIndex = animProgress !== null ? animProgress : allStitches.length;

    // Render Jump Stitches if enabled
    if (showJumps && data.jumps.length > 0) {
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
      ctx.lineWidth = 0.5 / finalScale;
      ctx.setLineDash([2 / finalScale, 3 / finalScale]);

      let count = 0;
      for (const jump of data.jumps) {
        if (count > maxStitchIndex) break;
        ctx.beginPath();
        ctx.moveTo(jump.from.x, jump.from.y);
        ctx.lineTo(jump.to.x, jump.to.y);
        ctx.stroke();
        count++;
      }
      ctx.setLineDash([]);
    }

    // Render Normal Stitches
    ctx.lineWidth = 1.2 / finalScale;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    let currentSectionColor = VISUALIZATION_PALETTE[0];
    let isPathOpen = false;

    for (let i = 0; i < maxStitchIndex && i < allStitches.length; i++) {
      const st = allStitches[i];
      const prevSt = i > 0 ? allStitches[i - 1] : null;

      currentSectionColor = VISUALIZATION_PALETTE[st.colorIndex % VISUALIZATION_PALETTE.length];

      if (st.isJump || st.isColorChange || !prevSt) {
        if (isPathOpen) {
          ctx.stroke();
          isPathOpen = false;
        }
        ctx.beginPath();
        ctx.moveTo(st.x, st.y);
      } else {
        if (!isPathOpen) {
          ctx.beginPath();
          ctx.strokeStyle = currentSectionColor;
          ctx.moveTo(prevSt.x, prevSt.y);
          isPathOpen = true;
        }
        ctx.lineTo(st.x, st.y);
      }
    }

    if (isPathOpen) {
      ctx.stroke();
    }

    // Draw End Needle Marker
    if (animProgress !== null && animProgress > 0 && animProgress <= allStitches.length) {
      const needleSt = allStitches[animProgress - 1];
      ctx.fillStyle = '#EF4444';
      ctx.beginPath();
      ctx.arc(needleSt.x, needleSt.y, 4 / finalScale, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.restore();
  }, [data, zoom, pan, showJumps, animProgress]);

  // 3. Handle Animation Loop
  useEffect(() => {
    if (!isPlaying || !data) {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      return;
    }

    let lastTime = performance.now();
    const total = data.allStitches.length;

    const step = (time: number) => {
      const delta = time - lastTime;
      lastTime = time;

      const stitchIncrement = Math.ceil((delta * 25 * speed) / 16.6);

      setAnimProgress((prev) => {
        const current = prev === null ? 0 : prev;
        const next = current + stitchIncrement;
        if (next >= total) {
          setIsPlaying(false);
          return total;
        }
        return next;
      });

      animFrameRef.current = requestAnimationFrame(step);
    };

    animFrameRef.current = requestAnimationFrame(step);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [isPlaying, data, speed]);

  // Pan Mouse Handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    isDraggingRef.current = true;
    dragStartRef.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDraggingRef.current) return;
    setPan({
      x: e.clientX - dragStartRef.current.x,
      y: e.clientY - dragStartRef.current.y
    });
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleResetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const togglePlay = () => {
    if (!data) return;
    if (isPlaying) {
      setIsPlaying(false);
    } else {
      if (animProgress === null || animProgress >= data.allStitches.length) {
        setAnimProgress(0);
      }
      setIsPlaying(true);
    }
  };

  const handleReplay = () => {
    setAnimProgress(0);
    setIsPlaying(true);
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-textMuted space-y-3">
        <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
        <span className="text-xs font-semibold">Parsing Tajima DST embroidery design...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-md w-full bg-bgCard border border-borderColor rounded-2xl p-8 text-center shadow-xl">
        <div className="w-16 h-16 rounded-2xl bg-rose-500/10 text-rose-400 flex items-center justify-center mx-auto mb-4">
          <Scissors className="w-8 h-8" />
        </div>
        <h4 className="text-base font-bold text-textPrimary mb-1">Embroidery Parsing Error</h4>
        <p className="text-xs text-textMuted mb-6 leading-relaxed">
          {error || 'Unable to parse Tajima DST file format.'}
        </p>

        <button
          type="button"
          onClick={onDownload}
          disabled={isDownloading}
          className="w-full py-2.5 rounded-xl bg-accent hover:bg-accentHover text-white text-xs font-semibold flex items-center justify-center space-x-2 transition-all shadow-md cursor-pointer"
        >
          <Scissors className="w-4 h-4" />
          <span>Download Original DST File</span>
        </button>
      </div>
    );
  }

  const formatNumber = (num: number) => num.toLocaleString();
  const currentStitchDisplay = animProgress !== null ? animProgress : data.stitchCount;

  return (
    <div className="w-full h-full flex flex-col lg:flex-row gap-4 overflow-hidden select-none">
      {/* Canvas Viewport & Interactive Toolbar */}
      <div className="flex-1 bg-zinc-950 border border-borderColor rounded-2xl overflow-hidden flex flex-col relative shadow-inner">
        {/* Top Control Bar */}
        <div className="p-2.5 bg-zinc-900/90 backdrop-blur border-b border-borderColor flex items-center justify-between z-10">
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-1 rounded-lg bg-purple-500/10 text-purple-400 text-[11px] font-semibold flex items-center gap-1.5 border border-purple-500/20">
              <Scissors className="w-3.5 h-3.5" /> Tajima DST
            </span>
            <span className="text-xs text-zinc-400 font-mono hidden sm:inline truncate max-w-[200px]">
              {data.label}
            </span>
          </div>

          <div className="flex items-center space-x-1.5">
            <button
              type="button"
              onClick={() => setShowJumps(prev => !prev)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors flex items-center space-x-1 ${
                showJumps ? 'bg-zinc-800 text-zinc-200 border border-zinc-700' : 'bg-transparent text-zinc-400 hover:bg-zinc-800'
              }`}
              title="Toggle Jump Stitches"
            >
              {showJumps ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
              <span className="hidden sm:inline">Jumps ({data.jumpCount})</span>
            </button>

            <div className="h-4 w-px bg-zinc-700 mx-1" />

            <button
              type="button"
              onClick={() => setZoom(prev => Math.min(prev + 0.3, 4))}
              className="p-1.5 text-zinc-300 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => setZoom(prev => Math.max(prev - 0.3, 0.4))}
              className="p-1.5 text-zinc-300 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={handleResetView}
              className="p-1.5 text-zinc-300 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
              title="Reset Zoom & Pan"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* 2D Canvas */}
        <div
          className="flex-1 relative cursor-grab active:cursor-grabbing overflow-hidden"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          <canvas
            ref={canvasRef}
            width={800}
            height={550}
            className="w-full h-full block"
          />
        </div>

        {/* Bottom Animation Controls */}
        <div className="p-3 bg-zinc-900/90 backdrop-blur border-t border-borderColor flex flex-col sm:flex-row items-center justify-between gap-3 z-10">
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={togglePlay}
              className="px-3.5 py-1.5 rounded-xl bg-accent hover:bg-accentHover text-white text-xs font-semibold flex items-center space-x-1.5 shadow-sm transition-all cursor-pointer"
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              <span>{isPlaying ? 'Pause' : 'Play Animation'}</span>
            </button>

            <button
              type="button"
              onClick={handleReplay}
              className="p-1.5 text-zinc-300 hover:text-white hover:bg-zinc-800 rounded-xl transition-colors cursor-pointer"
              title="Replay Stitch Animation"
            >
              <RotateCcw className="w-4 h-4" />
            </button>

            {/* Speed Selector */}
            <div className="flex items-center space-x-1 bg-zinc-800 rounded-xl p-1 text-[11px] font-semibold text-zinc-300">
              {[1, 2, 5, 10].map(s => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setSpeed(s)}
                  className={`px-2 py-0.5 rounded-lg transition-colors ${
                    speed === s ? 'bg-purple-600 text-white' : 'hover:bg-zinc-700 text-zinc-400'
                  }`}
                >
                  {s}x
                </button>
              ))}
            </div>
          </div>

          {/* Stitch Progress */}
          <div className="flex items-center space-x-3 w-full sm:w-auto">
            <span className="text-xs font-mono text-zinc-300">
              {formatNumber(currentStitchDisplay)} / {formatNumber(data.stitchCount)} stitches
            </span>
            <input
              type="range"
              min={0}
              max={data.stitchCount}
              value={currentStitchDisplay}
              onChange={(e) => {
                setIsPlaying(false);
                setAnimProgress(parseInt(e.target.value, 10));
              }}
              className="w-full sm:w-32 accent-purple-500 cursor-pointer"
            />
          </div>
        </div>
      </div>

      {/* Right Sidebar: Real Metadata Panel */}
      <div className="w-full lg:w-72 bg-bgCard border border-borderColor rounded-2xl p-4 flex flex-col justify-between shrink-0 shadow-lg space-y-4">
        <div className="space-y-4">
          <div className="flex items-center space-x-2.5 pb-3 border-b border-borderColor">
            <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <Scissors className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-textPrimary">Embroidery Details</h4>
              <p className="text-[11px] text-textMuted">Extracted format metadata</p>
            </div>
          </div>

          {/* Metadata Grid */}
          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-bgTertiary border border-borderColor">
              <span className="text-textMuted flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" /> Stitches
              </span>
              <span className="font-bold text-textPrimary font-mono">{formatNumber(data.stitchCount)}</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-xl bg-bgTertiary border border-borderColor">
              <span className="text-textMuted flex items-center gap-2">
                <Maximize2 className="w-4 h-4 text-emerald-400" /> Dimensions
              </span>
              <div className="text-right">
                <span className="font-bold text-textPrimary font-mono block">
                  {data.bounds.widthCm} × {data.bounds.heightCm} cm
                </span>
                <span className="text-[10px] text-textMuted font-mono">
                  ({data.bounds.widthMm} × {data.bounds.heightMm} mm)
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-xl bg-bgTertiary border border-borderColor">
              <span className="text-textMuted flex items-center gap-2">
                <Scissors className="w-4 h-4 text-rose-400" /> Color Changes
              </span>
              <span className="font-bold text-textPrimary font-mono">{data.colorChangeCount}</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-xl bg-bgTertiary border border-borderColor">
              <span className="text-textMuted flex items-center gap-2">
                <Eye className="w-4 h-4 text-amber-400" /> Jump Stitches
              </span>
              <span className="font-bold text-textPrimary font-mono">{formatNumber(data.jumpCount)}</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-xl bg-bgTertiary border border-borderColor">
              <span className="text-textMuted flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-blue-400" /> Format
              </span>
              <span className="font-bold text-purple-400">Tajima DST</span>
            </div>
          </div>

          {/* Color Disclaimer Alert */}
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-400 space-y-1">
            <div className="flex items-center space-x-1.5 font-semibold">
              <Info className="w-4 h-4 shrink-0" />
              <span>Color Disclaimer</span>
            </div>
            <p className="text-[10px] text-amber-400/90 leading-relaxed">
              Preview colors are visualization colors. Tajima DST format stores stitch paths and stop signals, but does not embed thread color codes.
            </p>
          </div>
        </div>

        {/* Download Button */}
        <button
          type="button"
          onClick={onDownload}
          disabled={isDownloading}
          className="w-full py-2.5 rounded-xl bg-accent hover:bg-accentHover disabled:opacity-50 text-white text-xs font-semibold flex items-center justify-center space-x-2 transition-all shadow-md cursor-pointer"
        >
          {isDownloading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Downloading...</span>
            </>
          ) : (
            <>
              <Scissors className="w-4 h-4" />
              <span>Download DST Design</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
