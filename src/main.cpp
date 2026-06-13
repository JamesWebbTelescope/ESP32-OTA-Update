#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <Update.h>

// Configuration - Update these values
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* host = "esp32-ota";
const int httpPort = 80;
const int otaPort = 8080;

WebServer server(httpPort);
WebServer otaServer(otaPort);

// LED pin for status indication
const int ledPin = LED_BUILTIN;

// Authentication (optional but recommended)
const char* www_username = "admin";
const char* www_password = "admin123";

// Current firmware version
const String firmwareVersion = "1.0.0";
const String firmwareBuildDate = __DATE__;

// Helper function for authentication
bool checkAuth(WebServer &server) {
  return server.authenticate(www_username, www_password);
}

// Request authentication for protected routes
void requestAuth(WebServer &server) {
  server.requestAuthentication(BASIC_AUTH, "OTA Update", "Authentication required");
}

// Format bytes to human readable string
String formatBytes(size_t bytes) {
  if (bytes < 1024) {
    return String(bytes) + " B";
  } else if (bytes < (1024 * 1024)) {
    return String(bytes / 1024.0) + " KB";
  } else if (bytes < (1024 * 1024 * 1024)) {
    return String(bytes / 1024.0 / 1024.0) + " MB";
  } else {
    return String(bytes / 1024.0 / 1024.0 / 1024.0) + " GB";
  }
}

// Handle root route
void handleRoot() {
  if (!checkAuth(server)) {
    requestAuth(server);
    return;
  }
  
  String html = "<html><head><title>ESP32 OTA Update</title>";
  html += "<meta name='viewport' content='width=device-width, initial-scale=1.0'>";
  html += "<style>body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }";
  html += ".info { background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 10px 0; }";
  html += ".form { background: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0; }";
  html += ".btn { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }";
  html += ".status { margin: 10px 0; padding: 10px; border-radius: 4px; }";
  html += "</style></head><body>";
  html += "<h1>ESP32 OTA Update Server</h1>";
  html += "<div class='info'>";
  html += "<h3>Device Information</h3>";
  html += "<p><strong>Hostname:</strong> " + String(host) + ".local</p>";
  html += "<p><strong>IP Address:</strong> " + WiFi.localIP().toString() + "</p>";
  html += "<p><strong>MAC Address:</strong> " + WiFi.macAddress() + "</p>";
  html += "<p><strong>Firmware Version:</strong> " + firmwareVersion + "</p>";
  html += "<p><strong>Build Date:</strong> " + firmwareBuildDate + "</p>";
  html += "<p><strong>Free Heap:</strong> " + String(ESP.getFreeHeap() / 1024) + " KB</p>";
  html += "<p><strong>Sketch Size:</strong> " + formatBytes(ESP.getSketchSize()) + "</p>";
  html += "<p><strong>Free Sketch Space:</strong> " + formatBytes(ESP.getFreeSketchSpace()) + "</p>";
  html += "</div>";
  html += "<div class='form'>";
  html += "<h3>Firmware Upload</h3>";
  html += "<form method='POST' action='/update' enctype='multipart/form-data'>";
  html += "<input type='file' name='update' accept='.bin,.bin.gz'><br><br>";
  html += "<button type='submit' class='btn'>Upload & Update</button>";
  html += "</form>";
  html += "<p><em>Note: Upload a compiled .bin file</em></p>";
  html += "</div>";
  html += "<div class='form'>";
  html += "<h3>API Endpoints</h3>";
  html += "<ul>";
  html += "<li><strong>GET /</strong> - This page</li>";
  html += "<li><strong>GET /info</strong> - JSON device info</li>";
  html += "<li><strong>POST /update</strong> - Upload firmware (multipart/form-data)</li>";
  html += "<li><strong>POST /ota</strong> - Raw firmware upload</li>";
  html += "</ul>";
  html += "</div>";
  html += "</body></html>";
  
  server.send(200, "text/html", html);
}

