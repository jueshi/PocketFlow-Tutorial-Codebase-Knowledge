# Chapter 8: Skew Correction Code

Welcome to the final chapter in our exploration of the `e112mp_pi_input_skew_cal` project! In the [previous chapter on the Iterative Search Algorithm for Skew Correction](07_iterative_search_algorithm_for_skew_correction_.md), we saw how our system cleverly searches for the best way to fix clock timing errors. That search algorithm's ultimate goal is to find a special "magic number" – a digital value that will perfectly tune our clocks. This magic number is what we call the **Skew Correction Code**.

Let's dive in and understand what this code is and how it performs its crucial clock-tuning magic!

## The Problem: How to Tell the Hardware "How Much" to Adjust?

Imagine you've meticulously figured out exactly how much to turn the tuning pegs on a guitar to get it in perfect tune. Now, you need a way to *set* those pegs to those exact positions. The [Iterative Search Algorithm for Skew Correction](07_iterative_search_algorithm_for_skew_correction_.md) does the hard work of figuring out the "how much" for our clock signals. But how does it communicate these precise instructions to the actual hardware circuits that can make the timing adjustments?

This is where the **Skew Correction Code** comes into play. It's the digital message that tells the hardware exactly how to adjust the clock timings.

## What is the Skew Correction Code? Your Digital Tuning Knobs!

The **Skew Correction Code** is a digital value – think of it as a sequence of 0s and 1s (like `01101011`). This code functions as a control setting for a specific piece of circuitry inside the [PMIX (Phase Mixer)](04_pmix__phase_mixer_.md). This specialized circuit is often called the **'PMIX Skew Adjust' circuit**.

You can imagine the Skew Correction Code as a set of very precise **digital knobs**. Each "knob" (or group of bits within the code) can finely adjust the timing of one of the [Quadrature Clocks (clk0, clk90, clk180, clk270)](03_quadrature_clocks__clk0__clk90__clk180__clk270__.md), making it arrive a tiny bit earlier or a tiny bit later.

The main job of the [Iterative Search Algorithm for Skew Correction](07_iterative_search_algorithm_for_skew_correction_.md) is to methodically try out different combinations for these digital knobs (i.e., different Skew Correction Code values) until it finds the one specific code that makes all the clocks perfectly aligned.

Once this **optimal Skew Correction Code** is determined, it's like finding the perfect setting for all your guitar tuning pegs. This code is then programmed into the hardware. This tells the 'PMIX Skew Adjust' circuit exactly how much it needs to compensate for any measured skews, effectively making the clocks arrive at their destinations in perfect synchronization.

As shown in the diagram on page 1 of the project documentation (`e112mp_pi_input_skew_cal.pdf`), finding the "Optimal Skew Correction Code" is the key to moving from a "With Skew" state to a "No Skew" state for our clock phases (represented by points A, B, C, D).

## How the "PMIX Skew Adjust" Circuit Uses the Code

Inside the [PMIX (Phase Mixer)](04_pmix__phase_mixer_.md), there's a dedicated "PMIX Skew Adjust" circuit (you can see this block in the diagram on Page 3 of `e112mp_pi_input_skew_cal.pdf`). This circuit sits *before* the main phase mixing logic of the PMIX. Its job is to pre-condition the incoming quadrature clocks (`clk0`, `clk90`, `clk180`, `clk270`).

Think of it like this:
*   `clk0` might be considered the main reference.
*   The 'PMIX Skew Adjust' circuit has tiny, controllable delay elements on the paths of `clk90`, `clk180`, and `clk270`.
*   The Skew Correction Code is a digital word. Different parts (bit-fields) of this word control these delay elements.
    *   For example, bits 0-3 of the code might control the delay for `clk90`.
    *   Bits 4-7 might control the delay for `clk180`.
    *   Bits 8-11 might control the delay for `clk270`.

When the optimal Skew Correction Code is loaded:
*   If `clk90` was arriving too early, the bits for `clk90` in the code would instruct its delay element to add a very specific, tiny delay.
*   If `clk180` was arriving too late, its bits in the code would instruct its delay element to reduce its inherent delay (effectively advancing it).

