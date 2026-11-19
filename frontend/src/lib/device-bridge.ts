/**
 * Device bridge interface for platform-specific biometric attestation
 * - Provides a seam for native device integration
 * - Returns proof results for backend verification
 */

export interface BiometricProofResult {
  success: boolean
  proof_data?: string
  error_code?: string
  error_message?: string
}

export interface DeviceBridge {
  /**
   * Check if biometric authentication is available
   */
  isBiometricAvailable(): Promise<boolean>

  /**
   * Request biometric authentication
   * @param challenge - Server-provided challenge data
   */
  requestBiometricProof(challenge: string): Promise<BiometricProofResult>

  /**
   * Get device identifier for registration
   */
  getDeviceIdentifier(): Promise<string>
}

// Seeded device ID from backend seed data (for demo/test purposes)
const DEMO_DEVICE_ID = '10000000-0000-0000-0000-000000000201'

/**
 * Web/browser implementation (stub for demo)
 * In a real mobile app, this would be implemented by native modules
 */
class WebDeviceBridge implements DeviceBridge {
  async isBiometricAvailable(): Promise<boolean> {
    // In a real implementation, check for WebAuthn support
    return Promise.resolve(false)
  }

  async requestBiometricProof(challenge: string): Promise<BiometricProofResult> {
    // Stub implementation - in real app, would call native bridge
    console.log('Biometric proof requested with challenge:', challenge)
    return Promise.resolve({
      success: false,
      error_code: 'NOT_AVAILABLE',
      error_message: 'Biometric authentication not available in web browser',
    })
  }

  async getDeviceIdentifier(): Promise<string> {
    // For demo/test purposes, use the seeded device ID
    // In a real implementation, this would be a unique device identifier
    let deviceId = localStorage.getItem('device_identifier')
    if (!deviceId) {
      // Use demo device ID that matches seeded data for local development
      deviceId = DEMO_DEVICE_ID
      localStorage.setItem('device_identifier', deviceId)
    }
    return Promise.resolve(deviceId)
  }
}

/**
 * Singleton device bridge instance
 */
export const deviceBridge: DeviceBridge = new WebDeviceBridge()
