# Chapter 3: Quadrature Clocks (clk0, clk90, clk180, clk270)

Welcome to Chapter 3! In the [previous chapter on Clock Skew](02_clock_skew_.md), we learned how tiny timing differences between clock signals can cause big problems in electronic systems. Now, we're going to meet a special set of clock signals that are essential for understanding incoming data accurately: the **Quadrature Clocks**.

## The Challenge: Getting a Clear Picture of Fast Data

Imagine you're trying to observe something that's happening very, very quickly, like the wing beats of a hummingbird. If you only take one snapshot (one picture), you might not get a full understanding of the motion. You might catch the wing up, down, or somewhere in between, but it's hard to tell the whole story from a single point.

High-speed digital receivers face a similar challenge. They receive data as a rapidly changing electronic signal. To understand this data (to read the 0s and 1s), the receiver needs to "look" at the signal at precise moments. If it only looks at one point in the signal's repeating pattern, it might miss important details, especially if there's noise or slight distortions.

## Meet the "Sampling Squad": Quadrature Clocks

To get a better "look" at the incoming data, many advanced receivers use a team of four special clock signals. These are often called **Quadrature Clocks**:
*   `clk0` (clock zero)
*   `clk90` (clock ninety)
*   `clk180` (clock one-eighty)
*   `clk270` (clock two-seventy)

Think of these clocks like four photographers stationed around a spinning wheel, all instructed to take a picture at slightly different times, perfectly spaced out.

### What is "Phase"? And Why Degrees?

Before we dive into each clock, let's quickly understand "phase." Imagine a spinning wheel. "Phase" describes a specific point in the wheel's rotation. We often measure phase in degrees, just like a circle has 360 degrees.
*   0 degrees could be the top of the wheel.
*   90 degrees would be a quarter turn.
*   180 degrees a half turn.
*   270 degrees a three-quarter turn.
*   360 degrees brings it back to the top (which is the same as 0 degrees for the next cycle).

Our quadrature clocks are named based on their ideal phase relationship to each other.

### The Clock Team:

1.  **`clk0` (Clock Zero): The Reference Point (North)**
    *   This is our main reference clock. Think of it as "North" on a compass. It marks the starting point, or 0-degree phase, for our timing.

2.  **`clk90` (Clock Ninety): 90 Degrees Later (East)**
    *   This clock is designed to trigger exactly 90 degrees (a quarter cycle) *after* `clk0`. If `clk0` is North, `clk90` is "East."

3.  **`clk180` (Clock One-Eighty): 180 Degrees Later (South)**
    *   This clock is designed to trigger 180 degrees (a half cycle) *after* `clk0`. This is "South" on our compass.

4.  **`clk270` (Clock Two-Seventy): 270 Degrees Later (West)**
    *   This clock is designed to trigger 270 degrees (a three-quarter cycle) *after* `clk0`. This is "West" on our compass.

After `clk270`, the next `clk0` pulse for the next cycle would occur, completing the 360-degree cycle.

**The "Quadrature" in Quadrature Clocks:**
The term "quadrature" refers to this 90-degree separation. "Quad" means four, and these four clocks divide the clock cycle into four equal parts, like the four quadrants of a circle or the four cardinal directions on a compass.

```mermaid
graph TD
    subgraph "Clock Cycle"
        direction LR
        C0[clk0 @ 0°<br>(North)] -->|90° delay| C90[clk90 @ 90°<br>(East)]
        C90 -->|90° delay| C180[clk180 @ 180°<br>(South)]
        C180 -->|90° delay| C270[clk270 @ 270°<br>(West)]
        C270 -->|90° delay| Next_C0[Next clk0 @ 360°/0°]
    end
```

## Why Four Clocks? The Power of Multiple Snapshots

Why go to the trouble of having four clocks instead of just one? These clocks are used to **sample** the incoming data signal. "Sampling" means taking a quick measurement of the signal's voltage (its level) at a specific instant.