The result is that the clocks emerging *from* the 'PMIX Skew Adjust' circuit and going *into* the PMIX's main mixing logic are now perfectly aligned, as if there was no skew to begin with!

```mermaid
graph LR
    subgraph "Incoming Clocks (Potentially Skewed)"
        direction LR
        iClk0["clk0"]
        iClk90["clk90"]
        iClk180["clk180"]
        iClk270["clk270"]
    end

    SCC["Optimal Skew<br>Correction Code<br>(from Iterative Search)"]

    subgraph "PMIX_Hardware [PMIX Hardware]"
        direction LR
        PMIX_SkewAdjust["PMIX Skew Adjust Circuit"]

        subgraph "Main_PMIX_Logic ["Main PMIX Logic<br>(Phase Interpolation)"]"
            direction LR
            MixingLogic["Mixing/Interpolation"]
        end

        iClk0 --> PMIX_SkewAdjust
        iClk90 --> PMIX_SkewAdjust
        iClk180 --> PMIX_SkewAdjust
        iClk270 --> PMIX_SkewAdjust

        SCC --> PMIX_SkewAdjust

        PMIX_SkewAdjust -- De-skewed clk0 --> MixingLogic
        PMIX_SkewAdjust -- De-skewed clk90 --> MixingLogic
        PMIX_SkewAdjust -- De-skewed clk180 --> MixingLogic
        PMIX_SkewAdjust -- De-skewed clk270 --> MixingLogic
    end

    MixingLogic --> OutputClock["Precisely Phased Output for Data Sampling"]

    style PMIX_Hardware fill:#e6f3ff,stroke:#333,stroke-width:2px
    style PMIX_SkewAdjust fill:#d1e0ff
```
This diagram shows the Skew Correction Code acting as the control for the 'PMIX Skew Adjust' circuit, ensuring the main part of the PMIX gets clean, aligned clocks.

## Programming the Hardware: Setting the Knobs

The [PI Input Skew Calibration](01_pi_input_skew_calibration_.md) process, including the [Iterative Search Algorithm for Skew Correction](07_iterative_search_algorithm_for_skew_correction_.md), typically runs when the system starts up.
Once the search algorithm proudly announces, "I've found the optimal Skew Correction Code!", this digital value needs to be made permanent (at least for the current power-on cycle).

This is done by **writing the Skew Correction Code into special hardware memory locations called registers**. These registers are directly connected to the 'PMIX Skew Adjust' circuit.
1.  The iterative search algorithm determines the optimal code (e.g., `01101011`).
2.  The system's control logic takes this code.
3.  It writes this code into the designated PMIX skew control register(s).

Once written, the 'PMIX Skew Adjust' circuit continuously uses this programmed code to apply the precise, tiny delays to the clock signals. The diagram on Page 3 of `e112mp_pi_input_skew_cal.pdf` shows "DIG Controls" feeding into the "PMIX Skew Adjust" block. The Skew Correction Code effectively *becomes* these "DIG Controls" after the calibration algorithm has done its job.

### A Simplified Example

Let's imagine our Skew Correction Code is very simple, say 4 bits long:
*   Bits 0-1 control `clk90`'s adjustment.
*   Bits 2-3 control `clk180`'s adjustment.
    (Assume `clk270` is adjusted similarly or `clk0` is the fixed reference).

And let's say:
*   `00` means no adjustment.
*   `01` means add a tiny delay (e.g., +1 unit of delay).
*   `10` means add a bit more delay (e.g., +2 units of delay).
*   `11` means subtract a tiny delay (e.g., -1 unit of delay, or advance).

If the [Iterative Search Algorithm for Skew Correction](07_iterative_search_algorithm_for_skew_correction_.md) finds that:
*   `clk90` needs +1 unit of delay.
*   `clk180` needs -1 unit of delay.

The optimal Skew Correction Code might be `1101` (bits 2-3 are `11` for `clk180`, bits 0-1 are `01` for `clk90`).
This code `1101` would then be written to the hardware register.

