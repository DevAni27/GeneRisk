export type LookupResult = 'Pathogenic' | 'Benign' | 'Uncertain'

export interface LookupRecord {
  id: string
  date: string
  variant: string
  worker: string
  facility: string
  result: LookupResult
  /** Links to a full Variant in data/variants.ts, if available */
  variantId?: string
}

export const lookupHistory: LookupRecord[] = [
  {
    id: 'l-1',
    date: '28 Aug, 10:14',
    variant: 'HBB · chr11:5,227,002 A>T',
    worker: 'Sunita Patil',
    facility: 'PHC Betul',
    result: 'Pathogenic',
    variantId: 'hbs',
  },
  {
    id: 'l-2',
    date: '28 Aug, 09:52',
    variant: 'HBB · c.92+5G>C',
    worker: 'Sunita Patil',
    facility: 'PHC Betul',
    result: 'Pathogenic',
    variantId: 'ivs1-5',
  },
  {
    id: 'l-3',
    date: '27 Aug, 16:30',
    variant: 'HBB · c.118A>C',
    worker: 'Ramesh Naik',
    facility: 'Camp 12, Kalahandi',
    result: 'Benign',
    variantId: 'vus-118',
  },
  {
    id: 'l-4',
    date: '27 Aug, 15:05',
    variant: 'HBB · chr11:5,227,010 C>G',
    worker: 'Ramesh Naik',
    facility: 'Camp 12, Kalahandi',
    result: 'Uncertain',
  },
  {
    id: 'l-5',
    date: '26 Aug, 11:47',
    variant: 'HBB · c.27_28insG',
    worker: 'Sunita Patil',
    facility: 'PHC Betul',
    result: 'Pathogenic',
  },
]