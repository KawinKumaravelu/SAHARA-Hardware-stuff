#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>

// ===== WiFi Credentials =====
const char* ssid = "kawin";
const char* password = "12345678";

// ===== Web Server =====
WebServer server(80);

// ===== Servo Pins =====
const int servo1Pin = 13; // Pan
const int servo2Pin = 12; // Tilt

// ===== Relay Pins =====
const int relayBuzzer = 26; // M1 - Buzzer
const int relayPump   = 27; // M2 - Pump
const int relayFlash  = 25; // M3 - LED Flash

// ===== Servo Objects =====
Servo servo1;
Servo servo2;

// ===== Servo Positions =====
int servo1Pos = 90;
int servo2Pos = 90;
const int servoMin = 0;
const int servoMax = 180;

// ===== Movement Flags =====
bool moveLeft = false;
bool moveRight = false;
bool moveUp = false;
bool moveDown = false;

// ===== Flash Control =====
bool flashOn = false;
unsigned long previousMillis = 0;
const long flashInterval = 1000; // 1 second toggle

// ===== Move Servos =====
void moveServos() {
  if (moveLeft) {
    servo1Pos = max(servoMin, servo1Pos - 1);
    servo1.write(servo1Pos);
  }
  if (moveRight) {
    servo1Pos = min(servoMax, servo1Pos + 1);
    servo1.write(servo1Pos);
  }
  if (moveUp) {
    servo2Pos = min(servoMax, servo2Pos + 1);
    servo2.write(servo2Pos);
  }
  if (moveDown) {
    servo2Pos = max(servoMin, servo2Pos - 1);
    servo2.write(servo2Pos);
  }
}

// ===== Handle Servo Commands =====
void handleMove() {
  if (server.hasArg("dir") && server.hasArg("action")) {
    String dir = server.arg("dir");
    String action = server.arg("action");
    bool state = (action == "start");

    if (dir == "left") moveLeft = state;
    else if (dir == "right") moveRight = state;
    else if (dir == "up") moveUp = state;
    else if (dir == "down") moveDown = state;

    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "text/plain", "OK");
  } else {
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(400, "text/plain", "Missing arguments");
  }
}

// ===== Handle Buzzer =====
void handleBuzzer() {
  if (server.hasArg("state")) {
    String state = server.arg("state");
    digitalWrite(relayBuzzer, state == "on" ? LOW : HIGH);
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "text/plain", "Buzzer " + state);
  }
}

// ===== Handle Pump =====
void handlePump() {
  if (server.hasArg("state")) {
    String state = server.arg("state");
    digitalWrite(relayPump, state == "on" ? LOW : HIGH);
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "text/plain", "Pump " + state);
  }
}

// ===== Handle Flash Alert =====
void handleFlash() {
  if (server.hasArg("state")) {
    String state = server.arg("state");
    flashOn = (state == "on");
    if (!flashOn) {
      digitalWrite(relayFlash, HIGH); // Turn OFF when stopped
    }
    server.sendHeader("Access-Control-Allow-Origin", "*");
    server.send(200, "text/plain", "Flash " + state);
  }
}

// ===== Setup =====
void setup() {
  Serial.begin(115200);

  servo1.attach(servo1Pin);
  servo2.attach(servo2Pin);
  servo1.write(servo1Pos);
  servo2.write(servo2Pos);

  pinMode(relayBuzzer, OUTPUT);
  pinMode(relayPump, OUTPUT);
  pinMode(relayFlash, OUTPUT);

  digitalWrite(relayBuzzer, HIGH);
  digitalWrite(relayPump, HIGH);
  digitalWrite(relayFlash, HIGH);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected!");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());

  server.on("/move", handleMove);
  server.on("/buzzer", handleBuzzer);
  server.on("/pump", handlePump);
  server.on("/flash", handleFlash);

  server.begin();
  Serial.println("HTTP server started");
}

// ===== Loop =====
void loop() {
  server.handleClient();
  moveServos();

  // Flash LED if enabled
  if (flashOn) {
    unsigned long currentMillis = millis();
    if (currentMillis - previousMillis >= flashInterval) {
      previousMillis = currentMillis;
      int state = digitalRead(relayFlash);
      digitalWrite(relayFlash, !state); // Toggle
    }
  }

  delay(10);
}
