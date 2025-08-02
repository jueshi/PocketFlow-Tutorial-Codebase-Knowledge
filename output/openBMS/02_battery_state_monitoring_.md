# Chapter 2: Battery State Monitoring

In [Chapter 1: BMS Configuration](01_bms_configuration_.md), we taught our BMS about the battery it's protecting—its size and safety limits. It's like giving a doctor a patient's chart with their name, age, and a list of normal vital signs.

But a chart is useless if the doctor never actually sees the patient! This chapter is all about that routine check-up. **Battery State Monitoring** is the process where the BMS periodically takes the battery's "vital signs" to understand its health at any given moment.

### What Are We Trying to Do?

Our goal is to get a live snapshot of the battery's health. Think of it like a car's dashboard. We don't just want to know if the engine is "okay" or "not okay"; we want specific numbers. How fast are we going? How much fuel is left?

For our BMS, the vital signs are:
1.  **Individual Cell Voltages:** What is the voltage of every single cell?
2.  **Pack Current:** How much electricity is flowing in or out of the entire pack right now?
3.  **Key Health Indicators:** From the raw data, what is the highest cell voltage, the lowest cell voltage, and the total pack voltage?

These numbers are the foundation for everything else the BMS does, from keeping the battery safe to balancing the cells.

---

### The Monitoring Routine

In the `openBMS` project, this check-up happens continuously inside the main `loop()` function. It's a three-step process:
1.  **Read all cell voltages.**
2.  **Read the pack current.**
3.  **Process the data to find the min, max, and total.**

Let's look at how the `openBMS.pde` code orchestrates this.

#### Code Example: The Main Check-up Loop

```c++
// File: openBMS.pde

void loop() {
  // ... some setup code ...

  // Step 1: Read the voltage of every cell
  readVolts();

  // Step 2: Read the current flowing through the pack
  readCurrent();

  // Step 3: Process the raw data into useful information
  voltageTotal = vTotal();
  highestCellNumber = highestCell(); // Also finds the highest voltage
  lowestCellNumber = lowestCell();   // Also finds the lowest voltage

  // ... now use this information for safety, balancing, etc. ...
}
```

This snippet from the main `loop()` is our "to-do" list. Every time it runs, it performs a full health check. Let's look at each of these functions to see what they do.

---

### Step 1 & 2: Gathering the Raw Data

The first two steps involve talking to the hardware to get raw measurements.

#### Reading Cell Voltages

The `readVolts()` function is responsible for communicating with the LTC6802-2 monitoring chips. It tells them to measure the voltage of each cell they are connected to and then collects the results.

```c++
// File: openBMS.pde

// A simplified view of what readVolts() does
void readVolts() {
  // 1. Send a command to all monitoring boards to start measuring.
  // This is like saying "everyone, take a reading now!"
  // ... hardware communication code ...

  // 2. Wait a moment for the measurement to complete.
  delay(20);

  // 3. Go to each board one-by-one and collect its results.
  for(int boardNumber = 0; boardNumber < TOTALBOARDS; boardNumber++) {
    // ... code to get data from one board ...
  }

  // 4. Convert the raw chip data into volts and store it.
  for(int i = 1; i <= TOTALCELLS; i++) {
    // The chip gives a number; we convert it to a human-readable voltage.
    cellVoltage[i] = raw_chip_value[i] * 1.5 / 1000;
  }
}
```

The details of talking to the chip are complex, so we've wrapped them in this function. We'll explore exactly how that works in [Chapter 7: LTC6802-2 Chip Communication](07_ltc6802_2_chip_communication_.md). For now, just know that after `readVolts()` is called, we have an up-to-date list of every cell's voltage stored in an array named `cellVoltage`.

#### Reading Pack Current

The `readCurrent()` function is much simpler. It reads a value from an analog input pin connected to a current sensor.

```c++
// File: openBMS.pde

void readCurrent() {
  // Read the analog pin where the current sensor is connected
  int adc = analogRead(CURRENTSENSOR);

  // Convert the raw analog reading (0-1023) into Amps
  // The formula depends on the specific sensor being used
  instantCurrent = (adc - zeroReference) * (/* scaling factors */);
}
```

After `readCurrent()` runs, the variable `instantCurrent` holds the number of amps flowing through the pack. A positive number means the battery is discharging (powering something), and a negative number means it's charging.

