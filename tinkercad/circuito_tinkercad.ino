// SCPRA - Aurora Siger: regra de risco no Arduino (Tinkercad Circuits)
// Entradas analogicas: A0 bateria, A1 O2, A2 TMP36, A3 consumo, A4 geracao
// Saidas: D8 LED vermelho (Y1 CRITICO), D9 LED amarelo (Y2 ATENCAO), D10 LED verde (NORMAL)
// Regra identica a classificar_risco() do codigo_fonte.py:
//   A = bateria < 20     B = O2 < 19,5     C = consumo > geracao
//   D = bateria < 40     E = temperatura fora de 18 a 26 C
//   Y1 = A + B           Y2 = (C . D) + E

const int PIN_BAT = A0, PIN_O2 = A1, PIN_TEMP = A2, PIN_CONS = A3, PIN_GER = A4;
const int LED_CRIT = 8, LED_ATEN = 9, LED_NORM = 10;

void setup() {
  Serial.begin(9600);
  pinMode(LED_CRIT, OUTPUT);
  pinMode(LED_ATEN, OUTPUT);
  pinMode(LED_NORM, OUTPUT);
}

void loop() {
  float bat  = analogRead(PIN_BAT) * 100.0 / 1023.0;               // 0 a 100 %
  float o2   = 15.0 + analogRead(PIN_O2) * 10.0 / 1023.0;          // 15 a 25 %
  float temp = (analogRead(PIN_TEMP) * 5.0 / 1023.0 - 0.5) * 100.0; // TMP36 em C
  float cons = analogRead(PIN_CONS) * 20.0 / 1023.0;               // 0 a 20 kW
  float ger  = analogRead(PIN_GER) * 20.0 / 1023.0;                // 0 a 20 kW

  bool A = bat < 20.0;
  bool B = o2 < 19.5;
  bool C = cons > ger;
  bool D = bat < 40.0;
  bool E = (temp < 18.0) || (temp > 26.0);

  bool Y1 = A || B;
  bool Y2 = (C && D) || E;

  digitalWrite(LED_CRIT, Y1 ? HIGH : LOW);
  digitalWrite(LED_ATEN, Y2 ? HIGH : LOW);
  digitalWrite(LED_NORM, (!Y1 && !Y2) ? HIGH : LOW);

  const char* status = Y1 ? "CRITICO" : (Y2 ? "ATENCAO" : "NORMAL");
  Serial.print("bat="); Serial.print(bat, 1);
  Serial.print(" o2="); Serial.print(o2, 1);
  Serial.print(" temp="); Serial.print(temp, 1);
  Serial.print(" cons="); Serial.print(cons, 1);
  Serial.print(" ger="); Serial.print(ger, 1);
  Serial.print(" | A"); Serial.print(A); Serial.print(" B"); Serial.print(B);
  Serial.print(" C"); Serial.print(C); Serial.print(" D"); Serial.print(D);
  Serial.print(" E"); Serial.print(E);
  Serial.print(" -> "); Serial.println(status);
  delay(500);
}
