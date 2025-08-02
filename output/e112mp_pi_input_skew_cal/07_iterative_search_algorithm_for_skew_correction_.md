# Chapter 7: Iterative Search Algorithm for Skew Correction

Welcome to Chapter 7! In our [previous chapter on Skew Correlation Measurements (E21, E31, E41)](06_skew_correlation_measurements__e21__e31__e41_.md), we learned how our system can cleverly measure the amount of skew between its critical [Quadrature Clocks (clk0, clk90, clk180, clk270)](03_quadrature_clocks__clk0__clk90__clk180__clk270__.md). We now have these E-values (E21, E31, E41) that tell us if our clocks are out of sync.

But just knowing there's a problem isn't enough – we need to fix it! How does the system automatically find the *best* setting to correct this skew? It uses a smart, step-by-step method called the **Iterative Search Algorithm for Skew Correction**.

## The Quest for the Perfect "Key"

Imagine you have a very complex lock with many tiny dials, and you need to find the exact combination to open it. You wouldn't just spin the dials randomly, right? You'd probably try a combination, see if it works, and if not, make a small, methodical change and try again.

The "Iterative Search Algorithm" in our `e112mp_pi_input_skew_cal` project works much like this.
*   The "lock" is the clock skew problem.
*   The "dials" correspond to something called a [Skew Correction Code](08_skew_correction_code_.md) – a digital value that tells the [PMIX (Phase Mixer)](04_pmix__phase_mixer_.md) how to adjust its internal timing.
*   The "try a combination and see if it works" part involves:
    1.  Applying a specific Skew Correction Code.
    2.  Measuring the resulting clock skew using the E21, E31, E41 values we learned about.
    3.  Checking if the skew is fixed, or at least better.
*   If not fixed, the algorithm intelligently adjusts the Skew Correction Code (like turning the dial a little) and repeats the process.

This "try, measure, adjust, repeat" cycle is what "iterative" means. It's a search because the algorithm is systematically looking for the one Skew Correction Code that makes the clocks perfectly aligned.

## Why "Iterative Search"?

Why not just calculate the perfect correction in one go?
*   **Complexity:** The relationship between the Skew Correction Code and its effect on the actual clock timing can be complex, influenced by many tiny physical factors in the chip. A direct calculation might be too difficult or imprecise.
*   **Adaptability:** An iterative search can adapt to the specific conditions of each individual chip, which might have slight variations from manufacturing.

So, a step-by-step search, guided by measurements, is a robust way to find the best solution.

## The Core Idea: Measure, Adjust, Repeat

Let's break down the key ingredients of this search:

1.  **The Goal:** To find the optimal [Skew Correction Code](08_skew_correction_code_.md). This code will be programmed into the [PMIX (Phase Mixer)](04_pmix__phase_mixer_.md) to counteract any existing skew in its input clocks.

2.  **The "Knob" We Turn:** The **Skew Correction Code**. This is a digital number. The algorithm will try different values for this code.

3.  **The "Meter" We Read:** The [Skew Correlation Measurements (E21, E31, E41)](06_skew_correlation_measurements__e21__e31__e41_.md). These tell us how much skew is present for a given Skew Correction Code.

4.  **A Special Test Condition: Checking at Different PI Settings**
    This is a very important part! The [PMIX (Phase Mixer)](04_pmix__phase_mixer_.md) can adjust the overall phase of the sampling clock. This adjustment is controlled by a "PI code." Our algorithm doesn't just check the skew at one PI code setting. Instead, it measures the skew (using E21, E31, E41) at *two different* PI code settings. Typically, these are:
    *   **PI Code 0:** This might correspond to a 0-degree phase shift by the PMIX.
    *   **PI Code 64:** This might correspond to a 90-degree phase shift by the PMIX. (The exact values and degrees can vary, but the key is they are distinct.)

    **Why check at two different PI settings?**
    We want the skew correction to be effective *no matter how the PMIX is currently set*. If we only optimized for PI code 0, the correction might mess things up when the PMIX is set to PI code 64.
    The algorithm's true goal is to find a Skew Correction Code that makes the *measured skew values (E21, E31, E41) as similar as possible* when measured at PI code 0 versus when measured at PI code 64. When these measurements are very close to each other (and ideally, the E-values themselves are small), it indicates the clocks are well-aligned and the PMIX can operate linearly across its range.

    As the project documentation (`e112mp_pi_input_skew_cal.pdf`, Page 3) states:
    > "The resultant skew is collected at PI code 0 (phase offset 0) and 64 (phase offset 90) and compared. If skew measurements are the same for PI code 0 and 64, skew code is found, otherwise keep stepping the code until it is."

