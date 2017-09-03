String strCommand = "";
int ANALOG_PIN = 0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  int analogValue;
  double temperatureData;
  while(Serial.available()) {
    strCommand = Serial.readString();

    if(strCommand == "GET_TEMPERATURE") {
      analogValue = analogRead(ANALOG_PIN);
      temperatureData = (double) analogValue * (5 / 10.24);
      Serial.println(temperatureData);
    }
  }
}
