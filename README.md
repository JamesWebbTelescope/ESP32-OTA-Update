# ESP32 OTA Update System

A complete Over-The-Air (OTA) update solution for ESP32 devices, consisting of a C++ backend server running on the ESP32 and a Python Flask frontend for managing firmware deployments.

## Overview

This project provides a comprehensive OTA update system that allows you to:

- **Wirelessly update** ESP32 devices without physical access
- **Manage multiple devices** from a central web interface
- **Track upload history** and device status
- **Discover devices** automatically on your local network
- **Deploy firmware** to single or multiple devices

## Architecture

```
+------------------+     +-------------------+     +------------------+
|  Your Computer   |     |  Local Network    |     |   ESP32 Device   |
|                  |     |                   |     |                  |
|  +------------+  |     |                   |     |  +------------+  |
|  | Flask      |--+--->|   WiFi/Ethernet   |--+--->|  | OTA Server  |  |
|  | Frontend   |  |     |                   |     |  | (C++)       |  |
|  +------------+  |     |                   |     |  +------------+  |
|                  |     |                   |     |                  |
|  +------------+  |     |                   |     |  +------------+  |
|  | Web Browser|  |     |                   |     |  | Your App    |  |
|  +------------+  |     |                   |     |  +------------+  |
+------------------+     +-------------------+     +------------------+
```

## Components

### 1. ESP32 Backend Server (C++)

A web server that runs on the ESP32 and provides:

- **HTTP Web Server**: Serves a web interface and API endpoints
- **OTA Update Handler**: Accepts firmware updates via HTTP POST
- **Device Information**: Provides JSON API with device stats
- **Authentication**: HTTP Basic Auth for security
- **mDNS Support**: Access devices via `.local` hostnames
- **Fallback AP Mode**: Creates a hotspot if WiFi connection fails

### 2. Python Flask Frontend

A web-based management interface that provides:

- **Dashboard**: Overview of all connected devices
- **Device Discovery**: Automatic network scanning for ESP32 devices
- **Firmware Library**: Central repository for managing `.bin` files
- **Upload Interface**: Easy firmware deployment to devices
- **History Tracking**: Log of all upload operations
- **REST API**: Programmatic access to functionality

## Quick Start

### Prerequisites

#### For ESP32 Backend:
- ESP32 development board (Arduino Nano ESP32, ESP32 DevKit, etc.)
- PlatformIO or Arduino IDE
- USB cable for initial setup

#### For Python Frontend:
- Python 3.7 or higher
- pip package manager
- Network connectivity to ESP32 devices

### Step 1: Configure ESP32 Firmware

1. Open `src/main.cpp` in your IDE
2. Update the WiFi credentials:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
3. Optionally change authentication credentials:
   ```cpp
   const char* www_username = "admin";
   const char* www_password = "admin123";
   ```

### Step 2: Upload ESP32 Firmware

#### Using PlatformIO:
```bash
# Navigate to project directory
cd "OTA Update"

# Build the project
pio run

# Upload via USB (for first deployment)
pio run --target upload

# Monitor serial output
pio run --target monitor
```

#### Using Arduino IDE:
1. Open `src/main.cpp`
2. Select your ESP32 board
3. Select the correct port
4. Click Upload

### Step 3: Start the Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the Flask server:
   ```bash
   python app.py
   ```

4. Open your browser to `http://localhost:5000`

### Step 4: Discover and Update Devices

1. Click "Scan Network" to find ESP32 devices
2. Click "Upload Firmware" on a device
3. Select your `.bin` file
4. Click "Upload & Update Device"

## Project Structure

