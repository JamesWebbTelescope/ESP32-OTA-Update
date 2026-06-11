/**
 * ESP32 OTA Update Server Configuration
 * 
 * This header file contains configuration options for the OTA update server.
 * Modify these settings to customize your ESP32's behavior.
 */

#ifndef OTA_CONFIG_H
#define OTA_CONFIG_H

#include <Arduino.h>

// ====================
// WiFi Configuration
// ====================

// Uncomment and modify these to use static WiFi credentials
// If not defined, the server will attempt to connect with default values
// #define WIFI_SSID "your_wifi_ssid"
// #define WIFI_PASSWORD "your_wifi_password"

// Default WiFi credentials (used if not overridden)
#define DEFAULT_WIFI_SSID "YOUR_WIFI_SSID"
#define DEFAULT_WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// Hostname for the device (used for mDNS)
#define DEVICE_HOSTNAME "esp32-ota"

// ====================
// Server Configuration
// ====================

// HTTP server port
#define HTTP_PORT 80

// OTA server port (separate for raw binary uploads)
#define OTA_PORT 8080

// ====================
// Authentication
// ====================

// Enable/disable HTTP basic authentication
#define ENABLE_AUTH true

// Default credentials
#define DEFAULT_USERNAME "admin"
#define DEFAULT_PASSWORD "admin123"

// ====================
// LED Configuration
// ====================

// Pin for status LED (use LED_BUILTIN for onboard LED)
#define STATUS_LED_PIN LED_BUILTIN

// Enable/disable status LED
#define ENABLE_STATUS_LED true

// ====================
// Firmware Version
// ====================

// Current firmware version (update this when releasing new versions)
#define FIRMWARE_VERSION "1.0.0"

// Build date (automatically set to compilation date)
#define FIRMWARE_BUILD_DATE __DATE__

// ====================
// OTA Update Settings
// ====================

// Maximum firmware size (in bytes) - 0 for unlimited
#define MAX_FIRMWARE_SIZE 0

// Enable progress reporting
#define ENABLE_UPLOAD_PROGRESS true

// Enable detailed serial debugging
#define ENABLE_SERIAL_DEBUG true

// ====================
// Network Settings
// ====================

// Enable mDNS (multicast DNS)
#define ENABLE_MDNS true

// Enable AP mode fallback if WiFi connection fails
#define ENABLE_AP_FALLBACK true

// AP mode credentials (used if WiFi connection fails)
#define AP_SSID "ESP32-OTA-AP"
#define AP_PASSWORD "password123"

// ====================
// Memory Settings
// ====================

// Minimum free heap to accept updates (in bytes)
#define MIN_FREE_HEAP_FOR_UPDATE (100 * 1024)  // 100KB

// ====================
// API Endpoints
// ====================

// Define API endpoint paths
#define API_ROOT "/"
#define API_INFO "/info"
#define API_UPDATE "/update"
#define API_OTA "/ota"

// ====================
// Feature Flags
// ====================

// Enable/disable various features
#define ENABLE_WEB_INTERFACE true
#define ENABLE_JSON_API true
#define ENABLE_OTA_ENDPOINT true
#define ENABLE_MULTIPART_UPLOAD true

#endif // OTA_CONFIG_H
