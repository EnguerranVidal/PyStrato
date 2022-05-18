/*********
  Rui Santos
  Complete project details at https://RandomNerdTutorials.com/ttgo-lora32-sx1276-arduino-ide/
*********/

//Libraries for LoRa
#include <SPI.h>
#include <LoRa.h>

//Libraries for OLED Display
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

//define the pins used by the LoRa transceiver module
#define SCK 5
#define MISO 19
#define MOSI 27
#define SS 18
#define RST 14
#define DIO0 26

//433E6 for Asia
//866E6 for Europe
//915E6 for North America
#define BAND 433E6

//OLED pins
#define OLED_SDA 21
#define OLED_SCL 22 
#define OLED_RST 16
#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels

//packet counter
int i = 0;
unsigned long MS; 
unsigned long start;

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RST);

void setup() {
  start=millis();
  //initialize Serial Monitor
  Serial.begin(115200);

  //reset OLED display via software
  pinMode(OLED_RST, OUTPUT);
  digitalWrite(OLED_RST, LOW);
  delay(20);
  digitalWrite(OLED_RST, HIGH);

  //initialize OLED
  Wire.begin(OLED_SDA, OLED_SCL);
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3c, false, false)) { // Address 0x3C for 128x32
    Serial.println(F("SSD1306 allocation failed"));
    for(;;); // Don't proceed, loop forever
  }
  
  display.clearDisplay();
  display.setTextColor(WHITE);
  display.setTextSize(1);
  display.setCursor(0,0);
  display.print("LORA SENDER ");
  display.display();
  
  Serial.println("LoRa Sender Test");

  //SPI LoRa pins
  SPI.begin(SCK, MISO, MOSI, SS);
  //setup LoRa transceiver module
  LoRa.setPins(SS, RST, DIO0);
  
  if (!LoRa.begin(BAND)) {
    Serial.println("Starting LoRa failed!");
    while (1);
  }
  Serial.println("LoRa Initializing OK!");
  display.setCursor(0,10);
  display.print("LoRa Initializing OK!");
  display.display();
  delay(1500);
}

void loop() {
   
  Serial.print("Sending packet: ");
  MS = millis() - start;
  String hour_str = String((MS / 1000) / 3600);
  String mins_str = String(((MS / 1000) / 60) % 60);
  String secs_str = String((MS / 1000) % 60);
  if (hour_str.length() == 1){hour_str = "0" + hour_str;};
  if (mins_str.length() == 1){mins_str = "0" + mins_str;};
  if (secs_str.length() == 1){secs_str = "0" + secs_str;};
  String clock_string = hour_str + mins_str + secs_str;
  String dataA = "F4KLD-1:A" + String(i) + clock_string + "+2242-2427095606502571007152436452650331023244238012643269523641024253713709";

  //Send LoRa packet to receiver
  LoRa.beginPacket();
  LoRa.print(dataA);
  LoRa.endPacket();

  i++;
  if (i == 10){
    i = 0;
    };
  
  delay(10000);
}