```
OTA Update/
├── README.md                    # This file
├── platformio.ini              # PlatformIO configuration
├── .gitignore                  # Git ignore rules
│
├── include/
│   ├── README                   # PlatformIO include info
│   └── ota_config.h            # Configuration header for ESP32
│
├── src/
│   └── main.cpp                # ESP32 backend server code
│
├── lib/
│   └── README                   # PlatformIO library info
│
├── test/
│
└── frontend/                    # Python Flask frontend
    ├── app.py                  # Main Flask application
    ├── requirements.txt        # Python dependencies
    ├── README.md               # Frontend documentation
    ├── .gitignore              # Frontend git ignore
    └── templates/
        ├── base.html           # Base HTML template
        ├── index.html          # Dashboard page
        ├── upload.html         # Firmware upload page
        └── firmware.html        # Firmware library page
```

## Configuration

### ESP32 Backend Configuration

Edit `src/main.cpp` or use `include/ota_config.h` for advanced configuration:

**WiFi Settings:**
```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* host = "esp32-ota";  // mDNS hostname
```

**Server Ports:**
```cpp
const int httpPort = 80;      // Web interface port
const int otaPort = 8080;    // OTA upload port
```

**Authentication:**
```cpp
const char* www_username = "admin";
const char* www_password = "admin123";
```

**Version:**
```cpp
const String firmwareVersion = "1.0.0";
```

### PlatformIO Configuration

Edit `platformio.ini` to match your board:

```ini
[env:arduino_nano_esp32]
platform = espressif32
board = arduino_nano_esp32
framework = arduino

; Required libraries
lib_deps =
    WiFi
    WebServer
    ESPmDNS
    Update
```

### Frontend Configuration

Edit `frontend/app.py` or create a `.env` file:

```bash
# Default credentials for ESP32 devices
ESP32_DEFAULT_USERNAME=admin
ESP32_DEFAULT_PASSWORD=admin123
ESP32_DEFAULT_PORT=80

# Server settings
FLASK_SECRET_KEY=your-secret-key
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

## API Reference

### ESP32 Backend API

#### GET /
Web interface with device information and upload form

#### GET /info
Returns device information in JSON format

**Response:**
```json
{
    "hostname": "esp32-ota.local",
    "ip": "192.168.1.100",
    "mac": "AA:BB:CC:DD:EE:FF",
    "version": "1.0.0",
    "build_date": "Jun 11 2026",
    "free_heap": 245760,
    "sketch_size": 1048576,
    "free_sketch_space": 2097152,
    "chip_id": 12345678,
    "cpu_freq": 240
}
```

#### POST /update
Upload firmware via multipart form data

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Form field: `update` (file)
- Authentication: HTTP Basic Auth required

**Response:**
- 200: Success (device will restart)
- 401: Unauthorized
- 500: Update error

#### POST /ota
Raw binary upload for direct OTA

**Request:**
- Method: POST
- Content-Type: application/octet-stream
- Body: Raw firmware binary
- Authentication: HTTP Basic Auth required

**Response:**
- 200: Success (device will restart)
- 401: Unauthorized
- 500: Update error

### Frontend API

#### GET /api/devices
Get list of all configured devices

**Response:**
```json
{
    "devices": [
        {
            "ip": "192.168.1.100",
            "hostname": "esp32-ota.local",
            "port": 80,
            "online": true,
            "version": "1.0.0"
        }
    ]
}
```

#### GET /api/device/<ip>/info
Get detailed device information

#### POST /api/upload
Programmatically upload firmware

**Request:**
```json
{
    "device_ip": "192.168.1.100",
    "firmware_url": "http://example.com/firmware.bin",
    "port": 80,
    "username": "admin",
    "password": "admin123"
}
```

## Usage Examples

### Example 1: Basic Update via Web Interface

1. Power on ESP32 with OTA firmware
2. Open `http://localhost:5000` in browser
3. Click "Scan Network"
4. Find your ESP32 in the list
5. Click "Upload Firmware"
6. Select your `.bin` file
7. Click "Upload & Update Device"

### Example 2: Using cURL for Direct Update

```bash
# Update via /update endpoint (multipart)
curl -X POST \
  -F "update=@firmware.bin" \
  -u admin:admin123 \
  http://esp32-ota.local/update

# Update via /ota endpoint (raw binary)
curl -X POST \
  --data-binary @firmware.bin \
  -u admin:admin123 \
  http://esp32-ota.local:8080/ota
```