By using `clk0`, `clk90`, `clk180`, and `clk270` to sample, the receiver gets four "snapshots" of the data signal spread across its cycle. This is incredibly useful:

*   **More Information:** It gives a much more detailed picture of the signal's shape and timing.
*   **Finding the Middle:** It helps the receiver find the best point in time to decide if the data is a '0' or a '1' (usually the "middle" of the data bit, where the signal is most stable).
*   **Dealing with Imperfections:** Real-world signals aren't perfect. Having multiple sample points helps the receiver make better sense of noisy or slightly distorted signals.

Let's imagine our incoming data signal is like a smooth wave (a sine wave, as often used in testing, like the [Loopback Test Signal and ADC](05_loopback_test_signal_and_adc_.md) will use). Here’s how our quadrature clocks would sample it:

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'lineColor': '#bbb', 'textColor': '#333'}}}%%
xychart-beta
    title "Sampling a Sine Wave with Quadrature Clocks"
    x-axis [0, 0.25, 0.5, 0.75, 1]
    y-axis [-1.2, 1.2]
    sine stroke-width=2px
    line [clk0_sample, clk90_sample, clk180_sample, clk270_sample] fill=false stroke-width=0px type=scatter shape=diamond size=4px
    bar [clk0_line, clk90_line, clk180_line, clk270_line] stroke-width=1px stroke-dasharray=5
    annotations [
      {
        "x": 0.0, "y": 0, "text": "clk0 samples here", "dx": 20, "dy": -20
      },
      {
        "x": 0.25, "y": 1, "text": "clk90 samples here", "dx": 20, "dy": -20
      },
      {
        "x": 0.5, "y": 0, "text": "clk180 samples here", "dx": 20, "dy": 20
      },
      {
        "x": 0.75, "y": -1, "text": "clk270 samples here", "dx": 20, "dy": 20
      }
    ]
    config {
      "chartOrientation": "horizontal",
      "plotRecess": {"left": 0, "right": 0, "top":0, "bottom":0}
    }
    series {
        "sine": {
            "data": [
                {"x":0, "y":0}, {"x":0.05, "y":0.309}, {"x":0.1, "y":0.588}, {"x":0.15, "y":0.809}, {"x":0.2, "y":0.951}, {"x":0.25, "y":1},
                {"x":0.3, "y":0.951}, {"x":0.35, "y":0.809}, {"x":0.4, "y":0.588}, {"x":0.45, "y":0.309}, {"x":0.5, "y":0},
                {"x":0.55, "y":-0.309}, {"x":0.6, "y":-0.588}, {"x":0.65, "y":-0.809}, {"x":0.7, "y":-0.951}, {"x":0.75, "y":-1},
                {"x":0.8, "y":-0.951}, {"x":0.85, "y":-0.809}, {"x":0.9, "y":-0.588}, {"x":0.95, "y":-0.309}, {"x":1, "y":0}
            ],
            "name": "Data Signal"
        },
        "clk0_sample": { "data": [{"x": 0, "y":0}], "name": "clk0 Sample"},
        "clk90_sample": { "data": [{"x": 0.25, "y":1}], "name": "clk90 Sample"},
        "clk180_sample": { "data": [{"x": 0.5, "y":0}], "name": "clk180 Sample"},
        "clk270_sample": { "data": [{"x": 0.75, "y":-1}], "name": "clk270 Sample"},
        "clk0_line": { "data": [{"x":0, "y":-1.2}, {"x":0, "y":1.2}], "name": "clk0 line"},
        "clk90_line": { "data": [{"x":0.25, "y":-1.2}, {"x":0.25, "y":1.2}], "name": "clk90 line"},
        "clk180_line": { "data": [{"x":0.5, "y":-1.2}, {"x":0.5, "y":1.2}], "name": "clk180 line"},
        "clk270_line": { "data": [{"x":0.75, "y":-1.2}, {"x":0.75, "y":1.2}], "name": "clk270 line"}
    }