## The Algorithm Step-by-Step

Let's walk through how this search algorithm typically works:

1.  **Initialization:** The algorithm starts by choosing an initial [Skew Correction Code](08_skew_correction_code_.md) to try. This could be zero, or a mid-range value.

2.  **Measure at PI Code 0:**
    *   The system applies the current Skew Correction Code to the [PMIX (Phase Mixer)](04_pmix__phase_mixer_.md).
    *   It sets the PMIX to operate with **PI Code 0**.
    *   It then uses the [Loopback Test Signal and ADC](05_loopback_test_signal_and_adc_.md) and the [Skew Correlation Measurements (E21, E31, E41)](06_skew_correlation_measurements__e21__e31__e41_.md) to get the skew values (let's call them `E21_pi0`, `E31_pi0`, `E41_pi0`). Remember these are averaged to reduce noise.

3.  **Measure at PI Code 64:**
    *   Keeping the *same* Skew Correction Code, the system now sets the PMIX to operate with **PI Code 64**.
    *   It measures the skew values again (let's call them `E21_pi64`, `E31_pi64`, `E41_pi64`).

4.  **Compare the Measurements:** The algorithm now compares the skew measurements from the two PI settings. For example, it looks at:
    *   How different is `E21_pi0` from `E21_pi64`?
    *   How different is `E31_pi0` from `E31_pi64`?
    *   How different is `E41_pi0` from `E41_pi64`?
    The goal is for these differences to be as close to zero as possible.

5.  **Decision Time:**
    *   **Is the match good enough?** If the differences calculated in step 4 are very small (e.g., below a tiny predefined threshold), it means the current Skew Correction Code is doing a great job! The clocks are well-aligned, and this alignment holds up even when the PMIX's main phase setting changes. The algorithm has found the optimal code, and the calibration can stop.
    *   **Not good enough?** If the differences are still too large, the current Skew Correction Code isn't the best one. The algorithm needs to try another.

6.  **Adjust and Repeat:**
    *   The algorithm "intelligently adjusts" the Skew Correction Code. This usually means "stepping" it – for example, incrementing it by one (or a small step).
    *   It then **loops back to Step 2** with the new Skew Correction Code and tries again.

This loop continues, systematically trying Skew Correction Codes, until it finds one that makes the skew measurements consistent across PI code 0 and PI code 64.

```mermaid
graph TD
    A[Start: Pick Initial Skew Correction Code (SCC)] --> B{Set PMIX to PI Code 0};
    B --> C{Measure Skew (E_pi0 values)};
    C --> D{Set PMIX to PI Code 64 (Keep same SCC)};
    D --> E{Measure Skew (E_pi64 values)};
    E --> F{Compare E_pi0 and E_pi64 values.<br>Are differences minimal?};
    F -- No --> G{Adjust Skew Correction Code (e.g., increment)};
    G --> B;
    F -- Yes --> H[Optimal Skew Correction Code Found! Calibration Done.];
end
```

## A Simplified Look "Under the Hood" (Conceptual Code)

Let's imagine some very simplified pseudo-code to get the feel for this loop. (This is not actual hardware code, just for understanding!)

```
// --- Configuration ---
MAX_SKEW_CODE_VALUE = 127; // Example: Skew code might be 7 bits
PI_CODE_SETTING_1 = 0;
PI_CODE_SETTING_2 = 64;
ACCEPTABLE_DIFFERENCE = 0.05; // Example: A very small target difference

// --- Algorithm ---
current_skew_code = 0; // Start with SCC = 0
found_optimal_code = false;

while (current_skew_code <= MAX_SKEW_CODE_VALUE and not found_optimal_code):
    // 1. Apply current skew_code
    set_pmix_skew_correction_code(current_skew_code);

    // 2. Measure at PI Code Setting 1
    set_pmix_pi_code(PI_CODE_SETTING_1);
    // Get averaged E21, E31, E41 values
    e21_pi_setting1 = measure_averaged_e21();
    // ... (similar for e31_pi_setting1, e41_pi_setting1)

    // 3. Measure at PI Code Setting 2
    set_pmix_pi_code(PI_CODE_SETTING_2);
    // Get averaged E21, E31, E41 values
    e21_pi_setting2 = measure_averaged_e21();
    // ... (similar for e31_pi_setting2, e41_pi_setting2)

    // 4. Compare
    difference_e21 = absolute_value(e21_pi_setting1 - e21_pi_setting2);
    // ... (calculate differences for E31, E41 too)

    // For simplicity, let's just check E21's difference for the decision
    // In reality, all E-values (or a combined metric) would be considered.
    if (difference_e21 < ACCEPTABLE_DIFFERENCE):
        // And other E-value differences are also small...
        found_optimal_code = true;
        print("Optimal Skew Correction Code found:", current_skew_code);
    else:
        // 5. Adjust and Repeat
        current_skew_code = current_skew_code + 1; // Step to the next code
        print("Trying next Skew Correction Code:", current_skew_code);

if (not found_optimal_code):
    print("Could not find optimal code within search range.");
```

**Explanation of the Conceptual Code:**

*   We have some initial settings, like the range of possible Skew Correction Codes and what we consider an "acceptable difference."
*   The `while` loop is the heart of the iterative process. It keeps running as long as we haven't found the optimal code and haven't run out of codes to try.
*   Inside the loop:
    *   We apply the `current_skew_code`.
    *   We measure the E-values at `PI_CODE_SETTING_1` (e.g., PI code 0).
    *   We measure the E-values at `PI_CODE_SETTING_2` (e.g., PI code 64).
    *   We calculate the `difference` between these measurements.
    *   If the `difference` is small enough, we declare `found_optimal_code` to be `true`, and the loop will stop.
    *   Otherwise, we increment `current_skew_code` to try the next value in the next iteration.

This systematic "stepping" through possible codes and checking the result is the essence of the iterative search. The actual hardware implementation will be far more optimized and work with digital logic, but the core principle is the same.

## Why This Matters

This iterative search algorithm is the "brains" behind the automatic calibration. It ensures that:
*   The [PMIX (Phase Mixer)](04_pmix__phase_mixer_.md) gets the best possible correction for any incoming clock skew.
*   This correction is robust and works well across different operational settings of the PMIX.
*   Ultimately, this leads to more accurate data reception, better signal quality, and fewer errors, as we discussed in the [first chapter on PI Input Skew Calibration](01_pi_input_skew_calibration_.md).

## What We've Learned

In this chapter, we've dived into the **Iterative Search Algorithm for Skew Correction**:
*   It's a methodical, step-by-step procedure the system uses to find the best [Skew Correction Code](08_skew_correction_code_.md).
*   It's like trying different keys on a complex lock until it opens.
*   The process involves:
    1.  Applying a Skew Correction Code.
    2.  Measuring skew (using E21, E31, E41) at two different PMIX PI settings (e.g., PI code 0 and PI code 64).
    3.  Comparing these two sets of skew measurements.
    4.  If the measurements are very similar (differences are minimal), the current code is optimal.
    5.  If not, the algorithm adjusts the code (e.g., steps to the next value) and repeats the process.
*   This ensures the clock skew is corrected effectively across the PMIX's operating range.

This algorithm works to find a specific digital value – the Skew Correction Code. What exactly *is* this code and how does it achieve the correction inside the PMIX? Let's explore that in our next and final chapter for this topic!

Join us in: [Skew Correction Code](08_skew_correction_code_.md)

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)