// Handle info endpoint (JSON)
void handleInfo() {
  if (!checkAuth(server)) {
    requestAuth(server);
    return;
  }
  
  String json = "{";
  json += "\"hostname\":\"" + String(host) + ".local\",";
  json += "\"ip\":\"" + WiFi.localIP().toString() + "\",";
  json += "\"mac\":\"" + WiFi.macAddress() + "\",";
  json += "\"version\":\"" + firmwareVersion + "\",";
  json += "\"build_date\":\"" + firmwareBuildDate + "\",";
  json += "\"free_heap\":" + String(ESP.getFreeHeap()) + ",";
  json += "\"sketch_size\":" + String(ESP.getSketchSize()) + ",";
  json += "\"free_sketch_space\":" + String(ESP.getFreeSketchSpace()) + ",";
  json += "\"chip_id\":" + String(ESP.getChipRevision()) + ",";
  json += "\"cpu_freq\":" + String(ESP.getCpuFreqMHz()) + 
  json += "}";
  
  server.send(200, "application/json", json);
}

// Handle firmware update via web form
void handleUpdate() {
  if (!checkAuth(server)) {
    requestAuth(server);
    return;
  }
  
  String response = "<html><head><title>Update Status</title>";
  response += "<meta http-equiv='refresh' content='5; url=/'>";
  response += "<style>body { font-family: Arial; max-width: 800px; margin: 0 auto; padding: 20px; }</style>";
  response += "</head><body><h1>Firmware Update</h1>";
  
  if (Update.hasError()) {
    response += "<div style='color: red;'>";
    response += "<p><strong>Update FAILED!</strong></p>";
    response += "<p>Error: " + String(Update.errorString()) + "</p>";
    response += "</div>";
  } else {
    response += "<div style='color: green;'>";
    response += "<p><strong>Update Successful!</strong></p>";
    response += "<p>Device will restart in 5 seconds...</p>";
    response += "</div>";
  }
  
  response += "<p><a href='/'>Back to home</a></p>";
  response += "</body></html>";
  
  server.send(200, "text/html", response);
  
  // Restart after a short delay if update was successful
  if (!Update.hasError()) {
    delay(5000);
    ESP.restart();
  }
}

// Handle raw OTA upload
void handleOTAUpload() {
  if (!checkAuth(otaServer)) {
    otaServer.send(401, "text/plain", "Unauthorized");
    return;
  }
  
  if (otaServer.uri() != "/ota") {
    otaServer.send(404, "text/plain", "Not found");
    return;
  }
  
  if (otaServer.method() == HTTP_POST) {
    // Handle raw binary upload
    if (Update.begin(UPDATE_SIZE_UNKNOWN)) {
      size_t written = 0;
      while (otaServer.client().connected()) {
        if (otaServer.client().available()) {
          uint8_t buffer[1024];
          size_t len = otaServer.client().read(buffer, sizeof(buffer));
          if (len > 0) {
            written += Update.write(buffer, len);
          }
        }
      }
      if (Update.end(true)) {
        otaServer.send(200, "text/plain", "Update successful, restarting...");
        delay(1000);
        ESP.restart();
      } else {
        otaServer.send(500, "text/plain", "Update error: " + String(Update.errorString()));
      }
    } else {
      otaServer.send(500, "text/plain", "Update begin failed: " + String(Update.errorString()));
    }
  } else {
    otaServer.send(405, "text/plain", "Method not allowed");
  }
}

// Handle update upload from form
void handleUpdateUpload() {
  if (!checkAuth(server)) {
    requestAuth(server);
    return;
  }
  
  HTTPUpload& upload = server.upload();
  
  if (upload.status == UPLOAD_FILE_START) {
    Serial.setDebugOutput(true);
    Serial.printf("Update: %s\n", upload.filename.c_str());
    
    if (!Update.begin(UPDATE_SIZE_UNKNOWN)) {
      Serial.println("Update begin failed");
      Update.printError(Serial);
    }
  } else if (upload.status == UPLOAD_FILE_WRITE) {
    if (Update.write(upload.buf, upload.currentSize) != upload.currentSize) {
      Serial.println("Update write failed");
      Update.printError(Serial);
    }
  } else if (upload.status == UPLOAD_FILE_END) {
    if (Update.end(true)) {
      Serial.println("Update finished");
      Serial.printf("Total size: %u\n", upload.totalSize);
    } else {
      Serial.println("Update error");
      Update.printError(Serial);
    }
    Serial.setDebugOutput(false);
  } else if (upload.status == UPLOAD_FILE_ABORTED) {
    Update.end();
    Serial.println("Update aborted");
  }
  
  delay(0);
}