```
This diagram shows that each clock captures the signal's value at a different phase point. Together, these four samples (`d0`, `d90`, `d180`, `d270` in some systems) give a very good idea of the signal's behavior over one full cycle.

## The Ideal vs. Reality: The Problem of [Clock Skew](02_clock_skew_.md)

Now, here's the crucial part: for this system to work perfectly, the phase separations *must be exactly 90 degrees*.
*   `clk90` must be *exactly* 90 degrees after `clk0`.
*   `clk180` must be *exactly* 90 degrees after `clk90` (and 180 after `clk0`).
*   And so on.

But as we learned in the [previous chapter on Clock Skew](02_clock_skew_.md), clock signals can arrive too early or too late due to various physical reasons. This means our "East" clock might not be exactly 90 degrees from "North," or "South" might be off from "East." If these phase relationships are not precise, the samples taken won't represent the signal correctly, leading to errors in data reception.

The project documentation (`e112mp_pi_input_skew_cal.pdf`, Page 1) shows a "No Skew" diamond shape (representing ideal 0, 90, 180, 270 degree timing points) and a "With Skew" distorted diamond. This distortion is what happens when our quadrature clocks aren't perfectly spaced.

## The Goal of Calibration: Keeping the Compass True

This is where the `e112mp_pi_input_skew_cal` project comes in. A primary goal of this project is to **calibrate** these quadrature clocks. The calibration process:
1.  Measures the *actual* phase differences between `clk0`, `clk90`, `clk180`, and `clk270`.
2.  Makes tiny adjustments to their timing until they are as close as possible to the ideal 90-degree separations.

By doing this, we ensure that our "compass points" are true and the receiver can accurately sample the incoming data.
The project documentation (`e112mp_pi_input_skew_cal.pdf`, Page 3) has a diagram illustrating this. You can see `+clk0`, `clk90`, `clk180`, `clk270` labeled as "Sampling Clocks" which are used to sample an "ADC IN" (Analog-to-Digital Converter Input) signal. The calibration aims to adjust these sampling clocks.

## What's Under the Hood (Briefly)

How are these clocks even created? Typically, a system has a primary, high-frequency clock source (like from a Phase-Locked Loop or PLL). The quadrature clocks are derived from this source. This might involve:
*   Special circuits that can divide the main clock's frequency.
*   Delay elements or phase shifters that intentionally delay copies of the clock signal to create the 90, 180, and 270-degree versions. A component called a [PMIX (Phase Mixer)](04_pmix__phase_mixer_.md) is often involved in generating or using these phases.

However, the wires (routes) carrying these clock signals to where they're needed, and the buffer circuits that strengthen them, can all introduce slight, unwanted delays. These delays are the source of the [Clock Skew](02_clock_skew_.md) that disrupts the perfect 90-degree relationships. This is why calibration is so vital.

## What We've Learned

In this chapter, we've met the quadrature clocks: `clk0`, `clk90`, `clk180`, and `clk270`.
*   They are a set of four clocks ideally phase-shifted by 90 degrees relative to each other, like points on a compass.
*   `clk0` is the reference (0 degrees).
*   `clk90` is at 90 degrees, `clk180` at 180 degrees, and `clk270` at 270 degrees.
*   They are used to sample an incoming data signal at four distinct points in its cycle, giving the receiver a much more detailed understanding of the data.
*   Maintaining these precise 90-degree separations is crucial for accurate data reception.
*   [Clock Skew](02_clock_skew_.md) can disrupt these ideal phase separations.
*   The `e112mp_pi_input_skew_cal` project works to calibrate these clocks, ensuring they are correctly aligned.

These quadrature clocks are fundamental inputs to other critical components in the receiver. One such component is the Phase Mixer, or PMIX.

Let's explore that in the next chapter: [PMIX (Phase Mixer)](04_pmix__phase_mixer_.md)

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)