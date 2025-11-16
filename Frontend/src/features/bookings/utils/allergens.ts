/**
 * Parses allergen string from API format to array
 * Handles formats like: "AE-CONTAINS,AM-CONTAINS,AN-MAY_CONTAIN"
 * or quoted: "\"AE-CONTAINS,AM-CONTAINS\""
 */
export function parseAllergens(allergensStr: string): string[] {
  if (!allergensStr || allergensStr === '""' || allergensStr === '') {
    return [];
  }

  // Remove surrounding quotes if present
  let cleaned = allergensStr.trim();
  if (cleaned.startsWith('"') && cleaned.endsWith('"')) {
    cleaned = cleaned.slice(1, -1);
  }

  // Remove escaped quotes
  cleaned = cleaned.replace(/\\"/g, '');

  // If empty after cleaning, return empty array
  if (!cleaned || cleaned === '""' || cleaned === '') {
    return [];
  }

  // Split by comma and filter out empty strings
  return cleaned
    .split(',')
    .map(item => item.trim())
    .filter(item => item.length > 0);
}

/**
 * Formats allergen code to human-readable format
 * Example: "AE-CONTAINS" -> "AE (Contains)"
 */
export function formatAllergen(code: string): string {
  const [allergenCode, status] = code.split('-');

  if (!allergenCode) return code;

  // Format status
  let formattedStatus = '';
  if (status) {
    formattedStatus = status.replace(/_/g, ' ').toLowerCase();
    formattedStatus = formattedStatus.charAt(0).toUpperCase() + formattedStatus.slice(1);
  }

  return formattedStatus ? `${allergenCode} (${formattedStatus})` : allergenCode;
}
