export interface DSTStitch {
  x: number; // mm
  y: number; // mm
  dx: number; // mm
  dy: number; // mm
  isJump: boolean;
  isColorChange: boolean;
  isEnd: boolean;
  colorIndex: number;
}

export interface DSTColorSection {
  colorIndex: number;
  points: { x: number; y: number }[];
}

export interface DSTJumpLine {
  from: { x: number; y: number };
  to: { x: number; y: number };
}

export interface DSTParsedData {
  label: string;
  stitchCount: number;
  colorChangeCount: number;
  jumpCount: number;
  bounds: {
    minX: number; // mm
    maxX: number; // mm
    minY: number; // mm
    maxY: number; // mm
    widthMm: number;
    heightMm: number;
    widthCm: number;
    heightCm: number;
  };
  sections: DSTColorSection[];
  jumps: DSTJumpLine[];
  allStitches: DSTStitch[];
}

export function parseDST(buffer: ArrayBuffer): DSTParsedData {
  const bytes = new Uint8Array(buffer);

  // 1. Parse Header (First 512 bytes)
  const headerBytes = bytes.subarray(0, Math.min(512, bytes.length));
  let headerText = '';
  for (let i = 0; i < headerBytes.length; i++) {
    headerText += String.fromCharCode(headerBytes[i]);
  }

  const labelMatch = headerText.match(/LA:([^\r\n]*)/);
  const label = labelMatch ? labelMatch[1].trim() : 'Embroidery Design';

  const headerStitchMatch = headerText.match(/ST:\s*(\d+)/);
  const headerStitchCount = headerStitchMatch ? parseInt(headerStitchMatch[1], 10) : 0;

  const headerColorMatch = headerText.match(/CO:\s*(\d+)/);
  const headerColorCount = headerColorMatch ? parseInt(headerColorMatch[1], 10) : 0;

  // 2. Parse Binary Stitch Data (Offset 512)
  let curX = 0; // in 0.1 mm
  let curY = 0; // in 0.1 mm

  let minX = 0;
  let maxX = 0;
  let minY = 0;
  let maxY = 0;

  let stitchCount = 0;
  let jumpCount = 0;
  let colorChangeCount = 0;
  let currentColorIndex = 0;

  const sections: DSTColorSection[] = [{ colorIndex: 0, points: [{ x: 0, y: 0 }] }];
  const jumps: DSTJumpLine[] = [];
  const allStitches: DSTStitch[] = [];

  const startOffset = 512;
  const totalBytes = bytes.length;

  for (let i = startOffset; i + 2 < totalBytes; i += 3) {
    const b0 = bytes[i];
    const b1 = bytes[i + 1];
    const b2 = bytes[i + 2];

    let dx = 0;
    let dy = 0;

    // Decode X delta (0.1 mm units)
    if (b0 & 0x01) dx += 1;
    if (b0 & 0x02) dx -= 1;
    if (b0 & 0x04) dx += 3;
    if (b0 & 0x08) dx -= 3;

    if (b1 & 0x01) dx += 9;
    if (b1 & 0x02) dx -= 9;
    if (b1 & 0x04) dx += 27;
    if (b1 & 0x08) dx -= 27;

    if (b2 & 0x04) dx += 81;
    if (b2 & 0x08) dx -= 81;

    // Decode Y delta (0.1 mm units)
    if (b0 & 0x80) dy += 1;
    if (b0 & 0x40) dy -= 1;
    if (b0 & 0x20) dy += 3;
    if (b0 & 0x10) dy -= 3;

    if (b1 & 0x80) dy += 9;
    if (b1 & 0x40) dy -= 9;
    if (b1 & 0x20) dy += 27;
    if (b1 & 0x10) dy -= 27;

    if (b2 & 0x20) dy += 81;
    if (b2 & 0x10) dy -= 81;

    // Flags
    const isJump = (b2 & 0x83) === 0x83;
    const isColorChange = (b2 & 0xC3) === 0xC3;
    const isEnd = (b2 & 0xF3) === 0xF3;

    if (isEnd) break;

    const prevX = curX;
    const prevY = curY;

    curX += dx;
    curY += dy;

    minX = Math.min(minX, curX);
    maxX = Math.max(maxX, curX);
    minY = Math.min(minY, curY);
    maxY = Math.max(maxY, curY);

    const xMm = curX / 10.0;
    const yMm = curY / 10.0;
    const dxMm = dx / 10.0;
    const dyMm = dy / 10.0;

    stitchCount++;

    allStitches.push({
      x: xMm,
      y: yMm,
      dx: dxMm,
      dy: dyMm,
      isJump,
      isColorChange,
      isEnd,
      colorIndex: currentColorIndex
    });

    if (isColorChange) {
      colorChangeCount++;
      currentColorIndex++;
      sections.push({ colorIndex: currentColorIndex, points: [{ x: xMm, y: yMm }] });
    } else if (isJump) {
      jumpCount++;
      jumps.push({
        from: { x: prevX / 10.0, y: prevY / 10.0 },
        to: { x: xMm, y: yMm }
      });
      sections[sections.length - 1].points.push({ x: xMm, y: yMm });
    } else {
      sections[sections.length - 1].points.push({ x: xMm, y: yMm });
    }
  }

  const minXmm = minX / 10.0;
  const maxXmm = maxX / 10.0;
  const minYmm = minY / 10.0;
  const maxYmm = maxY / 10.0;

  const widthMm = maxXmm - minXmm;
  const heightMm = maxYmm - minYmm;

  return {
    label: label || 'Tajima Embroidery Design',
    stitchCount: stitchCount || headerStitchCount,
    colorChangeCount: colorChangeCount || headerColorCount,
    jumpCount,
    bounds: {
      minX: minXmm,
      maxX: maxXmm,
      minY: minYmm,
      maxY: maxYmm,
      widthMm: Math.round(widthMm * 10) / 10,
      heightMm: Math.round(heightMm * 10) / 10,
      widthCm: Math.round((widthMm / 10) * 10) / 10,
      heightCm: Math.round((heightMm / 10) * 10) / 10
    },
    sections,
    jumps,
    allStitches
  };
}
