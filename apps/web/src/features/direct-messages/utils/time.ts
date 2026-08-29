export function formatLastSeen(lastSeenStr?: string | null): string {
  if (!lastSeenStr) return 'Offline';

  const isoUtc = !lastSeenStr.endsWith('Z') && !/[+-]\d{2}:?\d{2}$/.test(lastSeenStr)
    ? `${lastSeenStr}Z`
    : lastSeenStr;

  const date = new Date(isoUtc);
  if (isNaN(date.getTime())) return 'Offline';

  const now = new Date();
  const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const isToday = date.toDateString() === now.toDateString();

  const yesterday = new Date();
  yesterday.setDate(now.getDate() - 1);
  const isYesterday = date.toDateString() === yesterday.toDateString();

  if (isToday) {
    return `Last seen today at ${timeStr}`;
  } else if (isYesterday) {
    return `Last seen yesterday at ${timeStr}`;
  } else {
    const monthDayYear = date.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
    return `Last seen ${monthDayYear} at ${timeStr}`;
  }
}
