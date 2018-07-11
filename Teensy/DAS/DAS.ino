#include "SparkFunLSM6DS3.h"
#include "Wire.h"
#include <TinyGPS++.h>
#include <SoftwareSerial.h>
#include "SPI.h"

/* Debug Mode */
#define DEBUG // Comment this line out if not using debug mode

#ifdef DEBUG
  #define DEBUG_PRINTLN(input_text) Serial.println(input_text);
  #define DEBUG_PRINT_DEC(input_text, text_length) Serial.print(input_text, text_length);
  #define DEBUG_PRINT(input_text) Serial.print(input_text);
#else
   #define DEBUG_PRINTLN(input_text)
  #define DEBUG_PRINT_DEC(input_text, text_length)
  #define DEBUG_PRINT(input_text)
#endif

// Pin Values
static const int REED_PIN = 2; // Pin connected to reed switch
static const int GREEN_LED = 3, RED_LED = 4;
static const int POT_PIN = 0;
static const int GPS_RXPin = 7, GPS_TXPin = 8;
#define RPISERIAL Serial2 // Pin 9 (RX) & PIN 10 (TX) for Teensy LC
//const int SDchipSelect = 10;
const int LMS6DS3chipSelect = 6;

// Set up Accelerometer
LSM6DS3 myIMU(SPI_MODE, LMS6DS3chipSelect);

// GPS Variables & Setup
static const uint32_t GPS_Baud = 9600;
TinyGPSPlus gps;
SoftwareSerial ss(GPS_RXPin, GPS_TXPin);

// Raspberry Pi Communication
// Fastest speed for Teensy LC before errors occuring
// See here: https://www.pjrc.com/teensy/td_uart.html
int rpi_baud_rate = 500000;   // Set baud rate to 500000


// Define structs
struct Accelerometer
{
  float x;
  float y;
  float z;
};

// Global Variables
float gx, gy, gz;
float tempC, tempF;
int pot;
int gps_date, gps_time, gps_satellites;
double gps_latitude, gps_longitude, gps_altitude, gps_course, gps_speed;

void setup()
{
  // Open serial communications and wait for port to open:
  Serial.begin(9600);
  // Open Raspberry Pi Serial communication
  RPISERIAL.begin(rpi_baud_rate, SERIAL_8N1/*8 Data bits, No Parity bits*/);  // Hardware Serial (RX & TX pins)

  // Set Up Reed Switch
  pinMode(REED_PIN, INPUT_PULLUP);

  // Set up LEDs
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);

  // Indicate system is until it works
  // change functionality here later on to indicate communication with pi
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, HIGH);

  // Nothing to do to set up POT

  // Set Up IMU
  SPI1.setMOSI(0);
  SPI1.setMISO(1);
  SPI1.setSCK(20);
  myIMU.begin();

  // Set Up GPS
  ss.begin(GPS_Baud);
}


void loop()
{
  // Service GPS
  if (ss.available() > 0)
  {
    if (gps.encode(ss.read()))
    {
      // Indicate System is Working
      digitalWrite(GREEN_LED, HIGH);
      digitalWrite(RED_LED, LOW);

      /* GPS */ 
      String GPS_Data;
      GPS_Data = getGPSData(gps);
      
      // Output GPS Data
      DEBUG_PRINTLN("GPS DATA:\n" + GPS_Data);
      RPISERIAL.write("GPS DATA:\n");
      writeStringToRPi(GPS_Data);
      RPISERIAL.flush();
      
      /* Reed Switch */
      String reed_Data;
      reed_Data = getReedData();

      // Output Reed Data
      DEBUG_PRINTLN("REED DATA:\n" + reed_Data);
      RPISERIAL.write("REED DATA:\n");
      writeStringToRPi(reed_Data);
      RPISERIAL.flush();

      /* Accelerometer */
      String accelerometer_data;
      Accelerometer accelerometer;
      accelerometer = getAccelerometerData(myIMU);

      // Output accelerometer data
      DEBUG_PRINTLN("ACCELEROMETER DATA:");
      DEBUG_PRINT("X = ");
      DEBUG_PRINT_DEC(accelerometer.x, 4);
      DEBUG_PRINT("Y = ");
      DEBUG_PRINT_DEC(accelerometer.y, 4);
      DEBUG_PRINT("Z = ");
      DEBUG_PRINT_DEC(accelerometer.z, 4);

      RPISERIAL.write("ACCELEROMETER DATA:\n");
      RPISERIAL.write("X = ");
      writeStringToRPi(accelerometer.x);
      RPISERIAL.write(" Y = ");
      writeStringToRPi(accelerometer.y);
      RPISERIAL.write(" Z = ");
      writeStringToRPi(accelerometer.z);
      

      // Service Gyroscope
      Serial.print("\nGYROSCOPE:\n");
      Serial.print(" X = ");
      gx = myIMU.readFloatGyroX();
      Serial.println(gx, 4);
      Serial.print(" Y = ");
      gy = myIMU.readFloatGyroY();
      Serial.println(gy, 4);
      Serial.print(" Z = ");
      gz = myIMU.readFloatGyroZ();
      Serial.println(gz, 4);

      // Service Thermometer
      Serial.print("\nTHERMOMETER:\n");
      Serial.print(" Degrees C = ");
      tempC = myIMU.readTempC();
      Serial.println(tempC, 4);
      Serial.print(" Degrees F = ");
      tempF = myIMU.readTempF();
      Serial.println(tempF, 4);

      // Service Pot
      Serial.print("\nPOTENTIOMETER:");
      pot = analogRead(POT_PIN);
      Serial.print("\nPot = ");
      Serial.println(pot);
      Serial.print("\n");
    }
  }
}

/*
 * Function to write String variable type since Serial.write("input") does not allow String variable as input
 */
void writeStringToRPi(String stringData) 
{ 
  for (int i = 0; i < stringData.length(); i++)
  {
    RPISERIAL.write(stringData[i]);
  }
}

String getGPSData(TinyGPSPlus gps)
{
  String output_data;
  
  gps_latitude = gps.location.lat();
  gps_longitude = gps.location.lng();
  gps_altitude = gps.altitude.meters();
  gps_course = gps.course.value();
  gps_time = gps.time.value();
  gps_speed = gps.speed.kmph();
  gps_satellites = gps.satellites.value();

  if (gps_satellites > 0)
  {
    output_data = "Location = " + String(gps_latitude) + ", " + String(gps_longitude) + ", " + String(gps_altitude) + "\n";
    output_data += "Course = " + String(gps_course) + "\n";
    output_data += "Speed = " + String(gps_speed) + "\n";
    output_data += "Satellites = " + String(gps_satellites) + "\n";
    output_data += "\n";
  }
  else
  {
    output_data = "No Data\n";
  }
  return output_data;
}

String getReedData()
{
  String output_data;
  int proximity = digitalRead(REED_PIN); // Read the state of the switch
  if (proximity == LOW) // If the pin reads low, the switch is closed.
  {
    output_data = "Switch = 1\n";
  }
  else
  {
    output_data = "Switch = 0\n";
  }
  return output_data;
}

Accelerometer getAccelerometerData(LSM6DS3 input_IMU)
{
  Accelerometer accelerometer; 

  accelerometer.x = myIMU.readFloatAccelX();
  accelerometer.y = myIMU.readFloatAccelY();
  accelerometer.z = myIMU.readFloatAccelZ();
  return accelerometer;
}
