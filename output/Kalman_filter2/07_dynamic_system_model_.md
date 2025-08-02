# Chapter 7: Dynamic System Model

In [Chapter 6: Prediction Phase](06_prediction_phase_.md), we saw that the Kalman Filter makes an educated guess about where the system is headed. It predicts the next state and how uncertain that prediction is. But how does the filter know *how* the system is supposed to move or change on its own? How does it understand the "physics" or "rules" governing the system?

This is where the **Dynamic System Model** comes in. It's the rulebook the Kalman Filter uses to understand how the system behaves over time.

## What is the Dynamic System Model? The System's Rulebook

Imagine you're tracking a simple toy car rolling across a flat floor.
*   If you know its current **position** and **velocity** (its [System State (State Variables)](02_system_state__state_variables__.md)).
*   And you know a basic physics rule: `new_position = old_position + velocity * time_step`.

You can predict where the car will be a moment later. This rule, `new_position = old_position + velocity * time_step`, is a very simple example of a dynamic system model.

The **Dynamic System Model** (often just called the "system model" or "process model") is a set of mathematical equations that describe how the true state of a system evolves from one time step to the next. The Kalman Filter relies heavily on this model during its [Prediction Phase](06_prediction_phase_.md) to forecast what the system will do next.

This model usually includes:
1.  How the system changes on its own (its internal dynamics).
2.  How any known external controls or forces affect it.
3.  The inherent unpredictability or randomness in the system's behavior.

Let's break these parts down.

## 1. How the System Changes on Its Own: The State Transition Matrix (F)

The core of the dynamic system model tells us how the system's state variables would change from one time step (`k-1`) to the next (`k`) if there were no external controls and no random disturbances. This is often represented by a **State Transition Matrix**, usually denoted as **F**.

If our state vector at time `k-1` is `x_{k-1}`, then `F` helps us predict the state at time `k` like this (for now, ignoring controls and noise):
`predicted_state_at_k ≈ F * state_at_{k-1}`

**Example: Our 1D Moving Dot**
Let's say our dot only moves horizontally, and its state `x` is `[position, velocity]`.
Let `dt` be the small amount of time between step `k-1` and step `k`.

A simple model for our dot could be:
*   `new_position = old_position + old_velocity * dt`
*   `new_velocity = old_velocity` (assuming constant velocity, for now)

We can write this in matrix form:
`[new_position]` = `[1 * old_position + dt * old_velocity]`
`[new_velocity]` = `[0 * old_position +  1 * old_velocity]`

So, the State Transition Matrix `F` would be:
```
F = [[1, dt],
     [0,  1]]
```

If our state at `k-1` (`x_{k-1|k-1}`) was `[10.0, 2.0]` (position 10, velocity 2) and `dt = 0.5 sec`, then:
`F * x_{k-1|k-1} = [[1, 0.5], [0, 1]] * [10.0, 2.0]^T = [11.0, 2.0]^T`
This predicts the new position will be 11.0, and velocity will remain 2.0.

This `F` matrix is crucial. You, as the designer, need to define it based on your understanding of how the system you're tracking behaves.

## 2. How External Controls Affect the System: The Control Input Model (B) and Control Vector (u)

Sometimes, we know about external forces or controls acting on our system.
*   For a car, this could be the accelerator or brakes.
*   For a robot arm, it's the motor commands.
*   For our dot, maybe we have a joystick that applies a known acceleration.

If these controls are known, we can include them in our model to make our predictions more accurate.
*   The **Control Vector (u)**: This vector contains the values of our known control inputs. For example, `u_k = [acceleration_applied_at_step_k]`.
*   The **Control Input Model (B)**: This matrix tells us how each control input in `u_k` affects each state variable.

The full equation for state prediction (still ignoring noise for a moment) becomes:
`predicted_state_at_k ≈ F * state_at_{k-1} + B * control_vector_u_k`

