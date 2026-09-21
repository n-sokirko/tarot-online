/** Card number as the deck prints it: 17 → "XVII", 0 → "0". */
export function roman(n: number | null | undefined): string {
  if (n === null || n === undefined) return '';
  if (n <= 0) return '0';
  const table: [number, string][] = [
    [10, 'X'], [9, 'IX'], [5, 'V'], [4, 'IV'], [1, 'I'],
  ];
  let out = '';
  let rest = n;
  for (const [value, glyph] of table) {
    while (rest >= value) {
      out += glyph;
      rest -= value;
    }
  }
  return out;
}