```
// Conceptual: Iterative search has finished
optimal_scc_for_clk90 = 0b01; // Represents +1 unit delay
optimal_scc_for_clk180 = 0b11; // Represents -1 unit delay

// Combine into a single Skew Correction Code
// (Actual combination logic is hardware-specific)
final_skew_correction_code = (optimal_scc_for_clk180 << 2) | optimal_scc_for_clk90;
// final_skew_correction_code would be 0b1101 in this example

// Program this code into the hardware register
PMIX_SKEW_ADJUST_REGISTER = final_skew_correction_code;

// Now, the PMIX_Skew_Adjust circuit uses this value (0b1101)
// to apply the +1 delay to clk90 and -1 delay to clk180.
```
This simple code snippet shows the idea: individual adjustments are determined, combined into a single code, and then written to a hardware register to take effect.

## The Result: Perfectly Tuned Clocks

With the optimal Skew Correction Code programmed into the 'PMIX Skew Adjust' circuit, the magic happens:
*   The [Quadrature Clocks (clk0, clk90, clk180, clk270)](03_quadrature_clocks__clk0__clk90__clk180__clk270__.md) arriving at the main phase interpolation logic of the [PMIX (Phase Mixer)](04_pmix__phase_mixer_.md) are now precisely aligned, with their 90-degree phase relationships restored.
*   The PMIX can then perform its primary job of fine-tuning the data sampling phase with much greater accuracy and linearity.
*   This leads to a cleaner signal being sampled, which means a better Signal-to-Noise Ratio (SNR).
*   Ultimately, this results in fewer errors when reading the data, meaning a lower Bit Error Rate (BER).

As stated in the project documentation (`e112mp_pi_input_skew_cal.pdf`, Page 1):
> "Removal of Skew results in SNR and BER optimization for the RX."

The Skew Correction Code is the final piece of the puzzle that makes this "removal of skew" a reality.

## What We've Learned

In this chapter, we've uncovered the role of the **Skew Correction Code**:
*   It's a **digital value** (like a set of digital knobs) that acts as the control setting for the **'PMIX Skew Adjust' circuit** within the [PMIX (Phase Mixer)](04_pmix__phase_mixer__.md).
*   The [Iterative Search Algorithm for Skew Correction](07_iterative_search_algorithm_for_skew_correction_.md) works to find the **optimal Skew Correction Code**.
*   Once found, this code is **programmed into hardware registers**.
*   The 'PMIX Skew Adjust' circuit uses this code to apply fine-grained delays or advances to individual [Quadrature Clocks (clk0, clk90, clk180, clk270)](03_quadrature_clocks__clk0__clk90__clk180__clk270__.md).
*   This effectively **aligns the clocks**, counteracting any measured skew *before* they reach the main PMIX logic.
*   The result is improved PMIX performance, leading to better SNR and BER for the receiver.

## Conclusion: The Symphony of Calibration

And with that, we've reached the end of our journey through the core concepts of the `e112mp_pi_input_skew_cal` project!

We started by understanding the need for [PI Input Skew Calibration](01_pi_input_skew_calibration_.md) to combat the detrimental effects of [Clock Skew](02_clock_skew_.md). We met the crucial [Quadrature Clocks (clk0, clk90, clk180, clk270)](03_quadrature_clocks__clk0__clk90__clk180__clk270__.md) and the versatile [PMIX (Phase Mixer)](04_pmix__phase_mixer_.md) that uses them. We saw how a [Loopback Test Signal and ADC](05_loopback_test_signal_and_adc_.md) are used to gather data, which is then analyzed via [Skew Correlation Measurements (E21, E31, E41)](06_skew_correlation_measurements__e21__e31__e41_.md). This information feeds the intelligent [Iterative Search Algorithm for Skew Correction](07_iterative_search_algorithm_for_skew_correction_.md), which diligently seeks out the optimal **Skew Correction Code** – the very topic of this chapter.

Each of these components and processes plays a vital role in an automated startup routine that ensures our high-speed digital receiver can "hear" and interpret data with the utmost precision. It's a beautiful example of how complex systems can self-tune for optimal performance!

Thank you for following along with this tutorial. We hope this has given you a clear and beginner-friendly understanding of how PI input skew calibration works!

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)