### Example 3: Using Python for Programmatic Update

```python
import requests

# Upload firmware
url = "http://esp32-ota.local/update"
files = {'update': open('firmware.bin', 'rb')}
auth = ('admin', 'admin123')

response = requests.post(url, files=files, auth=auth)
print(f"Upload status: {response.status_code}")
```

### Example 4: Bulk Update Multiple Devices

```python
import requests
import time

devices = [
    "http://esp32-device1.local",
    "http://esp32-device2.local",
    "http://esp32-device3.local"
]

firmware = open('firmware.bin', 'rb')

for device_url in devices:
    try:
        print(f"Updating {device_url}...")
        response = requests.post(
            f"{device_url}/update",
            files={'update': firmware},
            auth=('admin', 'admin123'),
            timeout=120
        )
        print(f"  Status: {response.status_code}")
        time.sleep(5)  # Wait before next device
    except Exception as e:
        print(f"  Error: {e}")
    
    # Wait for device to restart
    time.sleep(10)
```

## Advanced Features

### Network Discovery

The frontend can automatically discover ESP32 devices on your local network using:
- mDNS (.local hostname resolution)
- TCP port scanning (port 80)
- HTTP endpoint checking (/info)

### Fallback Access Point Mode

If the ESP32 cannot connect to your WiFi network, it will automatically create an access point:
- **SSID**: `ESP32-OTA-AP`
- **Password**: `password123`
- **IP**: `192.168.4.1`

Connect to this AP to access the OTA server directly.

### Device Information

The ESP32 provides detailed information via the `/info` endpoint:
- Hostname and IP address
- MAC address
- Firmware version and build date
- Memory usage (free heap)
- Sketch size and free space
- Chip ID and CPU frequency

### Multiple Port Support

- **Port 80**: Web interface and multipart uploads
- **Port 8080**: Raw binary OTA uploads

## Security Best Practices

### 1. Change Default Credentials
Always change the default username and password in both the ESP32 firmware and frontend configuration.

**ESP32 (`src/main.cpp`):**
```cpp
const char* www_username = "your-secure-username";
const char* www_password = "your-strong-password";
```

**Frontend (`frontend/app.py`):**
```python
DEFAULT_USERNAME = "your-secure-username"
DEFAULT_PASSWORD = "your-strong-password"
```

### 2. Use Strong Passwords
- Minimum 12 characters
- Mix of upper/lower case, numbers, and special characters
- Different passwords for different devices

### 3. Network Security
- Keep IoT devices on a separate VLAN
- Use firewall rules to restrict access
- Consider using HTTPS with a reverse proxy (Nginx, Apache)

### 4. Physical Security
- Ensure physical access to ESP32 devices is controlled
- Consider tamper-evident enclosures for production devices

### 5. Firmware Signing (Advanced)
For production use, consider implementing firmware signing to prevent unauthorized updates.

## Troubleshooting

### Common Issues and Solutions

#### Issue: ESP32 won't connect to WiFi
**Solution:**
- Verify SSID and password are correct
- Check if the router is blocking the ESP32
- Try moving closer to the router
- Check serial monitor for connection errors
- Use AP fallback mode to verify ESP32 is working

#### Issue: Devices not found during scan
**Solution:**
- Ensure ESP32 is on the same network as your computer
- Verify ESP32 firmware is running and connected to WiFi
- Check firewall settings on your computer
- Try adding devices manually using their IP address
- Verify mDNS is working (try pinging `esp32-ota.local`)

#### Issue: Upload fails with authentication error
**Solution:**
- Verify username and password in frontend match ESP32 firmware
- Check for typos in credentials
- Try accessing the ESP32 web interface directly in browser
- Ensure authentication is enabled on the ESP32