// Handle 404
void handleNotFound() {
  String message = "File Not Found\n\n";
  message += "URI: ";
  message += server.uri();
  message += "\nMethod: ";
  message += (server.method() == HTTP_GET) ? "GET" : "POST";
  message += "\nArguments: ";
  message += server.args();
  message += "\n";
  
  for (uint8_t i = 0; i < server.args(); i++) {
    message += " " + server.argName(i) + ": " + server.arg(i) + "\n";
  }
  
  server.send(404, "text/plain", message);
}

// Setup WiFi connection
void setupWiFi() {
  Serial.println("");
  Serial.print("Connecting to ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  WiFi.setHostname(host);
  
  // Blink LED while connecting
  pinMode(ledPin, OUTPUT);
  int attempts = 0;
  
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    digitalWrite(ledPin, HIGH);
    delay(250);
    digitalWrite(ledPin, LOW);
    delay(250);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("");
    Serial.println("WiFi connection failed!");
    Serial.println("Starting Access Point mode...");
    
    // Start as Access Point
    WiFi.mode(WIFI_AP);
    WiFi.softAP("ESP32-OTA-AP", "password123");
    IPAddress apIP = WiFi.softAPIP();
    Serial.print("AP IP address: ");
    Serial.println(apIP);
    digitalWrite(ledPin, HIGH);
  } else {
    Serial.println("");
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    
    // Start mDNS
    if (!MDNS.begin(host)) {
      Serial.println("Error setting up MDNS responder!");
    } else {
      Serial.println("mDNS responder started");
      MDNS.addService("http", "tcp", httpPort);
      MDNS.addService("ota", "tcp", otaPort);
    }
    
    digitalWrite(ledPin, LOW);
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("");
  Serial.println("ESP32 OTA Update Server");
  Serial.println("Firmware Version: " + firmwareVersion);
  Serial.println("Build Date: " + firmwareBuildDate);
  
  // Initialize WiFi
  setupWiFi();
  
  // Configure server routes
  server.on("/", HTTP_GET, handleRoot);
  server.on("/info", HTTP_GET, handleInfo);
  server.on("/update", HTTP_GET, handleUpdate);
  server.on("/update", HTTP_POST, []() {
    if (!checkAuth(server)) {
      requestAuth(server);
      return;
    }
    server.send(200, "text/html", 
      "<html><body><h1>Upload Firmware</h1>"
      "<form method='POST' action='/update' enctype='multipart/form-data'>"
      "<input type='file' name='update' accept='.bin'><br>"
      "<button type='submit'>Upload</button>"
      "</form></body></html>");
  }, handleUpdateUpload);
  
  server.onNotFound(handleNotFound);
  
  // OTA Server on separate port
  otaServer.on("/ota", HTTP_POST, handleOTAUpload);
  otaServer.onNotFound([]() {
    otaServer.send(404, "text/plain", "OTA endpoint not found");
  });
  
  // Start servers
  server.begin();
  otaServer.begin();
  
  Serial.println("HTTP server started on port " + String(httpPort));
  Serial.println("OTA server started on port " + String(otaPort));
  Serial.println("Ready for OTA updates!");
}

void loop() {
  server.handleClient();
  otaServer.handleClient();
  //MDNS.update();
  
  // Heartbeat LED
  static unsigned long lastBlink = 0;
  if (millis() - lastBlink > 2000) {
    lastBlink = millis();
    digitalWrite(ledPin, !digitalRead(ledPin));
  }
}
