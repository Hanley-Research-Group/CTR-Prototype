#include <Wire.h>
#include <Adafruit_ADS1X15.h>
#include <EEPROM.h>

Adafruit_ADS1115 ads;

String input = "";
const int captureTime = 500; // default 500 ms

const int mosfetPin = 3;
const int currentSense = 2;
const int voltageSense = 3;

float ampCal;
float ohmCal;
float roomTemp;
float roomTemp_resistance;

float partTemp(float Rt, float Rroom){
  if(Rt < Rroom){
    return 0;
  }
  float rho = 100; //nominal resistivity of Nitinol -- 100 uO / C
  float rho_slope = 0.05; //change in resistivity per degree celcius of nitinol -> (0.05uO * cm)/C
  float alpha = rho_slope/rho; //temperature coefficient for nitinol

  float temp = ((Rt/Rroom) - 1.0) / alpha; //given by paper
  return temp;
  
}
float partResistance(){
    static float last_good = 10.0;

    const float N = 5.0;

    float ampSum = 0;
    float voltSum = 0;

    for(int i = 0; i < (int)N; i++){
        float rawAmps = ads.computeVolts(ads.readADC_SingleEnded(currentSense));
        float rawOhms = ads.computeVolts(ads.readADC_SingleEnded(voltageSense));

        ampSum += rawAmps;
        voltSum += rawOhms;
        delayMicroseconds(200);
    }

    float rawAmps = ampSum / N;
    float rawOhms = voltSum / N;

    if(isnan(rawAmps) || isnan(rawOhms) || isinf(rawAmps) || isinf(rawOhms)){
        return last_good;
    }

    float amps = rawAmps / ampCal;
    float volts = rawOhms / ohmCal;

    if(amps < 0) amps = 0.01;
    if(volts < 0) volts = 0.01;
    const float min_amps = 0.0003;
    if(fabs(amps) < min_amps){
        return last_good;
    }

    float resistance = volts / amps;

    if(isnan(resistance) || isinf(resistance) || resistance <= 0 || resistance > 1e6){
        return last_good;
    }

    last_good = resistance;
    return resistance;
}

void setup(void)
{
  Serial.begin(250000);
  Serial.println("Ready.");

  ads.begin();
  ads.setGain(GAIN_FOUR);
  pinMode(mosfetPin, OUTPUT);
  digitalWrite(mosfetPin, LOW);
  EEPROM.get(0, ampCal);
  EEPROM.get(4, ohmCal);
  EEPROM.get(8, roomTemp);
  EEPROM.get(12, roomTemp_resistance);
  if (isnan(ampCal) || ampCal == 0.0f) ampCal = 1.0f;
  if (isnan(ohmCal) || ohmCal == 0.0f) ohmCal = 1.0f;
  if (isnan(roomTemp) || roomTemp == 0.0f) roomTemp = 22.0f;
  if (isnan(roomTemp_resistance) || roomTemp_resistance == 0.0f) roomTemp_resistance = 0.0f;
  
}

void loop(void)
{
  while (Serial.available() > 0)
  {
    char c = Serial.read();

    if (c == '\n' || c == '\r')
    {
      if (input.length() > 0)
      {
        handleCommand(input);
        input = "";
      }
    }
    else
    {
      input += c;

      if (input.length() > 30)
        input = "";
    }
  }
}

void handleCommand(String cmd)
{
  cmd.trim();
  int spaceIndex = cmd.indexOf(' ');
  String value;
  if (spaceIndex > 0)
  {
    value = cmd.substring(spaceIndex + 1);
  }
  // check if command starts with CAP
  if (cmd.startsWith("CAP"))
  {
    testCase(value);
  }
  else if(cmd.startsWith("OHM")){
    setOhmCal(value);
  }
  else if(cmd.startsWith("AMP")){
    setAmpCal(value);
  }
  else if(cmd.startsWith("ROOM")){
    setRoomTemp(value);
  }
  else if(cmd.startsWith("ROHM")){
    setRoomResistance();
  }
  else if(cmd.startsWith("RUN")){
    runProc();
  }
  else if(cmd.startsWith("PRNT")){
    printStuff();
  }
}

