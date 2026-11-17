/**
 * Host configuration for brand-specific theming
 * In production, this would read from host container configuration
 */

export type Brand = 'lloyds' | 'bank_of_scotland';

interface HostConfig {
  brand: Brand;
  brandLabel: string;
  primaryColor: string;
}

/**
 * Get brand configuration from host context
 * For now, defaults to Lloyds; in production would read from host container
 */
export function getHostConfig(): HostConfig {
  // In production, this would read from:
  // - URL parameter
  // - localStorage
  // - postMessage from host container
  // - or other host-provided configuration
  
  const brand: Brand = 'lloyds';
  
  return {
    brand,
    brandLabel: brand === 'lloyds' ? 'Lloyds Bank' : 'Bank of Scotland',
    primaryColor: brand === 'lloyds' ? '#006943' : '#004990',
  };
}

/**
 * Get current brand
 */
export function getCurrentBrand(): Brand {
  return getHostConfig().brand;
}

/**
 * Get brand label for display
 */
export function getBrandLabel(): string {
  return getHostConfig().brandLabel;
}
