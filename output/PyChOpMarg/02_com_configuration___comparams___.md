# Chapter 2: COM Configuration (`COMParams`)

Welcome back! In [Chapter 1: Command-Line Interface (CLI)](01_command_line_interface__cli__.md), we saw how to use the terminal to run basic `PyChOpMarg` tasks. Now, let's dive into one of the core concepts needed for actual simulations: defining the **COM Configuration**, which we represent using an object called `COMParams`.

## What's the Problem? Setting the Stage for Simulation

Imagine you want to test if a high-speed communication link (like the connection between chips on a circuit board) will work reliably according to a specific industry standard (like Ethernet). Just knowing the physical path isn't enough. You also need to know:

*   How fast should the signals be? (Baud Rate)
*   How much noise is allowed?
*   What kind of signal processing (equalization) can the receiver use to clean up the signal?
*   What are the limits on that signal processing?
*   What tiny electrical effects (parasitics) from the chip packages need to be included?
*   How low does the error rate need to be?

Different standards (e.g., IEEE 802.3dj for 200 Gb/s per lane, or 802.3by for 25 Gb/s) have different answers to these questions. We need a way to neatly package all these rules and conditions *before* we can run a simulation.

## The Solution: `COMParams` - The Recipe Card

This is where `COMParams` comes in! Think of `COMParams` as a detailed **recipe card** or a **settings screen** for a Channel Operating Margin (COM) calculation. It's a data structure in `PyChOpMarg` that holds *all* the necessary parameters defined by a specific IEEE standard.

*   **It's a Template:** All standards use the same *structure* or *template* for these parameters.
*   **It Holds Values:** For a *specific* standard (like 802.3dj), this template is filled with the exact values required by that standard.
*   **It Defines the "How":** It tells the [COM Calculation Engine (`COM` class)](04_com_calculation_engine___com__class__.md) precisely how to perform the simulation, what limits to respect, and what conditions to assume.

Here are some examples of the "ingredients" listed on this recipe card:

*   `fb`: The baud rate (signal speed) in GigaBaud.
*   `SNR_TX`: Allowed signal-to-noise ratio from the transmitter (in dB).
*   `g_DC`, `g_DC2`: Gain settings for the receiver's continuous-time linear equalizer (CTLE).
*   `tx_taps_min`, `tx_taps_max`: Limits on the transmitter's equalizer settings.
*   `C_d`, `L_s`: Capacitance and inductance values representing the chip package.
*   `DER_0`: The target Detector Error Ratio (how many errors are acceptable).

## Using `COMParams` in PyChOpMarg

You usually won't create a `COMParams` object from scratch. Instead, `PyChOpMarg` comes with pre-defined configurations for common IEEE standards. You simply import the one you need.

Let's see how to load the parameters for the IEEE 802.3dj standard:

```python
# Import the pre-defined parameters for IEEE 802.3dj
from pychopmarg.config.ieee_8023dj import IEEE_8023dj

# The 'IEEE_8023dj' object now holds all the parameters
# Let's print a couple of them to see
print(f"Standard: IEEE 802.3dj")
print(f"Baud Rate (fb): {IEEE_8023dj.fb} GBaud")
print(f"Target Error Ratio (DER_0): {IEEE_8023dj.DER_0}")
print(f"Number of DFE Taps (len(dfe_max)): {len(IEEE_8023dj.dfe_max)}")

# You would then pass this 'IEEE_8023dj' object to the COM calculation engine
# (More on this in Chapter 4!)
```

**What happens?**

1.  We import `IEEE_8023dj` from a specific configuration file within `PyChOpMarg`.
2.  This creates a `COMParams` object filled with the values specified by the 802.3dj standard.
3.  We can access individual parameters like `fb` (baud rate) or `DER_0` (target error ratio) using dot notation (e.g., `IEEE_8023dj.fb`).
4.  Later, in [Chapter 4: COM Calculation Engine (`COM` class)](04_com_calculation_engine___com__class__.md), we will pass this entire `IEEE_8023dj` object to the main COM calculator to tell it *how* to run the analysis.