**Example: Our 1D Dot with Controlled Acceleration**
Let our state `x` still be `[position, velocity]`.
The `F` matrix is as before: `[[1, dt], [0, 1]]`.
Now, suppose we apply a known acceleration `accel_k` using a joystick. So, our control vector `u_k = [accel_k]`.

How does `accel_k` affect position and velocity over a time step `dt`?
*   Change in velocity: `accel_k * dt`
*   Change in position: `0.5 * accel_k * dt^2` (from basic physics: `Δp = v_0*t + 0.5*a*t^2`, here `v_0*t` is handled by F, so we add the acceleration part)

So the `B * u_k` term should add `[0.5 * dt^2 * accel_k, dt * accel_k]^T` to our state.
This means the `B` matrix (which multiplies `u_k = [accel_k]`) must be:
```
B = [[0.5 * dt^2],
     [dt        ]]
```
If `dt = 0.5 sec` and we apply `accel_k = 4.0 units/sec^2`:
`B * u_k = [[0.5 * 0.5^2], [0.5]] * [4.0] = [[0.125], [0.5]] * [4.0] = [[0.5], [2.0]]^T`
This means the control input adds 0.5 to the position and 2.0 to the velocity.

If there are no known control inputs, the `B * u_k` term is simply zero or omitted.

## 3. Unpredictability in the System: Process Noise Covariance (Q)

Our models (`F` and `B`) are rarely perfect. Real-world systems are messy!
*   Our toy car might hit a tiny bump we didn't model.
*   A gust of wind might nudge our drone slightly.
*   The motors in our robot might not respond exactly as commanded.

These are small, unpredictable disturbances or unmodeled forces that cause the actual system to behave slightly differently than our `F * x + B * u` prediction. This inherent unpredictability in the system's *evolution* is called **Process Noise**.

The Kalman Filter accounts for this by adding a **Process Noise Covariance Matrix (Q)** when it predicts the new uncertainty. In [Chapter 6: Prediction Phase](06_prediction_phase_.md), we saw the equation for the predicted error covariance:
`P_{k|k-1} = F_k * P_{k-1|k-1} * F_k^T + Q_k`

The `Q_k` term ensures that even if we were very certain about our previous state (`P_{k-1|k-1}` was small), our uncertainty about the *next* state (`P_{k|k-1}`) will increase because our model of how things change isn't perfect.

*   **What `Q` represents**: It's a covariance matrix that describes the uncertainty of our dynamic model. A larger `Q` means we think our model (`F` and `B`) is less reliable or that the system is subject to larger random disturbances.
*   **Defining `Q`**: This can be one of the trickiest parts of setting up a Kalman Filter. It often involves understanding the physics of unmodeled forces or making educated guesses based on how much the system tends to deviate from the model.

**Example: Process Noise for the 1D Dot**
Let's say we believe our dot experiences small, random accelerations that are not part of our control input `u_k`. Let `a_rand` be this random acceleration, and we assume it's constant over the small interval `dt`, with a mean of 0 and a variance of `sigma_a^2`.

This random acceleration `a_rand` will cause:
*   A random change in velocity: `dv_rand = a_rand * dt`
*   A random change in position: `dp_rand = 0.5 * a_rand * dt^2`

The process noise vector `w_k` represents these random changes: `w_k = [dp_rand, dv_rand]^T`.
We can write `w_k = G_noise * a_rand`, where `G_noise = [[0.5 * dt^2], [dt]]^T`.
The covariance matrix `Q_k` is then `E[w_k * w_k^T]`.
If `a_rand` has variance `sigma_a^2`, then:
`Q_k = G_noise * sigma_a^2 * G_noise^T`
```
Q_k = [[0.5 * dt^2],  * sigma_a^2 * [0.5 * dt^2, dt]
       [dt        ]]

     = [[0.25 * dt^4,   0.5 * dt^3 ],
        [0.5 * dt^3 ,         dt^2   ]] * sigma_a^2
```
This `Q_k` matrix tells the filter how much "fuzziness" to add to its predicted covariance due to these unmodeled random accelerations. For instance, if `dt=0.5` and `sigma_a^2 = 0.04` (as in the example from Chapter 6), `Q_k` would be `[[0.000625, 0.0025],[0.0025, 0.01]]`.
The exact derivation of `Q` can be complex, but the key idea is that it injects uncertainty into your state estimate during prediction because your model of the world isn't perfect.

