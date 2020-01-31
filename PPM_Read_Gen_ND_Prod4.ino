// PPM_Read_Gen  by Wayne Andrrews aka CurryKitten
//
// The premise of this simple script is to read some channel information from the serial port, 
// turn this into a valid PPM frame, and then write it out to a transmitter.  In this case I'm
// using the unpluggable module from a Turnigy 9X.
//
// Some compromises have been made on this version, I decided to read channels as a pecentage
// value where 0 is low, and 99  is high.  This was to avoid the use of multibyte reads - obviously
// though I could have gone up to 255, so can do this in the future.  I noticed it seems quite easy
// for the arduino to either lose, or gain serial bytes which can throw everything out of sync, so
// expect a start/stop byte of 255/254 respectively - so our complete packet from the host
// should look like -
//
//  ff ch1 ch2 ch3 ch4 fe
//
// The PPM write is now interrupt driven on a timer.  Using delaymicroseconds and delay were 
// causing some serious jitter in the servos

#define channumber 8         // How many channels we'll work on, though some parts are hardcoded to 4 anyway
int channel[channumber+1];   // This array hold the PPM usec values 0 is the sync pulse
int ch[5];                   // This array is used to read the percentage values of each channel from the python bridge
int PPMout = 9;              // The pin on the Arduino we output PPM on
int pulsegap = 300;          // The gap between the channels (300 is for a Turnigy 9X)
int frameLength = 20;        // The duration in millisecs of a frame
int startpack=0;             // We use this to check for a valid start of a serial read
int endpack=0;               // ..and this for the end of the serial read
int lastFrame=0;
int curMillis=0;
int i;

void setup()
{
  while (!Serial) {
    ; // wait for serial port to connect. Needed for Leonardo only
  }
  Serial.begin(9600); 
  pinMode(PPMout, OUTPUT); 
  
  // Set channels 5-8 at midpoint, since we're only reading 4 channels from our Python bridge
  // Channel 0 represents the length of the sync pulse, but this isn't needed in this code
  channel[1] = 1079;
  channel[2] = 1079;
  channel[3] = 1079;
  channel[4] = 1079;
  channel[5] = 1079;
  channel[6] = 1079;
  channel[7] = 1079;
  channel[8] = 1079;
  channel[0] = 13352;
  
  // UseTimer1 to setup an ISR every 20ms
  cli();          // disable global interrupts
  TCCR1A = 0;     // set entire TCCR1A register to 0
  TCCR1B = 0;     // same for TCCR1B
 
  // set compare match register to desired timer count:
  OCR1A = 312;  // At 16Mhz, 20ms = 320,000 clock cycles, so 312 * 1024 = 319488
  // turn on CTC mode:
  TCCR1B |= (1 << WGM12);
  // Set CS10 and CS12 bits for 1024 prescaler:
  TCCR1B |= (1 << CS10);
  TCCR1B |= (1 << CS12);
  // enable timer compare interrupt:
  TIMSK1 |= (1 << OCIE1A);
  // enable global interrupts:
  sei();
}

void loop()
{
  // Don't bother going on unless we have a complete packet length, I found the Arduino would have the first 4 bytes of the packet
  // ready, and so fail on the incorrect end bytes.
  
  if (Serial.available() >= 6) {      // Check data is available
  // Turn off interrupts while we're processing the serial data so we don't jump out and run our ISR
   cli();
    startpack = Serial.read();
    if (startpack == 255) {      // Check to see if we're at the start of a valid set of values
      ch[4] = Serial.read();     // Axis 1 on PS3 maps to ch 4
      ch[3] = Serial.read();     // 2 to 3
      ch[1] = Serial.read();     // 3 to 1
      ch[2] = Serial.read();     // and 4 to 2
      endpack = Serial.read();   // Make sure that our sequence ends correctly      
      if (endpack == 254) {  
        // Calculate the PPM sync value from the percentage we're given.  When looking at the 
        // values that came in from the radio, I noticed that the range from centre to bottom and
        // centre to top is different, so we must use a slightly different scaling method when 
        // working out the values. 
        //
        // We base this on some conservative values so we aren't in danger of over doing the servos.
        // low position is 665usec, centre is 1079usec, and max is 1440usec
        for ( i = 1; i < 5; i = i + 1 ) {
          if (ch[i] <= 50) {
            channel[i] = int(ch[i] * 8.28) + 665;
          } else {
            channel[i] = int((ch[i] - 50) * 7.22 + 1079);
          }
        }     
      } 
    }
  // ok, finished processing the serial data, so can turn interrupts back on
  sei();
  }
} 


ISR(TIMER1_COMPA_vect)
{
  // The ISR generate the PPM.  This was written with a Turnigy 9X in mind, however
  // it's simple to change to a radio which uses LOW pulses to generate it's PPM
  // just by reversing the LOW/HIGH in the loop  
 
  for ( i = 1; i < 5; i = i + 1 ) {
    digitalWrite(PPMout, LOW);                 // Start on the LOW pulse
    delayMicroseconds(pulsegap);               // wait for the pulse gap
    digitalWrite(PPMout, HIGH);                // .. and do our HIGH pulse 
    delayMicroseconds(channel[i]);             // Finish off pulse
  }
  // Finish frame with sync pulse
  digitalWrite(PPMout, LOW);
  delayMicroseconds(pulsegap);
  // The sync is HIGH, so leave the pin in that state under the next interrupt
  digitalWrite(PPMout, HIGH);  
}




