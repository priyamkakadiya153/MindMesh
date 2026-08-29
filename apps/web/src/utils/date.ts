/**
 * Utility function to format timestamps according to specified IANA timezone
 */
export function formatTimestamp(
  dateInput: string | number | Date | null | undefined,
  timeZone?: string | null
): string {
  if (!dateInput) return '';
  const date = new Date(dateInput);
  if (isNaN(date.getTime())) return '';

  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  };

  if (timeZone) {
    try {
      options.timeZone = timeZone;
    } catch (e) {
      console.warn(`Invalid timezone: ${timeZone}`);
    }
  }

  return new Intl.DateTimeFormat(undefined, options).format(date);
}
