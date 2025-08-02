# Chapter 6: COM and Metric Calculation

In the [previous chapter](05_interference___noise_pdf_generation_.md), we completed the monumental task of building a complete statistical model for all the interference in our system. We now have a comprehensive **Probability Density Function (PDF)** and a **Cumulative Distribution Function (CDF)** that describe the total noise our signal will face.

We have everything we need for the final step. From [Chapter 4](04_equalizer_optimization___optimize_fom_.md), we have our best-case signal amplitude (`A_s`), and from Chapter 5, we have the complete picture of the noise. It's time to bring them together for the final verdict.

### Our Goal for This Chapter

This is the moment of truth. Our goal is to calculate the final score for our channel: the **Channel Operating Margin (COM)**. We will learn how the simulation compares the clean signal's strength to the statistical worst-case noise to determine if the channel passes or fails.

---

## The Final Verdict: Signal vs. Noise

Let's return one last time to our analogy of the structural engineer designing a bridge.
*   The engineer knows the maximum strength of the bridge's materials. This is our clean, equalized signal amplitude, **`A_s`**.
*   The engineer has a detailed statistical report on all possible loads—traffic, wind, even rare events like earthquakes. This is our combined noise and interference PDF from the last chapter.

The engineer doesn't just check against the *average* load. They look at the statistical report and find the load level that has a very low probability of being exceeded (e.g., a 1-in-100,000-year event). This worst-case statistical load is our noise amplitude, **`A_ni`**.

The final safety margin of the bridge is the ratio of its strength (`A_s`) to the worst-case load it's designed to handle (`A_ni`). This safety margin is exactly what **COM** represents for our channel.

## The Core Concepts

Let's break down the three key ingredients of this final calculation.

### 1. Signal Amplitude (`A_s`)

This is the value we worked so hard to get in [Chapter 4](04_equalizer_optimization___optimize_fom_.md). It's the peak amplitude of our perfectly equalized pulse response. It represents the strength of our signal under ideal, noise-free conditions.

### 2. Statistical Noise Amplitude (`A_ni`)

This is the clever part. We don't use the average or RMS noise. We use our target **Bit Error Rate (`specBER`)** from the [`param`](01_configuration_and_control_structures___param____op___.md) structure to define our noise threshold.

We go to the **Cumulative Distribution Function (CDF)** of the total noise (which we created in [Chapter 5](05_interference___noise_pdf_generation_.md)) and ask a simple question:

> "At what noise voltage level is there a `specBER` probability that the actual noise will be even worse than this?"

The answer to that question is `A_ni`. It is the noise "budget" we have to work with. If the actual noise exceeds `A_ni`, we expect to get a bit error. The CDF tells us this will happen with a probability equal to our target `specBER`.

```mermaid
xychart-beta
    title "Finding A_ni from the Cumulative Distribution Function (CDF)"
    x-axis "Noise Voltage (V)" [0, 0.035]
    y-axis "Cumulative Probability" [0, 2e-5]
    line [
        0.00, 1e-12,
        0.01, 1e-9,
        0.02, 1e-7,
        0.03, 1e-5,
        0.035, 2e-5
    ]
    annotation "Target BER" {
        x: 0.0, y: 1e-5,
        dx: 5, dy: 0,
        text: "param.specBER = 1e-5"
    }
    annotation "arrow_y" {
        x: 0.0, y: 1e-5,
        dx: 130, dy: 0,
        text: "→"
    }
    annotation "arrow_x" {
        x: 0.03, y: 1e-5,
        dx: 0, dy: -55,
        text: "↓"
    }
    annotation "A_ni label" {
        x: 0.03, y: 0,
        dx: 0, dy: -10,
        text: "A_ni"
    }
```
As the diagram shows, we find our target BER on the probability axis, trace it over to the CDF curve, and then trace down to find the corresponding noise voltage, `A_ni`.

### 3. The COM Calculation

With `A_s` and `A_ni` in hand, the calculation for COM is simple. It's the ratio of the two, expressed in decibels (dB):

**`COM (dB) = 20 * log10( A_s / A_ni )`**

*   If **COM > Pass Threshold** (e.g., 3 dB), the channel **PASSES**. The signal is significantly stronger than the noise floor required for the target BER. We have a healthy "safety margin."
*   If **COM < Pass Threshold**, the channel **FAILS**. The signal is too weak to be reliably detected in the presence of the noise.

## Other Metrics: VEO and VEC

COM is the main result, but other useful metrics are also calculated at this stage.

*   **Vertical Eye Opening (VEO):** This measures the height of the "eye diagram" opening in millivolts at the target BER. A bigger opening is better. It's calculated directly from our two amplitudes:
    `VEO_mV = 1000 * (A_s - A_ni) * 2`

*   **Vertical Eye Closure (VEC):** This is just another way to express the same information, often used in different standards. It measures how much the eye is closed relative to the ideal signal height.

## Under the Hood: The Final Lines of Code

This entire process happens in just a few lines in the main script, `com_ieee8023_4p10p0_beta1.m`, right after the noise PDF has been created.

Here is a simplified look at the code:

```matlab
% --- File: com_ieee8023_4p10p0_beta1.m ---

% ... code to create combined_interference_and_noise_cdf from Chapter 5 ...

% STEP 1: Find the index in the CDF array that corresponds to our target BER.
% This finds the first element in the CDF that is greater than the specBER.
A_ni_ix = find(combined_interference_and_noise_cdf > param.specBER, 1, 'first');

% STEP 2: Use that index to look up the corresponding voltage. This is A_ni.
% We use the PDF's x-axis, which holds the voltage values for each bin.
A_ni = abs(combined_interference_and_noise_pdf.x(A_ni_ix));

% STEP 3: Calculate COM using the formula.
% A_s comes from the equalizer optimization results.
COM = 20*log10(A_s/A_ni);

% STEP 4: Calculate other metrics like VEO.
VEO_mV = 1000*(A_s - A_ni)*2;

% ... code to report the final results ...
```

That's it! The logic is a direct translation of the concepts we just discussed. The code finds the statistical noise floor `A_ni` and compares it to the signal strength `A_s` to produce the final COM value.

## Conclusion

In this chapter, we've reached the summit of our COM simulation journey. We learned how the final performance metrics are calculated, tying together the work from all previous chapters.

-   The final metric, **Channel Operating Margin (COM)**, is a signal-to-noise ratio expressed in decibels.
-   It's calculated by comparing the equalized signal amplitude (`A_s`) to the statistical noise amplitude (`A_ni`).
-   `A_ni` is not an average; it's the specific noise level derived from the total noise **CDF** that corresponds to our target **Bit Error Rate**.
-   A COM value greater than the standard's pass threshold (e.g., 3 dB) means the channel performs well enough to meet the target BER.
-   Other important metrics like **VEO** are also calculated from `A_s` and `A_ni`.

You have now walked through the entire COM algorithm, from initial configuration to the final result. You've seen how a complex physical system is modeled, how its impairments are corrected, and how a rigorous statistical analysis provides a clear, quantitative measure of its performance. Congratulations

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)