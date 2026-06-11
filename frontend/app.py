#!/usr/bin/env python3
"""
ESP32 OTA Update Frontend
========================

A Flask-based web interface for uploading firmware to ESP32 devices.
This frontend provides a user-friendly interface to discover ESP32 devices
on the network and upload new firmware via OTA (Over-The-Air) updates.

Usage:
    python app.py
    
Then open http://localhost:5000 in your browser.

Requirements:
    - Python 3.7+
    - Flask
    - requests
    - python-nmap (optional, for network scanning)
"""

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import os
import requests
import json
import threading
import time
from datetime import datetime
import socket
import ipaddress
import netifaces
from functools import wraps

app = Flask(__name__)
app.secret_key = 'esp32-ota-secret-key-change-this'

# Configuration
UPLOAD_FOLDER = 'uploads'
FIRMWARE_FOLDER = 'firmware'
ALLOWED_EXTENSIONS = {'bin', 'bin.gz'}

# ESP32 defaults
DEFAULT_ESP32_PORT = 80
DEFAULT_OTA_PORT = 8080
DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWORD = 'admin123'

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FIRMWARE_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['FIRMWARE_FOLDER'] = FIRMWARE_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

# In-memory database of discovered devices
devices = []
upload_history = []


# Helper functions
def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_local_ip():
    """Get the local IP address of the machine."""
    try:
        # Try to get the IP address of the default interface
        gateways = netifaces.gateways()
        default_interface = gateways.get('default', {}).get(netifaces.AF_INET, [None, None])[1]
        
        if default_interface:
            addrs = netifaces.ifaddresses(default_interface)
            if netifaces.AF_INET in addrs:
                for addr_info in addrs[netifaces.AF_INET]:
                    if 'addr' in addr_info:
                        return addr_info['addr']
        
        # Fallback to socket method
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            s.connect(('192.255.255.255', 1))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def scan_network_for_esp32(start_ip='192.168.1.1', end_ip='192.168.1.254', timeout=1):
    """
    Scan the local network for ESP32 devices.
    This is a simple ping sweep - for more accurate results, use nmap.
    """
    found_devices = []
    local_ip = get_local_ip()
    
    # Extract network prefix
    try:
        network = ipaddress.IPv4Network(local_ip + '/24', strict=False)
        start = network.network_address + 1
        end = network.broadcast_address - 1
    except Exception:
        # Fallback to default range
        start = ipaddress.IPv4Address('192.168.1.1')
        end = ipaddress.IPv4Address('192.168.1.254')
    
    print(f"Scanning network from {start} to {end}")
    
    # Simple scan - check common ESP32 hostnames via mDNS
    common_hostnames = [
        'esp32', 'esp32-ota', 'esp32local', 'espressif',
        'esp32dev', 'esp32-wroom', 'nodemcu', 'esp8266'
    ]
    
    for hostname in common_hostnames:
        try:
            # Try .local suffix (mDNS)
            ip = socket.gethostbyname(hostname + '.local')
            found_devices.append({
                'ip': ip,
                'hostname': hostname + '.local',
                'type': 'mDNS',
                'port': DEFAULT_ESP32_PORT,
                'online': True
            })
        except socket.gaierror:
            pass
    
    # Quick ping sweep for ESP32 web servers
    for ip_int in range(int(start), int(end) + 1):
        ip_str = str(ipaddress.IPv4Address(ip_int))
        
        # Skip our own IP
        if ip_str == local_ip:
            continue
        
        # Check if port 80 is open (HTTP)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip_str, DEFAULT_ESP32_PORT))
            if result == 0:
                # Port is open, try to identify as ESP32
                try:
                    response = requests.get(f'http://{ip_str}/info', 
                                          timeout=timeout, 
                                          auth=(DEFAULT_USERNAME, DEFAULT_PASSWORD))
                    if response.status_code == 200:
                        data = response.json()
                        if 'hostname' in data or 'version' in data:
                            found_devices.append({
                                'ip': ip_str,
                                'hostname': data.get('hostname', ip_str),
                                'type': 'ESP32',
                                'port': DEFAULT_ESP32_PORT,
                                'online': True,
                                'info': data
                            })
                except Exception:
                    # If /info fails, just add as generic device
                    found_devices.append({
                        'ip': ip_str,
                        'hostname': ip_str,
                        'type': 'HTTP Server',
                        'port': DEFAULT_ESP32_PORT,
                        'online': True
                    })
            sock.close()
        except Exception:
            pass
    
    return found_devices


