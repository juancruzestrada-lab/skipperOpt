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

## 2026-10-01 12:23 | module skipper | 30 measurements (30 new) | best F = 0.20852 at Vdd=-17.5, Vdrain=-20.2, Vr=-5.0, delay_H_overlap=30.0

## 2026-10-01 | module skipper | 30 measurements (30 new) | best F = 0.2085 at Vdd=-17.5, Vdrain=-20.2, Vr=-5.0, delay_H_overlap=30.0

**Setup state.** noise_overscan was back to normal (≈630–920 ADU). The LED signal was weak, though: the best gain was only 3.3e3, against 2–3e4 in earlier campaigns. From about #13 onward the signal was essentially lost.

**Best region.** Only the first 12 points look valid.
- **Best point:** #12 (−17.5, −20.2, −5.0, 30) gave F = 0.209 with gain 3308.
- **Runners-up:** #9 (−17.5, −20.2, −5.7, 28) gave 0.279, and #1 (−12.0, −20.7, −7.8, 17) gave 0.319.
- **Not reproducible:** the best point was re-measured 7 times (#14, 16, 18, 24, 27, 29, 30). Gain was 35–95 or negative (−460 to −600), and F ranged from 1.18 to 19. A repeat of #1 (#21) gave gain 93. This is a signal-dropout episode like the one in campaign 1, not a parameter effect.

**Broken or useless images.**
- **Dropout signature (#13–30):** gain ≤ ~160 or negative. The active median sat at or below the overscan median.
- **Misleading F values:** F uses |gain|, so negative-gain points produce plausible-looking F ≈ 1.2–2.4. Never rank points by F without checking that gain > 0.
- **Offset jump:** charge_overscan moved from about −1500 to +250…+730 ADU (#19, #25–30).
- **Active-region spikes:** noise_active jumped to 5.3e4 (#18) and 1.1e4 (#30), suggesting artifacts in the active region.
- **Shallow corner (−10.3, −12.5, −5.2):** gain −48, F 17.7. This failure has now reproduced in all four campaigns.
- **Vdrain less negative than Vdd:** #2 and #5 gave negative gain again. #4 gave gain 999 (positive but low).

**Sensitivity.** None could be resolved this campaign because of the dropout. The prior that Vdd ≈ −17.5 with Vdrain 2.5–3 V more negative is best is consistent with #9 and #12. Vr and delay remain untested.

**Suggestions for the next campaign.**
- **Check the signal before optimizing:** confirm the LED and signal chain (LED drive, exposure, cabling) and measure the reference point (−17.5, −20.2, −5.0 to −5.7, 28–30). Proceed only if gain > ~1e4.
- **Monitor for dropouts:** re-measure the reference point every ~5 points. Discard any point with gain < 1000 or negative, and flag charge_overscan jumps.
- **Bounds:** keep Vdd −19 to −16, Vdrain −22 to −19, Vr −7 to −5, delay 20–30.
- **Still-open tests:** the Vr comparison (−5.0 vs −6.8) and the Vdrain–Vdd gap scan.

## 2026-10-02 15:15 | module skipper | 30 measurements (30 new) | best F = 0.0072334 at Vdd=-17.5, Vdrain=-20.2, Vr=-5.0, delay_H_overlap=30.0

**Best region and reproducibility.** The best setting was (Vdd −17.5, Vdrain −20.2, Vr −5.0, delay 30).
- #10 and #11 were measured back-to-back there and gave F = 0.00723 and 0.00735, with gain ≈ 1.22e5. These are the best values in any campaign, with gain about 4× higher than before.
- Delay 27 (#12) gave 0.0080, which is not resolvably worse.
- Vr −5.7 / delay 28 (#9) gave 0.0149 (gain 4.8e4), but it was measured before #10, so drift may explain the difference.
- Overscan noise stayed normal throughout (630–940 ADU), so F tracks gain only.

**Signal decay and dropout (#13–30).** Gain fell steadily, roughly halving each measurement: 1.0e5 → 4.1e4 → 1.4e4 → 7e3 → 4e3 → … → about 0 by #21.
- Repeats of the reference point fell in the same way, so this is time drift, not a parameter effect.
- #22–30 had gain from −164 to +267, so F ranged from 2.5 to 55.
- charge_overscan went from about +300 at peak signal to about −1300 during the dropout.
- Dropouts started around measurement 11–13 in campaigns 1 and 4 as well, which suggests a recurring time or exposure-history effect (LED, or charge build-up after high-signal exposures). This is unconfirmed.
- The #13–15 tests of Vdd and Vdrain (F 0.019, 0.051, 0.10) are therefore confounded and uninformative.

**Broken images.**
- The shallow corner (−10.3, −12.5, −5.2) gave gain −39. It has now failed in all five campaigns.
- With Vdrain less negative than Vdd, #2 and #5 gave negative gain and #4 gave gain 1006.
- #3 (−15.2, −17.4, −5.6, 22) gave gain 150.
- The opening points #1–8 are always measured in the same order, so time and parameter effects cannot be separated for them.

**Sensitivity.** Gain dominates F; overscan noise is effectively constant. Vr and delay are unresolved, with a weak hint that Vr −5.0 / delay 30 is better than Vr −5.7 / delay 28.

**Suggestions for the next campaign.**
- Skip the standard opening points #1–8, which are known to be bad.
- Start directly at (−17.5, −20.2, −5.0, 30) and verify gain > 5e4.
- Front-load the key comparisons in the first ~10 measurements, alternating with the reference point:
  - Vr −5.0 vs −5.7 vs −6.5
  - delay 27 vs 30
  - the Vdrain–Vdd gap at 2, 2.7 and 3.5 V
- Discard any point with gain < 1000.
- When the reference gain starts to decay, stop optimizing and investigate the LED or exposure chain and the CCD state (for example erase/purge between images).
- Bounds: Vdd −19 to −16, Vdrain −22 to −19, Vr −7 to −5, delay 24–30.

## 2026-10-02 16:53 | module skipper | operator note

This is the first lookbook entry that I write as an operator. I think the optimization that we did yesterday 10/1/2026 were using as illumination a lot of light leaks on the system. Now I am using as illumination the LED, i closed most of the light leaks. I think that is why the "gain" which is really the signal level minus overscan, is much lower than before.

## 2026-10-02 17:36 | module skipper | amp 3 (HDU 4) | gp | 30 measurements (30 new) | best F = 0.76876 at Vdd=-23.0, Vdrain=-23.0, Vr=-6.7, delay_H_overlap=30.0

**Run facts** (recorded by the code)
- Optimizer: gp; config: config_compare_gp.json; images optimize_394.fz to optimize_423.fz; 17:28-17:36.
- Best F this run: 0.7688 at (Vdd=-23.0, Vdrain=-23.0, Vr=-6.7, delay_H_overlap=30.0), image optimize_402.fz. Next: 0.9197 at (Vdd=-23.0, Vdrain=-20.6, Vr=-5.0, delay_H_overlap=10.0); 0.9225 at (Vdd=-23.0, Vdrain=-21.8, Vr=-5.7, delay_H_overlap=30.0).
- Signal (gain, ADU): median -16, max 850; 30 of 30 images below 1000 (no usable signal).
- Overscan noise (ADU): median 733, range 619-945.

## 2026-10-02 17:46 | module skipper | amp 3 (HDU 4) | claude | 30 measurements (30 new) | best F = 0.42845 at Vdd=-23.0, Vdrain=-10.5, Vr=-7.4, delay_H_overlap=10.0

**Run facts** (recorded by the code)
- Optimizer: claude; config: config_compare_claude.json; images optimize_424.fz to optimize_453.fz; 17:36-17:46.
- Best F this run: 0.4284 at (Vdd=-23.0, Vdrain=-10.5, Vr=-7.4, delay_H_overlap=10.0), image optimize_451.fz. Next: 0.4469 at (Vdd=-23.0, Vdrain=-10.5, Vr=-7.5, delay_H_overlap=10.0); 0.4477 at (Vdd=-23.0, Vdrain=-10.5, Vr=-7.6, delay_H_overlap=10.0).
- Signal (gain, ADU): median 1177, max 1590; 12 of 30 images below 1000 (no usable signal).
- Overscan noise (ADU): median 693, range 614-943.

**Best region.** The best results came from Vdd = -23.0, Vdrain = -10.5, Vr = -7.4 and delay_H_overlap = 10.

- Two runs at this point gave F = 0.428 and 0.457, with gain ~1460–1590 ADU and noise_overscan ~670–680 ADU.
- Nearby points form a plateau of F ≈ 0.43–0.53: Vr from -7.3 to -7.7 at Vdrain -10.5, and Vdrain from -10 to -15 at Vr ≈ -7.6.
- Repeat scatter is about ±0.03–0.05. Differences inside that plateau are therefore not meaningful.

**Broken or useless images.**
- **#8** (Vdd -10.3, Vdrain -12.5, Vr -5.2): gain was only 14 ADU, giving F = 61.
- **Negative gain** (#2, #3, #5, #7): charge_active was below charge_overscan, which is not a valid LED response. F uses |gain|, so these look deceptively moderate (#7 scored F = 1.58). Treat any gain < 0 as a failure.
- **#1 and #6** (Vdd -12 to -13.6, Vdrain -20.7 to -22.3): gain ~185 ADU and the highest overscan noise of the campaign (820–940 ADU), giving F ≈ 4–5.

**Sensitivity.**
- **F is driven mainly by gain.** noise_overscan stayed roughly between 610 and 940 ADU across all runs.
- **Vdd had the largest effect.** Every good point was at Vdd ≤ -21.7, and the low-F points mostly sat at the -23 bound.
- **delay_H_overlap mattered next.** At the same settings, delay 10 gave F = 0.50 and delay 16 gave 0.72; 10 is the lower bound.
- **Vrdrain was flat from -10 to -15** but degraded at -18 (F = 0.89).
- **Vr is best around -7.4 to -7.6.** Both ends were worse: -7.0 gave F = 0.69 and -8.0 gave 0.63.

**Suggestions for the next campaign.**
- Start at Vdd -23, Vdrain -10.5, Vr -7.4, delay 10.
- Both Vdd and delay are pinned at their bounds. If hardware limits permit, extend Vdd below -23 and delay below 10 and test there first.
- Narrow the search to Vdrain between -10 and -15 and Vr between -7.8 and -7.2.
- Add a penalty or rejection rule for gain < 0 or very small gain.
- Budget 2–3 repeats per candidate, since real improvements will likely be at the ±0.03 level.