## Putting It All Together: The Full Dynamic System Model Equation

The true state of the system `x_k` at time `k` is thought to evolve from the state `x_{k-1}` at time `k-1` according to:
`x_k = F_k * x_{k-1} + B_k * u_k + w_k`

Where:
*   `x_k`: The true state at time `k`.
*   `F_k`: The state transition matrix (how state evolves naturally).
*   `x_{k-1}`: The true state at time `k-1`.
*   `B_k`: The control input model matrix.
*   `u_k`: The known control input vector.
*   `w_k`: The process noise vector (unpredictable disturbances). This `w_k` is a random variable with mean zero and covariance `Q_k`. (i.e., `w_k ~ N(0, Q_k)`).

The Kalman Filter uses `F_k`, `B_k`, `u_k`, and `Q_k` in its [Prediction Phase](06_prediction_phase_.md) to estimate `x_k` (as `x̂_{k|k-1}`) and its uncertainty `P_{k|k-1}`.

## Defining Your System Model: It's About Understanding Your System!

When you use a Kalman filter, a significant part of your job is to define these matrices: `F`, `B` (if applicable), and `Q`. This requires you to:
1.  Choose your [System State (State Variables)](02_system_state__state_variables__.md) (what are you trying to track?).
2.  Understand the physics or rules governing how these state variables change over time. This helps define `F`.
3.  Identify any known control inputs and how they affect the state. This helps define `B` and `u`.
4.  Estimate the magnitude and nature of unmodeled disturbances or model inaccuracies. This helps define `Q`.

This "modeling" step is crucial for the filter to perform well. If your model is a poor representation of reality, the filter's estimates won't be as good.

### Conceptual Code Representation

Let's look at how we might define these matrices conceptually. This isn't code the filter *runs* to get the model, but rather how *you* might set up the model parameters for the filter to use.

```python
import numpy as np

# For our 1D dot with state x = [position, velocity]
dt = 0.5 # Time step in seconds

# --- State Transition Matrix (F) ---
# Assumes: new_pos = old_pos + old_vel * dt
#          new_vel = old_vel
F = np.array([[1.0,  dt],
              [0.0, 1.0]])
print(f"F (State Transition Matrix):\n{F}\n")

# --- Control Input Model (B) and Control Vector (u) ---
# (Optional: if we have known controls, e.g., a known acceleration)
# Let's say we apply a known acceleration of accel_val = 1.5 units/sec^2
accel_val = 1.5
u = np.array([accel_val]) # Control vector

# B translates control input (acceleration) to changes in state [pos, vel]
# Change in pos = 0.5 * accel * dt^2
# Change in vel = accel * dt
B = np.array([[0.5 * dt**2],  # Effect of accel on position
              [dt         ]]) # Effect of accel on velocity
print(f"B (Control Input Model Matrix):\n{B}")
print(f"u (Control Vector): {u}\n")

# --- Process Noise Covariance (Q) ---
# Represents uncertainty in the model (e.g., unmodeled random accelerations)
# Let's assume random accelerations have a variance of sigma_a_sq = 0.1 units^2/sec^4
sigma_a_sq = 0.1
# Q based on G_noise * sigma_a_sq * G_noise.T where G_noise = [[0.5*dt^2], [dt]]
# (This is one way to derive Q; others exist based on system knowledge)
G_noise = np.array([[0.5 * dt**2],
                    [dt]])
Q = G_noise @ G_noise.T * sigma_a_sq
# Q = np.array([[0.25 * dt**4, 0.5 * dt**3],
#               [0.5 * dt**3 ,       dt**2  ]]) * sigma_a_sq
print(f"Q (Process Noise Covariance Matrix):\n{Q}")
```