Similarly, if you were working with the 802.3by standard, you would import `IEEE_8023by` from `pychopmarg.config.ieee_8023by`.

## Under the Hood: Dataclasses and Defaults

How does `PyChOpMarg` store these parameters internally?

1.  **The Template (`COMParams`):** The structure is defined using a Python feature called a `dataclass`. Think of a `dataclass` as a blueprint for creating simple objects whose main purpose is to hold data fields. The definition lives in `src/pychopmarg/config/template.py`. It lists all the possible parameter *names* and their expected *types* (like float, integer, list of floats).

    ```python
    # src/pychopmarg/config/template.py (Simplified Snippet)
    from dataclasses import dataclass
    import numpy as np
    from pychopmarg.common import Rvec # Rvec is like a list/array of floats

    @dataclass() # This marks it as a dataclass
    class COMParams():
        """Template definition for COM parameters."""
        # General
        fb: float                   # (GBaud) - Baud Rate
        M: int                      # samples per UI
        DER_0: float                # target detector error ratio
        # ... many more parameters ...

        # Rx EQ (Example: DFE limits)
        dfe_min: Rvec               # Min values for DFE taps
        dfe_max: Rvec               # Max values for DFE taps

        # Package (Example: Capacitance)
        C_d: list[float]            # Die capacitance (nF)

        # ... many more parameters ...

        def __post_init__(self):
            """Validate incoming COM parameters."""
            # This special method runs after creation
            # to check if values are reasonable (e.g., fb > 0)
            # (Implementation details omitted for simplicity)
            pass
    ```

    This code defines the *empty* recipe card structure.

2.  **Filling the Template (Defaults):** For specific standards like 802.3dj, there are separate files (e.g., `src/pychopmarg/config/ieee_8023dj.py`) that *use* this `COMParams` template and fill it with the actual values defined in the standard.

    ```python
    # src/pychopmarg/config/ieee_8023dj.py (Simplified Snippet)
    import numpy as np
    from pychopmarg.config.template import COMParams # Import the template

    # Create an instance of the COMParams template, filling in the values
    IEEE_8023dj = COMParams(
        fb=106.25,          # Baud Rate set to 106.25 GBaud
        fstep=0.01,         # Frequency step
        L=4,                # 4 levels (PAM4 modulation)
        M=32,               # 32 samples per Unit Interval
        DER_0=2e-4,         # Target error rate
        # ... all other parameters filled in according to 802.3dj ...
        dfe_min=np.array([0.0]), # Example DFE min values
        dfe_max=np.array([0.85]),# Example DFE max values
        C_d=[4.0e-5, 9.0e-5, 1.1e-4], # Example Capacitance values
        # ... rest of the parameters ...
    )
    ```

    This code takes the empty `COMParams` blueprint and creates a specific "filled-in" recipe card named `IEEE_8023dj`.

3.  **Validation:** When a `COMParams` object is created (like `IEEE_8023dj` above), the special `__post_init__` method inside the `COMParams` class definition (in `template.py`) automatically runs some basic checks to make sure the provided values are within reasonable ranges, helping to catch potential typos or errors early.

So, when you import `IEEE_8023dj`, you're getting a pre-validated `dataclass` object containing all the settings needed to run a COM simulation according to that specific standard.

## Conclusion

You've now learned about `COMParams`, the crucial "recipe card" that defines all the settings and conditions for a COM calculation based on industry standards like IEEE 802.3. It bundles parameters like speed, noise, equalization limits, and physical properties into a single, convenient object. We saw how `PyChOpMarg` provides pre-filled `COMParams` objects for common standards, which you can easily import and use.

We know how to set the *rules* for the simulation (`COMParams`), but what about the actual physical path the signal travels through? In the next chapter, we'll explore how we represent the signal path itself.

Next: [Chapter 3: Signal Path Representation (S-parameters)](03_signal_path_representation__s_parameters__.md)

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)