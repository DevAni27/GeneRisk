import * as pdfjsLib from "pdfjs-dist";

pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`;

export async function extractTextFromPdf(file: File): Promise<string> {
  const arrayBuffer = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;

  let fullText = "";
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    const pageText = content.items.map((item: any) => item.str).join(" ");
    fullText += pageText + "\n";
  }
  return fullText;
}

export interface VariantCandidate {
  raw: string;
  chrom: string;
  position: number;
  ref: string;
  alt: string;
}

const GENOMIC_PATTERN = /chr(\d{1,2}|X|Y)\s*:\s*([\d,]+)\s*([ACGT])\s*>\s*([ACGT])/gi;

export function findVariantCandidates(text: string): VariantCandidate[] {
  const candidates: VariantCandidate[] = [];
  let match;

  while ((match = GENOMIC_PATTERN.exec(text)) !== null) {
    candidates.push({
      raw: match[0],
      chrom: match[1],
      position: parseInt(match[2].replace(/,/g, ""), 10),
      ref: match[3].toUpperCase(),
      alt: match[4].toUpperCase(),
    });
  }

  const seen = new Set<string>();
  return candidates.filter((c) => {
    const key = `${c.chrom}:${c.position}${c.ref}>${c.alt}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}