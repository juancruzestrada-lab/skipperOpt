# Claude lab notebook

Written by the Claude optimizer at the end of each campaign and read at the start of the next one. Edit or delete entries freely.

## 2026-10-01 09:13 | module skipper | 30 measurements (30 new) | best F = 0.018867 at Vdd=-14.5, Vdrain=-18.8, Vr=-6.3, delay_H_overlap=21.0

**Best region.** The best results came from a tight cluster around Vdd −14.5 to −14.6, Vdrain −18.6 to −18.8, Vr −6.1 to −6.3, delay_H_overlap 20–21.

- Best single points: #20 (−14.5, −18.8, −6.3, 21) with F = 0.0189, and #22 (−14.6, −18.6, −6.1, 20) with F = 0.0198.
- The repeat of #20 (#21) gave 0.0229.
- Eleven points in this cluster (#20–30) all fell between 0.019 and 0.037, except #28 at 0.063, where gain dropped to 12k.
- Within the cluster, differences below about 0.01 are noise.

**Reproducibility problem.** Earlier repeats were badly irreproducible:

| Point | First F | Repeat F |
|---|---|---|
| #3 | 0.022 | 0.81 (#11), 4.5 (#17) |
| #7 | 0.038 | 1.7 (#13) |
| #6 | 0.12 | 9.0 (#15) |
| #1 | 0.35 | 100 (#18) |

Measurements #11–18 all had near-zero or negative gain. This suggests an episode where the LED or signal was lost, rather than a parameter effect. The cause is unknown.

**Broken or useless images.** These showed up as gain ≤ ~100 or negative gain, meaning the active median was at or below the overscan median, with noise_active ≈ noise_overscan.

- **Systematic failures:** Vdrain less negative than Vdd (#2, #4, #5) and the shallow corner Vdd −10.3 / Vr −5.2 (#8, gain 74).
- **Not obvious from overscan noise:** noise_overscan stayed at 690–1006 ADU throughout. Only #18 reached the top of that range (1006).

**Sensitivity.** F is driven almost entirely by gain, since overscan noise is roughly constant.

- **Most sensitive:** the Vdd/Vdrain relationship. Good points had Vdd ≈ −14.5 to −15 with Vdrain about 2–4 V more negative.
- **Least sensitive:** within the good region, delay 19–22 and Vr −6.0 to −6.4 showed no resolvable effect.

**Suggestions for the next campaign.**

- Start at (−14.5, −18.8, −6.3, 21).
- Narrow the bounds to Vdd −16 to −13, Vdrain −20 to −17, Vr −7 to −5.5, delay 17–25.
- Interleave periodic re-measurements of a reference point to detect LED or signal dropouts. Treat any gain < ~1000 as a suspect measurement rather than a parameter result.
- Check whether noise_overscan in electrons can be reduced at all. The current overscan noise of ~700 ADU dominates F.

## 2026-10-01 09:27 | module skipper | 30 measurements (30 new) | best F = 0.024221 at Vdd=-17.5, Vdrain=-20.2, Vr=-5.0, delay_H_overlap=30.0

**Best region.** The good cluster is Vdd −17.3 to −18.2, Vdrain −20.0 to −21.3 (about 2.5–3 V more negative than Vdd), Vr −5.0 to −5.7, delay 27–30. Fourteen points there (#14, #15, #17, #18, #20, #21, #23, #25–30) gave F = 0.024–0.036.

| Point | Settings (Vdd, Vdrain, Vr, delay) | F | Repeats / near-repeats |
|---|---|---|---|
| #18 (lowest) | (−17.5, −20.2, −5.0, 30) | 0.0242 | #20 gave 0.0352 |
| #21 (most reproducible) | (−17.5, −20.2, −5.7, 28) | 0.0270 | #28 0.0287, #30 0.0301 (mean ≈ 0.029) |
| #25 | (−17.6, −20.4, −5.4, 29) | 0.0257 | 0.030–0.036 |

- The scatter is about ±0.005 at a fixed setting. It comes from gain varying between 2.0e4 and 2.8e4 while overscan noise stays at about 700 ADU.
- Last campaign's best point (−14.5, −18.8, −6.3, 21) gave only 0.047 this time (#9, gain 1.45e4). Its earlier 0.019 was probably a lucky draw or reflects changed conditions.
- There was no LED-dropout episode this campaign. All plausible-region points had gain > 1.4e4.

**Broken or useless images.**
- **Vdrain less negative than Vdd** (#2, #4, #5): negative gain (−500 to −2300), F 0.3–1.3.
- **Shallow corner** (−10.3, −12.5, −5.2), #8: gain −55, F 16.
- **Shallow Vdd with very negative Vdrain and Vr ≈ −7.5 to −7.8** (#1, #6): gain 313 and 5044, F 2.8 and 0.17. These points also showed a negative overscan median and elevated overscan noise (840–870 ADU).

**Sensitivity.**
- **Most sensitive:** the Vdd/Vdrain relation. Moving Vdd from −14.5 to about −17.5 (with a matching Vdrain shift) raised gain from about 1.5e4 to about 2.5e4.
- **Possibly worse:** a Vdrain–Vdd gap of 4.5 V (#16, F 0.035).
- **Unresolved within noise:** Vr between −5.0 and −5.7, delay 27–30, and Vdd beyond −18 (#19, #24 ≈ 0.035).
- Vr = −6.4 (#22) gave 0.0385, which is a single point and only marginally worse.

**Suggestions for the next campaign.**
- Start at (−17.5, −20.2, −5.7, 28).
- Bounds: Vdd −19.5 to −16, Vdrain −22.5 to −19, Vr −6.5 to −5.0, delay 24–30. Note that Vr −5.0 and delay 30 are at the hard limits.
- Use at least 3 repeats per candidate. Single-shot differences below about 0.01 are not meaningful.
- Keep periodic reference re-measurements in place to catch LED dropouts.
- Test delay independently at fixed voltages. In this campaign it was confounded with the Vdd moves.
- Scan the Vdrain–Vdd gap (2, 3 and 4 V) at fixed Vdd ≈ −17.5.
- Investigate overscan noise, which still dominates F.

## 2026-10-01 10:19 | module skipper | 30 measurements (30 new) | best F = 1.1335 at Vdd=-16.9, Vdrain=-19.6, Vr=-7.0, delay_H_overlap=22.0

**Setup state changed sharply this campaign.** noise_overscan was 3.1–4.5e4 ADU, about 50× the ~700 ADU of earlier campaigns. charge_overscan sat near −4.8e5 ADU in all plausible-region points, versus small values before. Gain was similar to before (1.5–3.2e4), so F was about 1.1–3 instead of 0.02–0.04. F values from this campaign are not comparable with earlier entries. The likely cause is a hardware, offset or cabling change rather than a parameter effect, but this is unconfirmed.

**Best region.** The best points were around Vdd −16.9, Vdrain −19.6, Vr −6.8 to −7.0, delay 16–22.

| Setting (Vdd, Vdrain, Vr, delay) | Measurements | F | Mean F |
|---|---|---|---|
| (−16.9, −19.6, −7.0, 22) | #13, #16, #29 | 1.31, 1.13, 1.93 | ≈1.46 |
| (−16.9, −19.6, −6.8, 20) | #26, #28, #30 | 1.23, 1.34, 1.42 | ≈1.33 |

- Scatter at a fixed setting is about ±0.3 in F, driven by gain varying from 1.8e4 to 3.2e4.
- Last campaign's best point (−17.5, −20.2, −5.7, 28) gave 2.47 (#9).

**Broken or useless images.**
- **Shallow corner (−10.3, −12.5, −5.2):** gain −39, F 797. This failure is reproducible across campaigns.
- **Shallow Vdd with very negative Vdrain and Vr −7.5 to −7.8** (#1, #6): gain 4.6e3 and 1.8e3, F 7 and 19. These points also had an overscan median of only about −5e3 to −9e3.
- **Vdrain less negative than Vdd** (#2, #4, #5): these gave *positive* gain this time (1.2–2.3e4, F 1.9–3.1). This contradicts the earlier entries, so treat that rule as state-dependent.

**Sensitivity.**
- **Most sensitive:** the overall noise level (setup state), then Vr. Vr −7.3 and −7.4 gave F 2.4 and 3.1, with gain dropping to about 1.0–1.5e4. The Vdd/Vdrain region also mattered.
- **Little effect, single points only:** Vdd −16.4 to −17.3 and Vdrain −19.1 to −20.1 differed by ≤0.3. Delay 16–22 showed no resolvable effect, and delay 27 gave 2.17.

**Suggestions for the next campaign.**
- Before optimizing, measure a reference point and check noise_overscan and charge_overscan. If they are still around 3.5e4 and −4.8e5, investigate the readout chain or offset first, because that dominates F.
- Start at (−16.9, −19.6, −6.8, 20).
- Bounds: Vdd −18 to −16, Vdrain −21 to −18.5, Vr −7.2 to −5.5, delay 15–25.
- Test Vr from −5.7 to −6.8 at fixed voltages with at least 3 repeats each. The earlier campaign favoured −5.0 to −5.7, this one favoured −6.8 to −7.0, and the two have not been compared under the same conditions.
- Re-check whether the Vdrain > Vdd failure returns.