void printStuff(){
  Serial.println("DEBUG VALUES");
  Serial.print("Ohm Calibration Factor: ");
  Serial.println(ohmCal, 6);
  Serial.print("Amp Calibration Factor: ");
  Serial.println(ampCal, 6);
  Serial.print("Room Temp: ");
  Serial.println(roomTemp);
  Serial.print("Room Temp Resistance: ");
  Serial.println(roomTemp_resistance, 6);
}
void testCase(String newTime)
{
    int captureTime = (int)newTime.toInt();
    Serial.print("Starting capture for ");
    Serial.print(captureTime);
    Serial.println(" ms");

    digitalWrite(mosfetPin, HIGH);

    unsigned long startTime = millis();

    float ampSum = 0;
    float resSum = 0;
    float rawAmpSum = 0;
    float rawOhmSum = 0;
    int count = 0;

    while (millis() - startTime < (unsigned long)captureTime)
    {
    float rawAmps = ads.computeVolts(ads.readADC_SingleEnded(currentSense)); //in volts
    float rawOhms = ads.computeVolts(ads.readADC_SingleEnded(voltageSense)); //in volts
    
    float amps = rawAmps / ampCal;
    float resistance = (rawOhms / ohmCal) /  amps; //R = Vdiff/I

    ampSum += amps;
    resSum += resistance;
    rawAmpSum += rawAmps;
    rawOhmSum += rawOhms;
    count++;
    
    unsigned long elapsed = millis() - startTime;

    Serial.print(elapsed / 1000.0, 3);
    Serial.print("s / ");
    Serial.print(captureTime / 1000.0, 3);
    Serial.println("s");
    
    Serial.print(amps, 3);
    Serial.print("A, ");
    Serial.print(resistance,3);
    Serial.println("O");
    
    Serial.print("Raw Amps in Volts: "); Serial.println(rawAmps, 6);
    Serial.print("Raw Ohms in Volts: "); Serial.println(rawOhms, 6);
    
    }

    digitalWrite(mosfetPin, LOW);

    float avgAmps = ampSum / (float)count;
    float avgRes = resSum / (float)count;
    float avgRawAmps = rawAmpSum / (float)count;
    float avgRawOhms = rawOhmSum / (float)count;

    Serial.print("Average Amps: ");
    Serial.println(avgAmps, 6);
    Serial.print("Average Resistance: ");
    Serial.println(avgRes, 6);
    Serial.print("Average Raw Amps (V): ");
    Serial.println(avgRawAmps, 6);
    Serial.print("Average Raw Ohms (V): ");
    Serial.println(avgRawOhms, 6);

    Serial.println("Done.");
}
void setAmpCal(String cal)
{
  Serial.println("Setting Amp Calibration Value");
  float value = cal.toFloat();
  ampCal = value;
  EEPROM.put(0, value);
  Serial.print("Amp Calibration Value Set To ");
  Serial.println(value, 6);
}
void setOhmCal(String cal)
{
  Serial.println("Setting Ohm Calibration Value");
  float value = cal.toFloat();
  ohmCal = value;
  EEPROM.put(4, value);
  Serial.print("Ohm Calibration Value Set To ");
  Serial.println(value, 6);
}
void setRoomTemp(String temp)
{
  Serial.println("Setting Room Temperature");
  float value = temp.toFloat();
  roomTemp = value;
  EEPROM.put(8, value);
  Serial.print("Room Temperature Set To ");
  Serial.print(value);
  Serial.println(" Degrees C.");
}

float setRoomResistance(){
  int frequency = 1000; //Hz
  int time_s = 1;
  Serial.println("Setting Room Resistance");

  int time_between = (int)((1.0f / (float)frequency) * 1000.0f);
  int samples = frequency * time_s;

  roomTemp_resistance = 0;

  digitalWrite(mosfetPin, HIGH);

  for(int i = 0; i<samples; i++){
    float r = partResistance();
    if(isfinite(r)){
      roomTemp_resistance += r;
    }

    if(i % 100 == 0){
      Serial.print("Value: ");
      Serial.print(roomTemp_resistance / (i + 1));
      Serial.print(" | ");
      Serial.print(i);
      Serial.print("/");
      Serial.println(samples);
    }
    delay(time_between);
  }

  digitalWrite(mosfetPin, LOW);

  roomTemp_resistance /= (float)samples;
  EEPROM.put(12, roomTemp_resistance);
  Serial.print("Room Resistance Set To ");
  Serial.print(roomTemp_resistance);
  Serial.println(" Ohms");

  return roomTemp_resistance;
}








