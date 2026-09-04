export interface ExampleChip {
  id: string;
  chipLabel: string;
  chipNote: string;
  query: string;
}

export const exampleChips: ExampleChip[] = [
  { id: "hbs", chipLabel: "HbS · rs334", chipNote: "classic sickle mutation", query: "HbS" },
  { id: "ivs1-5", chipLabel: "c.92+5G>A · IVS1-5", chipNote: "common India splice variant", query: "HBB c.92+5G>A" },
  { id: "manual-example", chipLabel: "chr11:5227002 T>A", chipNote: "raw genomic notation", query: "chr11:5227002 T>A" },
];