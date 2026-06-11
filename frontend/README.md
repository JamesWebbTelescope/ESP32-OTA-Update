# ESP32 OTA Update Frontend

A Python Flask-based web interface for managing and deploying firmware updates to ESP32 devices via Over-The-Air (OTA) updates.

## Features

- **Device Discovery**: Automatically scan your local network for ESP32 devices running the OTA server
- **Firmware Management**: Upload, organize, and manage your ESP32 firmware files
- **Easy Deployment**: Deploy firmware to one or multiple devices with a few clicks
- **Real-time Status**: Monitor upload progress and device status
- **History Tracking**: Keep track of all firmware uploads with timestamps and status
- **REST API**: Programmatic access to device management and upload functionality

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- ESP32 devices running the OTA server firmware

## Installation

1. **Clone or download this frontend folder**

2. **Install dependencies**
   ```bash
   cd frontend
   pip install -r requirements.txt
   ```

3. **Optional dependencies**
   ```bash
   # For advanced network scanning
   pip install python-nmap
   
   # For environment variables
   pip install python-dotenv
   ```

## Quick Start

1. **Start the frontend server**
   ```bash
   python app.py
   ```

2. **Open your browser**
   Navigate to `http://localhost:5000`

3. **Scan for devices**
   Click "Scan Network" to discover ESP32 devices on your local network

4. **Upload firmware**
   - Upload your compiled `.bin` firmware files
   - Select a device and upload the firmware

## Configuration

### Environment Variables

Create a `.env` file in the frontend folder to override default settings:

```bash
# Server settings
FLASK_SECRET_KEY=your-secret-key-here
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=true

# Default ESP32 credentials
ESP32_DEFAULT_USERNAME=admin
ESP32_DEFAULT_PASSWORD=admin123
ESP32_DEFAULT_PORT=80

# Upload settings
MAX_UPLOAD_SIZE=52428800  # 50MB
UPLOAD_FOLDER=./uploads
FIRMWARE_FOLDER=./firmware
```

## Usage

### Dashboard
The main dashboard shows:
- Quick statistics (connected devices, recent uploads)
- Device discovery and management
- Recent upload history
- Quick action buttons

### Adding Devices

1. **Automatic Discovery**: Click "Scan Network" to automatically find ESP32 devices
2. **Manual Addition**: Enter the IP address, hostname, port, and credentials manually

### Uploading Firmware

1. Select a device from the dashboard
2. Click "Upload Firmware"
3. Choose your `.bin` file
4. Click "Upload & Update Device"
5. Wait for the upload to complete (device will restart automatically)

### Firmware Library

- Upload firmware files for easy management
- Organize multiple versions
- Download or delete firmware files
- Quick access for deployment to multiple devices

## API Endpoints

### GET /api/devices
Get a list of all configured devices

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

### GET /api/device/<ip>/info
Get detailed information about a specific device

**Response:**
```json
{
    "ip": "192.168.1.100",
    "hostname": "esp32-ota.local",
    "port": 80,
    "username": "admin",
    "online": true,
    "version": "1.0.0",
    "info": {
        "free_heap": 245760,
        "sketch_size": 1048576,
        "free_sketch_space": 2097152
    }
}
```

### POST /api/upload
Programmatically upload firmware to a device

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

**Response:**
```json
{
    "success": true,
    "message": "Upload successful"
}
```

## ESP32 Backend Setup

The ESP32 must be running the companion OTA server firmware. The ESP32 code should:

1. Start a web server on port 80
2. Implement the `/update` endpoint for multipart form uploads
3. Implement the `/ota` endpoint for raw binary uploads
4. Support HTTP Basic Authentication
5. Provide a `/info` endpoint for device information

See the `src/main.cpp` file in the parent directory for a complete implementation.

## Troubleshooting

### Devices not found during scan
- Ensure ESP32 devices are on the same network
- Check that the devices are running the OTA server firmware
- Verify WiFi connectivity on the ESP32
- Try adding devices manually using their IP address

### Upload failures
- Check that the firmware file is valid (.bin format)
- Verify device credentials (username/password)
- Ensure sufficient memory on the ESP32
- Check the serial monitor on the ESP32 for error messages

### Connection issues
- Verify network connectivity
- Check firewall settings
- Ensure port 80 is open on the ESP32
- Try accessing the ESP32 web interface directly in your browser

## Security Considerations

1. **Change default credentials**: Update the username and password in both the ESP32 firmware and frontend configuration
2. **Use HTTPS**: For production use, consider setting up HTTPS with a reverse proxy
3. **Network segmentation**: Keep IoT devices on a separate network segment
4. **Access control**: Restrict access to the frontend server

## Building ESP32 Firmware

To build firmware for your ESP32:

1. Install PlatformIO
2. Configure `platformio.ini` with your board settings
3. Build the project
4. Upload to your ESP32 via USB initially
5. Subsequent updates can be done over-the-air via this frontend

## Project Structure

```
frontend/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── templates/
    ├── base.html       # Base HTML template
    ├── index.html      # Dashboard page
    ├── upload.html     # Firmware upload page
    └── firmware.html    # Firmware library page
```

## License

This project is provided as-is for educational and development purposes. Feel free to modify and distribute according to your needs.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Submit a pull request

## Support

For issues or questions, please refer to the ESP32 Arduino core documentation and the Flask documentation.