#### Issue: Upload fails with HTTP 500 error
**Solution:**
- Check serial monitor on ESP32 for error details
- Ensure firmware file is valid (.bin format)
- Verify sufficient free space on ESP32
- Check that the firmware is compiled for the correct board
- Try a smaller firmware file

#### Issue: Upload hangs or times out
**Solution:**
- Check network connectivity between computer and ESP32
- Try reducing the upload chunk size
- Use a wired connection if possible
- Move closer to the router
- Try uploading via serial (USB) instead

#### Issue: ESP32 restarts but new firmware doesn't run
**Solution:**
- Check serial monitor during restart
- Verify the upload completed successfully
- Ensure the firmware file is not corrupted
- Check that the partition table is correct
- Try uploading via USB to verify the firmware works

### Debugging Tools

#### ESP32 Serial Monitor
```bash
# Using PlatformIO
pio run --target monitor

# Using screen (Linux/Mac)
screen /dev/ttyUSB0 115200

# Using PuTTY (Windows)
# Open PuTTY, select serial port, set baud rate to 115200
```

#### Network Tools
```bash
# Ping ESP32
ping esp32-ota.local

# Check if port 80 is open
nc -zv esp32-ota.local 80

# Get device info via cURL
curl -u admin:admin123 http://esp32-ota.local/info

# Test upload via cURL
curl -v -X POST -F "update=@firmware.bin" -u admin:admin123 http://esp32-ota.local/update
```

## Building Custom Firmware

### Using PlatformIO

1. Create a new PlatformIO project or use this one
2. Add your application code
3. Configure `platformio.ini` for your board
4. Build and upload:
   ```bash
   pio run      # Build
   pio run -t upload  # Upload via USB
   ```

### Using Arduino IDE

1. Install ESP32 board support (via Boards Manager)
2. Select your ESP32 board
3. Select the correct port
4. Include the necessary libraries:
   ```cpp
   #include <WiFi.h>
   #include <WebServer.h>
   #include <ESPmDNS.h>
   #include <Update.h>
   ```
5. Compile and upload

### Creating OTA-Compatible Firmware

For OTA updates to work, your firmware must:
1. Use the same partition table as the original firmware
2. Be compiled with the correct board configuration
3. Have enough free space for the update
4. Not use features that prevent OTA (certain PSRAM configurations)

## Partition Table

The default partition table should include:
- System partitions (bootloader, partitions, etc.)
- OTA data partitions
- Application partitions (at least 2 for OTA)

Example partition table (CSV format):
```csv
# Name,   Type, SubType, Offset,  Size, Flags
nvs,      data, nvs,     0x9000,  0x5000,
phy_init, data, phy,     0xe000,  0x1000,
factory,  app,  factory, 0x10000, 1M,
storage,  data, 0x99,    0x110000, 1M,
ota_0,    app,  ota_0,   0x210000, 1M,
ota_1,    app,  ota_1,   0x310000, 1M,
```

## Performance Optimization

### For ESP32 Backend:
- Reduce debug output in production
- Minimize memory usage in handlers
- Use smaller buffer sizes if needed
- Disable unused features

### For Frontend:
- Use production mode for Flask (`FLASK_DEBUG=false`)
- Implement caching for static files
- Use a production WSGI server (gunicorn, uwsgi) for deployment
- Consider using a database for device management instead of in-memory storage

## Deployment Scenarios

### Scenario 1: Development
- ESP32 connected via USB for initial setup
- Frontend running locally on development machine
- Direct network connection to ESP32

### Scenario 2: Small Office
- Multiple ESP32 devices on office network
- Frontend running on a dedicated machine or Raspberry Pi
- All devices accessible via local network

### Scenario 3: Production
- ESP32 devices distributed across multiple locations
- Frontend hosted on a central server
- Devices use cellular or VPN for remote access
- HTTPS with authentication for security

### Scenario 4: IoT Fleet Management
- Hundreds or thousands of ESP32 devices
- Frontend integrated with cloud services (AWS, Azure, GCP)
- Automated update scheduling
- Device health monitoring
- Rollback capabilities

