/**
 * Frame Rate Limiter Utility
 * Prevents overloading the backend with too many frame requests
 */
export class FrameLimiter {
  private lastFrameTime: number = 0;
  private minFrameInterval: number;

  /**
   * @param maxFPS - Maximum frames per second to process (default: 5)
   */
  constructor(maxFPS: number = 5) {
    this.minFrameInterval = 1000 / maxFPS; // Convert FPS to milliseconds
  }

  /**
   * Check if enough time has passed since last frame
   * @returns true if frame should be processed, false if should be skipped
   */
  shouldProcessFrame(): boolean {
    const currentTime = Date.now();
    const timeSinceLastFrame = currentTime - this.lastFrameTime;

    if (timeSinceLastFrame >= this.minFrameInterval) {
      this.lastFrameTime = currentTime;
      return true;
    }
    
    return false;
  }

  /**
   * Reset the frame limiter (useful when starting/stopping detection)
   */
  reset(): void {
    this.lastFrameTime = 0;
  }

  /**
   * Update the maximum FPS
   */
  setMaxFPS(maxFPS: number): void {
    this.minFrameInterval = 1000 / maxFPS;
  }

  /**
   * Get current effective FPS
   */
  getCurrentFPS(): number {
    return 1000 / this.minFrameInterval;
  }
}

/**
 * Recommended FPS settings for different detection types:
 * - Helmet Detection: 5-10 FPS (real-time monitoring)
 * - Loitering Detection: 3-5 FPS (slow-moving people)
 * - Production Counter: 10-15 FPS (fast-moving objects on conveyor)
 * - Attendance System: 2-3 FPS (face recognition is expensive)
 */
export const RECOMMENDED_FPS = {
  HELMET: 8,
  LOITERING: 4,
  PRODUCTION: 12,
  ATTENDANCE: 2
};