**Explanation:**
*   **`F`**: Defines how position and velocity would change if there were no controls or random noise. Here, position changes based on velocity, and velocity stays constant (in this part of the model).
*   **`u` and `B`**: If we command an acceleration `accel_val`, `u` holds this value. `B` tells us how this commanded acceleration will specifically change the position and velocity over `dt`.
*   **`Q`**: This matrix reflects our uncertainty about the model. Even if `u` was zero, the actual dot might not perfectly follow `x_k = F * x_{k-1}`. For example, tiny, unmodeled forces (like air currents for a very light dot) could cause random accelerations. `Q` quantifies the expected variance of these random effects on the state. The `sigma_a_sq` represents how "strong" these random accelerations are assumed to be.

These `F`, `B`, and `Q` matrices (along with the latest state estimate `x̂_{k-1|k-1}` and its covariance `P_{k-1|k-1}`) are exactly what the Kalman Filter uses in its [Prediction Phase](06_prediction_phase_.md) equations:
1.  `x̂_{k|k-1} = F * x̂_{k-1|k-1} + B * u_k`  (Predicts the next state)
2.  `P_{k|k-1} = F * P_{k-1|k-1} * F^T + Q` (Predicts the uncertainty of that new state)

The Dynamic System Model is your description of these rules and uncertainties to the filter.

## Visualizing the Model's Role

Imagine the state `x_{k-1}` as a point. The Dynamic System Model tells the filter how to move this point and its uncertainty to a new predicted point for time `k`.

```mermaid
graph LR
    subgraph "Time k-1"
        X_km1["State x̂<sub>k-1|k-1</sub><br>(e.g., position, velocity)"]
    end

    subgraph "Dynamic System Model (Your 'Rulebook')"
        F_matrix["F <br> (How state changes <br> on its own)"]
        B_u_term["B * u<sub>k</sub> <br> (Effect of known controls)"]
        Q_matrix["Q <br> (Uncertainty in model <br> / random disturbances)"]
    end
    
    X_km1 -->|Multiplied by F| Step1_F_applied["x' = F * x̂<sub>k-1|k-1</sub>"]
    Step1_F_applied -->|Add control effect| Step2_B_u_added["x'' = x' + B * u<sub>k</sub> <br> This is x̂<sub>k|k-1</sub>"]
    
    note right of Step2_B_u_added
        The covariance P also evolves:
        P<sub>k|k-1</sub> = F * P<sub>k-1|k-1</sub> * F<sup>T</sup> + Q
        Q from the model makes P<sub>k|k-1</sub> larger,
        reflecting model uncertainty.
    end

    Step2_B_u_added --> Output[To Prediction Phase Output:<br>x̂<sub>k|k-1</sub>, P<sub>k|k-1</sub>]
    
    style F_matrix fill:#lightcyan,stroke:#333
    style B_u_term fill:#lightcyan,stroke:#333
    style Q_matrix fill:#lightcyan,stroke:#333
```
The model (`F`, `B`, `Q`) you define is used by the Kalman filter to make these predictions. `F` and `B` determine where the state *should* go, while `Q` acknowledges that this prediction isn't perfect and adds to the uncertainty.

## Conclusion

The **Dynamic System Model** is the Kalman Filter's understanding of how the system being tracked behaves. It's composed of:
*   The **State Transition Matrix (F)**, describing the system's natural evolution.
*   The **Control Input Model (B) and Control Vector (u)**, describing the effect of known external influences (if any).
*   The **Process Noise Covariance (Q)**, quantifying the uncertainty in this model due to unmodeled effects or random disturbances.

You, the user of the Kalman Filter, are responsible for defining this model based on your knowledge of the system. A good model is key to good filter performance. This model provides the essential `F`, `B` (if used), and `Q` matrices that drive the [Prediction Phase](06_prediction_phase_.md) of the filter.

Now that we've predicted where the system might be and how uncertain we are, what happens when we get a new, actual measurement from our sensors? That's the topic of our next chapter: the [Update Phase](08_update_phase_.md).

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)