def check_esp32_device(ip, port=DEFAULT_ESP32_PORT, username=DEFAULT_USERNAME, password=DEFAULT_PASSWORD):
    """
    Check if a device at the given IP is an ESP32 with OTA capability.
    """
    try:
        response = requests.get(f'http://{ip}:{port}/info', 
                              timeout=2, 
                              auth=(username, password))
        if response.status_code == 200:
            data = response.json()
            return {
                'ip': ip,
                'port': port,
                'online': True,
                'info': data,
                'hostname': data.get('hostname', ip),
                'version': data.get('version', 'Unknown')
            }
    except Exception as e:
        pass
    
    return None


# Routes
@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html', 
                         devices=devices,
                         history=upload_history[-10:])  # Last 10 uploads


@app.route('/scan', methods=['GET'])
def scan_devices():
    """Scan for ESP32 devices on the network."""
    global devices
    
    devices = scan_network_for_esp32()
    
    # Also check any manually added devices
    for device in devices:
        if 'online' in device and device['online']:
            info = check_esp32_device(device['ip'], device.get('port', DEFAULT_ESP32_PORT))
            if info:
                device.update(info)
    
    flash(f'Found {len(devices)} devices on the network', 'success')
    return redirect(url_for('index'))


@app.route('/add_device', methods=['POST'])
def add_device():
    """Manually add a device."""
    ip = request.form.get('ip')
    hostname = request.form.get('hostname', ip)
    port = int(request.form.get('port', DEFAULT_ESP32_PORT))
    username = request.form.get('username', DEFAULT_USERNAME)
    password = request.form.get('password', DEFAULT_PASSWORD)
    
    device_info = check_esp32_device(ip, port, username, password)
    
    if device_info:
        device = {
            'ip': ip,
            'hostname': hostname,
            'port': port,
            'username': username,
            'password': password,
            'online': True,
            'info': device_info.get('info', {}),
            'version': device_info.get('version', 'Unknown')
        }
        devices.append(device)
        flash(f'Device {hostname} ({ip}) added successfully!', 'success')
    else:
        # Add anyway, but mark as offline
        device = {
            'ip': ip,
            'hostname': hostname,
            'port': port,
            'username': username,
            'password': password,
            'online': False
        }
        devices.append(device)
        flash(f'Device {hostname} added but appears offline', 'warning')
    
    return redirect(url_for('index'))


@app.route('/remove_device/<int:index>', methods=['POST'])
def remove_device(index):
    """Remove a device from the list."""
    if 0 <= index < len(devices):
        removed = devices.pop(index)
        flash(f'Removed device {removed.get("hostname", removed.get("ip", "Unknown"))}', 'success')
    return redirect(url_for('index'))