## Extending the System

### Adding New Features to ESP32

1. **Custom Endpoints**: Add new routes to the WebServer
2. **Additional Sensors**: Integrate with sensors and expose data via API
3. **Configuration Management**: Add endpoints to manage device configuration
4. **Remote Control**: Add endpoints to control device outputs

### Adding New Features to Frontend

1. **Device Groups**: Organize devices into groups for bulk operations
2. **Scheduled Updates**: Schedule firmware updates for specific times
3. **Rollback**: Implement firmware rollback capability
4. **Monitoring**: Add real-time monitoring of device status
5. **Notifications**: Email or push notifications for update events
6. **User Management**: Multi-user support with different permissions

### Integration with Other Systems

1. **Cloud Services**: Connect to AWS IoT, Azure IoT Hub, or Google Cloud IoT
2. **CI/CD Pipelines**: Integrate with GitHub Actions, GitLab CI, or Jenkins
3. **Monitoring Systems**: Prometheus, Grafana, or ELK stack
4. **Alerting Systems**: PagerDuty, Slack, or Microsoft Teams

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is provided as-is for educational and development purposes. Feel free to modify and distribute according to your needs.

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the ESP32 Arduino core documentation
- Consult the Flask documentation
- Search online forums and communities

## Resources

### ESP32 Resources
- [Espressif ESP32 Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/)
- [ESP32 Arduino Core](https://github.com/espressif/arduino-esp32)
- [PlatformIO ESP32](https://docs.platformio.org/en/latest/frames/esp32.html)

### OTA Resources
- [ESP32 OTA Update Guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/ota.html)
- [ESP32 OTA with Arduino](https://github.com/espressif/arduino-esp32/blob/master/doc/ota_updates.md)

### Flask Resources
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask Mega Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)

## Appendix

### A. Common ESP32 Boards

| Board Name | PlatformIO ID | Notes |
|------------|---------------|-------|
| Arduino Nano ESP32 | arduino_nano_esp32 | Official Arduino board |
| ESP32 DevKitC | esp32dev | Most common development board |
| ESP32 WROOM 32 | esp32dev | Generic ESP32 module |
| ESP32-S2 | esp32-s2-devkitm-1 | ESP32-S2 variant |
| ESP32-C3 | esp32-c3-devkitm-1 | ESP32-C3 variant |
| NodeMCU-32S | nodemcu-32s | NodeMCU style board |

### B. Required Libraries

**ESP32 Backend:**
- WiFi: Built-in ESP32 library
- WebServer: Built-in ESP32 library
- ESPmDNS: Built-in ESP32 library
- Update: Built-in ESP32 library

**Python Frontend:**
- Flask: Web framework
- requests: HTTP client
- netifaces: Network interface information
- Werkzeug: WSGI utilities

### C. Default Ports

| Service | Port | Protocol | Description |
|---------|------|----------|-------------|
| HTTP | 80 | TCP | Web interface and multipart uploads |
| OTA | 8080 | TCP | Raw binary OTA uploads |
| mDNS | 5353 | UDP | Multicast DNS for .local hostnames |
| Frontend | 5000 | TCP | Flask web interface |

### D. Default Credentials

| Component | Username | Password |
|-----------|----------|----------|
| ESP32 Web Interface | admin | admin123 |
| ESP32 OTA Endpoint | admin | admin123 |
| Frontend (if configured) | admin | (set in configuration) |

### E. File Size Limits

- Maximum firmware size: Limited by ESP32 flash size (typically 4MB-16MB)
- Frontend upload limit: 50MB (configurable)
- ESP32 free space requirement: At least 1.5x firmware size for OTA

## Version History

- **v1.0.0** (2026-06-11): Initial release
  - ESP32 OTA server with web interface
  - Python Flask frontend
  - Device discovery and management
  - Firmware library
  - Upload history tracking