//real thingy
void runProc() {
  // STRUCTURE VARS
  float t_hold = 30;
  float t_ramp = 3;               // ramping time
  int pulse_time_ms = 100;
  int timeout_ms = 100;

  // TARGET TEMP AND SAMPLE RATE
  float temp_target = 500;        // degrees Celsius
  int frequency = 500;            // target sampling frequency (Hz)

  float stall_diff = 0.5;

  // EDGE CASES IF USER HASNT SET UP PROPERLY
  if (isnan(roomTemp) || roomTemp == 0) {
    Serial.println("Set room temp!!");
    return;
  }
  if (isnan(roomTemp_resistance) || roomTemp_resistance == 0) {
    Serial.println("Set room temp resistance!");
    return;
  }

  // Timing parameters
  unsigned long period_us = 1000000UL / frequency;          // microseconds between samples
  unsigned long time_between_ms = period_us / 1000;         // milliseconds, for compatibility
  if (time_between_ms == 0) time_between_ms = 1;            // safety

  // Convert user times to milliseconds
  unsigned long target_time_adjusted = (unsigned long)(t_hold * 1000.0f);
  unsigned long ramp_time_adjusted = (unsigned long)(t_ramp * 1000.0f);

  // Total elapsed time in milliseconds (for outer loop)
  unsigned long total_time = 0;

  // Outer loop – originally intended to maintain temperature for t_hold seconds
  // (kept as in original, but timing now precise)
  while (total_time <= target_time_adjusted) {
    float current_temp = roomTemp;
    int current_timeout_ms = 0;

    int ramp_samples = (int)((float)frequency * t_ramp);
    int samples = 0;
    Serial.println("Ramping...");

    // ----- RAMPING PHASE (precise timing) -----
    unsigned long ramp_start_us = micros();
    unsigned long next_sample_us = ramp_start_us;

    while (samples < ramp_samples && current_temp < temp_target) {
      // Set PWM duty cycle (linearly increasing with sample index)
      analogWrite(mosfetPin, (int)(((float)samples / (float)(ramp_samples) * 255.0f)));

      // Sample every 100 cycles (original logic)
      if (samples % 100 == 0) {
        digitalWrite(mosfetPin, HIGH);
        current_temp = roomTemp + partTemp(partResistance(), roomTemp_resistance);
        float amps = ads.computeVolts(ads.readADC_SingleEnded(currentSense)) / ampCal;
        digitalWrite(mosfetPin, LOW);

        // Print every 1000 samples
        if (samples % 1000 == 0) {
          Serial.println("Ramping... Current Temperature:");
          Serial.print(current_temp);
          Serial.print(" C | Amperage: ");
          Serial.print(amps);
          Serial.print(" Amps. | Samples: ");
          Serial.print(samples);
          Serial.print("/");
          Serial.println(ramp_samples);
        }
      }

      samples++;
      // Wait until it's time for the next sample
      next_sample_us += period_us;
      long delay_us = next_sample_us - micros();
      if (delay_us > 0) {
        delayMicroseconds(delay_us);
      }
    }

    // Special output for early temperature attainment
    if (current_temp >= temp_target) {
      Serial.println("DESIRED TEMPERATURE REACHED DURING RAMPING PERIOD.");
    } else {
      Serial.println("Ramping Finished. Heating to Desired Temperature:");
    }

    // ----- HOLD / HEATING PHASE (precise timing) -----
    // Continue using the same timing interval
    next_sample_us = micros();     // re-sync after ramp

    while (current_temp < temp_target && current_timeout_ms < timeout_ms) {
      analogWrite(mosfetPin, 254);   // nearly full power

      // Sample every 100 cycles
      if (samples % 100 == 0) {
        digitalWrite(mosfetPin, HIGH);
        float new_temp = roomTemp + partTemp(partResistance(), roomTemp_resistance);
        float amps = ads.computeVolts(ads.readADC_SingleEnded(currentSense)) / ampCal;
        digitalWrite(mosfetPin, LOW);

        // Stall detection
        if (new_temp - current_temp < stall_diff) {
          current_timeout_ms += time_between_ms;
        } else {
          current_timeout_ms = 0;
          current_temp = new_temp;
        }

        // Print every 1000 samples
        if (samples % 1000 == 0) {
          Serial.print(current_temp);
          Serial.print(" C | Amperage: ");
          Serial.print(amps);
          Serial.print(" Amps. | TIMEOUT: ");
          Serial.print(current_timeout_ms);
          Serial.print("/");
          Serial.println(timeout_ms);
        }
      }

      samples++;
      // Precise delay until next sample
      next_sample_us += period_us;
      long delay_us = next_sample_us - micros();
      if (delay_us > 0) {
        delayMicroseconds(delay_us);
      }
    }

    // Timeout check
    if (current_timeout_ms >= timeout_ms) {
      Serial.println("Could not reach desired temperature: Timed out.");
      return;
    }

    digitalWrite(mosfetPin, LOW);
    Serial.println("Desired temperature reached.");
    delay(100);   // brief pause (kept from original)

    // Update total elapsed time (precise, based on actual elapsed microseconds)
    unsigned long elapsed_us = micros() - ramp_start_us;
    total_time += elapsed_us / 1000;   // convert to ms
    Serial.print(total_time);
    Serial.print("/");
    Serial.println(target_time_adjusted);
  }

  Serial.println("Shape-Setting Complete.");
  delay(1000);

  // Cooldown period (unchanged)
  int cooldown_seconds = 60 * 5;
  Serial.println("Cooling..");
  for (int i = cooldown_seconds; i >= 0; i--) {
    Serial.print("Cooling... ");
    Serial.print("Time Remaining: ");
    Serial.print(i / 60);
    Serial.print("m ");
    Serial.print(i % 60);
    Serial.println("s.");
    delay(1000);
  }
  Serial.println("Process Complete!");
}