### Step 3: Processing the Vitals

Now that we have the raw data in the `cellVoltage` array and `instantCurrent` variable, we need to make sense of it. This is like a doctor looking at a list of numbers and finding the most important ones.

#### Calculating Total Voltage

The `vTotal()` function simply adds up all the individual cell voltages.

```c++
// File: openBMS.pde

float vTotal() {
  float total = 0;
  // Loop through every cell we have
  for (int i = 1; i <= TOTALCELLS; i++) {
    // Add its voltage to our running total
    total = total + cellVoltage[i];
  }
  return total;
}
```
*   **Input:** The `cellVoltage` array filled by `readVolts()`.
*   **Output:** A single number, like `105.6` (Volts), which is the sum of all cell voltages.

#### Finding the Highest and Lowest Cell Voltages

The `highestCell()` and `lowestCell()` functions are critical for safety. They scan through the list of cell voltages to find the outliers.

```c++
// File: openBMS.pde

int highestCell() {
  voltageHighest = 0; // Start with a very low number
  int cellNumber;

  for (int i = 1; i <= TOTALCELLS; i++) {
    // If the cell we're looking at is higher than the highest we've seen so far...
    if (cellVoltage[i] > voltageHighest) {
      // ...then this is our new highest!
      voltageHighest = cellVoltage[i];
      cellNumber = i;
    }
  }
  return cellNumber; // Return which cell was the highest
}
```
This function does two things:
1.  It finds the single highest voltage value and stores it in the global variable `voltageHighest`.
2.  It returns the "cell number" (e.g., cell #25) that had that highest voltage.

The `lowestCell()` function works in the exact same way but looks for the smallest value instead.

---

### Under the Hood: The Flow of Information

Let's visualize the entire process from start to finish with a diagram.

```mermaid
sequenceDiagram
    participant MainLoop as Main Loop
    participant readVolts() as readVolts()
    participant LTCBoards as LTC6802-2 Boards
    participant Processing as Processing Functions

    MainLoop->>readVolts(): Get all cell voltages.
    readVolts()->>LTCBoards: Command: "Start measuring voltages!"
    LTCBoards-->>readVolts(): Raw voltage data
    Note right of readVolts(): Data is converted to volts and <br> stored in `cellVoltage` array.
    readVolts()-->>MainLoop: Done.

    MainLoop->>Processing: Find total, highest, and lowest voltages.
    Processing->>Processing: Loop through `cellVoltage` array.
    Note right of Processing(): Calculates `voltageTotal`, <br> `voltageHighest`, `voltageLowest`.
    Processing-->>MainLoop: Results are ready in global variables.
```

This sequence repeats over and over, giving the BMS a constant, fresh stream of information about the battery's state. This fresh data is crucial for the next step: using it to make safety decisions.

For example, remember the `HIGHVOLTAGECUTOFF` we set in Chapter 1? Here’s how it's used with the data we just gathered:

```c++
// File: openBMS.pde in loop()

// After running highestCell(), the variable 'voltageHighest' is updated.
// Now, we check it against our rule.
if (voltageHighest >= HIGHVOLTAGECUTOFF) {
  // One of the cells is too high!
  // Take action, like shutting off the charger.
  digitalWrite(CHARGERSHUTOFF, HIGH);
}
```
You can now see the whole picture:
1.  **Configuration** sets the rule (`HIGHVOLTAGECUTOFF`).
2.  **Monitoring** gets the live data (`voltageHighest`).
3.  **Safety Logic** compares the live data to the rule and acts.

### Conclusion

You've now learned how the `openBMS` performs its regular health check-up!

1.  **Battery State Monitoring** is the routine process of measuring the battery's vital signs.
2.  It involves two main parts: **data collection** (`readVolts`, `readCurrent`) and **data processing** (`vTotal`, `highestCell`, `lowestCell`).
3.  The `loop()` function continuously runs this check-up to get a live snapshot of the battery's health.
4.  The results of this monitoring—like `voltageHighest` and `voltageLowest`—are the key inputs for all other BMS tasks.

Now that we know how to check the battery's vital signs, what do we do if we find a problem? What happens if a cell voltage is dangerously high or low? That's the subject of our next chapter.

Next up: [Safety Management](03_safety_management_.md)

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)