@app.route('/upload', methods=['GET', 'POST'])
def upload_firmware():
    """Upload firmware to a specific device."""
    if request.method == 'POST':
        device_index = int(request.form.get('device_index'))
        
        if device_index < 0 or device_index >= len(devices):
            flash('Invalid device selection', 'error')
            return redirect(url_for('index'))
        
        device = devices[device_index]
        
        # Check if file was uploaded
        if 'firmware' not in request.files:
            flash('No firmware file selected', 'error')
            return redirect(url_for('index'))
        
        file = request.files['firmware']
        
        if file.filename == '':
            flash('No firmware file selected', 'error')
            return redirect(url_for('index'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Save the file temporarily
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(temp_path)
            
            # Get device credentials
            ip = device['ip']
            port = device.get('port', DEFAULT_ESP32_PORT)
            username = device.get('username', DEFAULT_USERNAME)
            password = device.get('password', DEFAULT_PASSWORD)
            
            # Record upload start
            upload_record = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'device_ip': ip,
                'device_hostname': device.get('hostname', ip),
                'filename': filename,
                'size': os.path.getsize(temp_path),
                'status': 'uploading'
            }
            upload_history.append(upload_record)
            
            # Perform upload in background thread
            def upload_task():
                try:
                    update_upload_record(upload_record, 'connecting')
                    
                    # Build URL
                    url = f'http://{ip}:{port}/update'
                    
                    # Prepare multipart form data
                    files = {'update': open(temp_path, 'rb')}
                    auth = (username, password)
                    
                    update_upload_record(upload_record, 'uploading')
                    
                    response = requests.post(url, 
                                          files=files,
                                          auth=auth,
                                          timeout=120)
                    
                    if response.status_code == 200:
                        update_upload_record(upload_record, 'success')
                    else:
                        update_upload_record(upload_record, f'error: HTTP {response.status_code}')
                        
                except Exception as e:
                    update_upload_record(upload_record, f'error: {str(e)}')
                finally:
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            
            # Start upload thread
            thread = threading.Thread(target=upload_task)
            thread.start()
            
            flash(f'Upload started for {device.get("hostname", ip)}', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid file type. Please upload .bin or .bin.gz files only.', 'error')
    
    # GET request - show upload form
    return render_template('upload.html', 
                         devices=devices,
                         enumerated_devices=enumerate(devices))


@app.route('/ota_upload', methods=['POST'])
def ota_upload():
    """
    Direct OTA upload using raw binary data.
    This endpoint accepts raw firmware and uploads it to the specified device.
    """
    device_index = int(request.form.get('device_index'))
    
    if device_index < 0 or device_index >= len(devices):
        return json.dumps({'success': False, 'error': 'Invalid device selection'}), 400
    
    device = devices[device_index]
    
    if 'firmware' not in request.files:
        return json.dumps({'success': False, 'error': 'No firmware file'}), 400
    
    file = request.files['firmware']
    
    if file.filename == '' or not allowed_file(file.filename):
        return json.dumps({'success': False, 'error': 'Invalid file'}), 400
    
    # Save temporarily
    filename = secure_filename(file.filename)
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(temp_path)
    
    ip = device['ip']
    ota_port = device.get('port', DEFAULT_OTA_PORT)
    username = device.get('username', DEFAULT_USERNAME)
    password = device.get('password', DEFAULT_PASSWORD)
    
    try:
        # Read firmware data
        with open(temp_path, 'rb') as f:
            firmware_data = f.read()
        
        # Upload to ESP32 OTA endpoint
        url = f'http://{ip}:{ota_port}/ota'
        
        response = requests.post(url,
                              data=firmware_data,
                              auth=(username, password),
                              timeout=120)
        
        # Clean up
        os.remove(temp_path)
        
        if response.status_code == 200:
            return json.dumps({'success': True, 'message': 'Upload successful, device restarting'})
        else:
            return json.dumps({'success': False, 'error': f'HTTP {response.status_code}: {response.text}'}), 500
            
    except Exception as e:
        # Clean up on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return json.dumps({'success': False, 'error': str(e)}), 500


def update_upload_record(record, status):
    """Update the status of an upload record."""
    for idx, r in enumerate(upload_history):
        if (r['timestamp'] == record['timestamp'] and 
            r['device_ip'] == record['device_ip'] and
            r['filename'] == record['filename']):
            upload_history[idx]['status'] = status
            break


@app.route('/firmware')
def firmware_management():
    """Firmware file management."""
    firmware_files = []
    
    if os.path.exists(app.config['FIRMWARE_FOLDER']):
        for filename in os.listdir(app.config['FIRMWARE_FOLDER']):
            if allowed_file(filename):
                filepath = os.path.join(app.config['FIRMWARE_FOLDER'], filename)
                firmware_files.append({
                    'name': filename,
                    'size': os.path.getsize(filepath),
                    'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    return render_template('firmware.html', firmware_files=firmware_files)


@app.route('/firmware/upload', methods=['POST'])
def firmware_upload():
    """Upload firmware to the firmware library."""
    if 'firmware' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('firmware_management'))
    
    file = request.files['firmware']
    
    if file.filename == '' or not allowed_file(file.filename):
        flash('Invalid file type. Please upload .bin or .bin.gz files only.', 'error')
        return redirect(url_for('firmware_management'))
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['FIRMWARE_FOLDER'], filename)
    file.save(filepath)
    
    flash(f'Firmware {filename} uploaded successfully!', 'success')
    return redirect(url_for('firmware_management'))


@app.route('/firmware/download/<filename>')
def firmware_download(filename):
    """Download a firmware file."""
    if allowed_file(filename):
        return send_from_directory(app.config['FIRMWARE_FOLDER'], filename, as_attachment=True)
    return redirect(url_for('firmware_management'))


@app.route('/firmware/delete/<filename>', methods=['POST'])
def firmware_delete(filename):
    """Delete a firmware file."""
    filepath = os.path.join(app.config['FIRMWARE_FOLDER'], filename)
    if os.path.exists(filepath) and allowed_file(filename):
        os.remove(filepath)
        flash(f'Firmware {filename} deleted', 'success')
    return redirect(url_for('firmware_management'))


@app.route('/api/devices')
def api_devices():
    """API endpoint to get list of devices."""
    device_list = []
    for device in devices:
        device_list.append({
            'ip': device.get('ip'),
            'hostname': device.get('hostname', device.get('ip', 'Unknown')),
            'port': device.get('port', DEFAULT_ESP32_PORT),
            'online': device.get('online', False),
            'version': device.get('version', 'Unknown'),
            'type': device.get('type', 'ESP32')
        })
    return json.dumps({'devices': device_list})


@app.route('/api/device/<ip>/info')
def api_device_info(ip):
    """API endpoint to get device information."""
    for device in devices:
        if device.get('ip') == ip:
            return json.dumps(device)
    return json.dumps({'error': 'Device not found'}), 404


@app.route('/api/upload', methods=['POST'])
def api_upload():
    """API endpoint for programmatic firmware upload."""
    data = request.get_json()
    
    if not data or 'device_ip' not in data or 'firmware_url' not in data:
        return json.dumps({'success': False, 'error': 'Missing required parameters'}), 400
    
    device_ip = data['device_ip']
    firmware_url = data['firmware_url']
    port = data.get('port', DEFAULT_ESP32_PORT)
    username = data.get('username', DEFAULT_USERNAME)
    password = data.get('password', DEFAULT_PASSWORD)
    
    # Find device
    device = None
    for d in devices:
        if d.get('ip') == device_ip:
            device = d
            break
    
    if not device:
        return json.dumps({'success': False, 'error': 'Device not found'}), 404
    
    try:
        # Download firmware from URL
        response = requests.get(firmware_url, timeout=30)
        if response.status_code != 200:
            return json.dumps({'success': False, 'error': 'Failed to download firmware'}), 400
        
        # Upload to device
        upload_url = f'http://{device_ip}:{port}/update'
        files = {'update': (os.path.basename(firmware_url), response.content)}
        
        upload_response = requests.post(upload_url,
                                      files=files,
                                      auth=(username, password),
                                      timeout=120)
        
        if upload_response.status_code == 200:
            return json.dumps({'success': True, 'message': 'Upload successful'})
        else:
            return json.dumps({'success': False, 'error': f'Upload failed: HTTP {upload_response.status_code}'}), 500
            
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)}), 500


# Template context processor
@app.context_processor
def inject_globals():
    return dict(
        app_name='ESP32 OTA Update Manager',
        local_ip=get_local_ip(),
        default_username=DEFAULT_USERNAME,
        default_password='***',  # Don't expose password
        default_port=DEFAULT_ESP32_PORT
    )


if __name__ == '__main__':
    print("=" * 60)
    print("ESP32 OTA Update Frontend")
    print("=" * 60)
    print(f"Starting on http://{get_local_ip()}:5000")
    print(f"Uploads folder: {os.path.abspath(UPLOAD_FOLDER)}")
    print(f"Firmware folder: {os.path.abspath(FIRMWARE_FOLDER)}")
    print("=" * 60)
    
    # Create folders if they don't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(FIRMWARE_FOLDER, exist_ok=True)
    
    # Add a sample device for testing
    if len(devices) == 0:
        devices.append({
            'ip': 'esp32-ota.local',
            'hostname': 'esp32-ota.local',
            'port': DEFAULT_ESP32_PORT,
            'username': DEFAULT_USERNAME,
            'password': DEFAULT_PASSWORD,
            'online': False,
            'type': 'Sample (scan to find real devices)'
        })
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
