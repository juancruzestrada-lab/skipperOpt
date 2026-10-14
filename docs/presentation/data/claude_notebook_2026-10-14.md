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

## 2026-10-02 19:46 | module skipper | amp 3 (HDU 4) | operator note | correction

Correction to the 17:36 (gp) and 17:46 (claude) entries of 2026-10-02: their 'below 1000 (no usable signal)' line used a threshold from the light-leak period. With LED-only illumination the real signal is about 1000-1600 ADU (shot-noise consistent, ~10 e-/pixel), so those images do have signal. The gp run's best point (F 0.77) has negative gain, i.e. an inverted signal.

## 2026-10-05 10:12 | module skipper | amp 3 (HDU 4) | claude | 30 measurements (30 new) | best F = 0.24715 at Vdd=-12.0, Vdrain=-20.7, Vr=-7.8, delay_H_overlap=17.0

**Run facts** (recorded by the code)
- Optimizer: claude; config: config_compare_claude.json; images optimize_454.fz to optimize_483.fz; 10:01-10:12.
- Best F this run: 0.2471 at (Vdd=-12.0, Vdrain=-20.7, Vr=-7.8, delay_H_overlap=17.0), image optimize_454.fz. Next: 0.3735 at (Vdd=-18.0, Vdrain=-10.5, Vr=-7.3, delay_H_overlap=10.0); 0.3869 at (Vdd=-18.5, Vdrain=-10.5, Vr=-7.3, delay_H_overlap=10.0).
- Signal (gain = active minus overscan median, ADU): median 1075, max 3357; 2 of 30 images with negative gain.
- Overscan noise (ADU): median 664, range 580-978.

**Best region (reproducible).** Vdd −18.0 to −19.5, Vdrain −10.5, Vr −7.3 to −7.4, delay_H_overlap 10 gave F 0.37–0.41 (#26, 27, 29, 30). Gain there was about 1550–1610 ADU and noise_overscan 580–650. The best point was #30 (Vdd −18.0, Vdrain −10.5, Vr −7.3, delay 10) with F = 0.374. It was not repeated. In this region the scatter looks small: #4 and #12 were near-duplicates and gave F 0.602 and 0.601. Within that scatter, F was still improving slightly as Vdd moved from −19.5 toward −18.

**Unreliable or broken points.**
- #1 had the lowest F of the campaign (0.247). An exact repeat (#11) gave 5.7, and its neighbours #9 and #10 gave about 7.7. Treat #1 as an outlier, possibly a first-image artefact.
- With Vdd between −10 and −13.6 (#6, 8–11), gain collapsed to 120–390 ADU and noise_overscan rose above 900 ADU, giving F of 2.4–7.8.
- #2 and #5 had negative gain (active median below overscan). Both had Vdrain −14 to −16 and Vr −6.0 to −6.3. These settings are confounded with each other, so the cause is unclear.

**Sensitivity.** F was driven mainly by gain. noise_overscan stayed fairly flat (about 580–720) in the usable region.
- **Vr:** most sensitive, with a narrow optimum. At delay 11, Vr −7.0, −7.6 and −7.9 gave 0.67, 0.49 and 0.78. At delay 10, Vr −7.2, −7.3 and −7.4 gave 0.45, 0.40 and 0.41.
- **delay_H_overlap:** lower was better. Delay 10, 11 and 14 gave 0.45, 0.49 and 0.77. The optimum sits at the lower bound.
- **Vdrain:** values from −10 to −11 performed alike, and −12 was worse (0.52). The optimum sits near the upper bound.
- **Vdd:** weak sensitivity between −17.5 and −21. Values above about −14 are catastrophic.

**Suggestions for next campaign.**
- Start at Vdd −18, Vdrain −10.5, Vr −7.3, delay 10. Repeat this point 2–3 times to measure scatter.
- Discard or re-measure the first image of the run, and confirm any surprisingly good point.
- Narrow the bounds to roughly Vdd [−23, −15], Vdrain [−13, −10], Vr [−8, −6.8], delay [10, 16].
- Extend the Vdd scan toward −17 and −16 at Vr −7.3.
- Re-optimise Vr between −7.2 and −7.6 at the new Vdd.
- If the hardware allows, test delay below 10 and Vdrain above −10.

## 2026-10-05 13:19 | module skipper | amp 3 (HDU 4) | claude | 30 measurements (30 new) | best F = 0.26941 at Vdd=-12.0, Vdrain=-20.7, Vr=-7.8, delay_H_overlap=17.0

**Run facts** (recorded by the code)
- Optimizer: claude; config: config_compare_claude.json; images optimize_484.fz to optimize_513.fz; 13:09-13:19.
- Best F this run: 0.2694 at (Vdd=-12.0, Vdrain=-20.7, Vr=-7.8, delay_H_overlap=17.0), image optimize_484.fz. Next: 0.4698 at (Vdd=-22.0, Vdrain=-13.0, Vr=-7.6, delay_H_overlap=10.0); 0.4702 at (Vdd=-21.7, Vdrain=-12.9, Vr=-7.6, delay_H_overlap=10.0).
- Signal (gain = active minus overscan median, ADU): median 1118, max 3470; 2 of 30 images with negative gain.
- Overscan noise (ADU): median 672, range 621-963.

**Best region.** The optimum sits near **Vdd ≈ −21.7 to −22.0, Vdrain ≈ −12.9 to −13.0, Vr ≈ −7.6, delay_H_overlap = 10**.

- Best measured points:
  - #26 (−22.0, −13.0, −7.6, 10): F = 0.470
  - #29 (−21.7, −12.9, −7.6, 10): F = 0.470
- Close neighbours (#18, #21–23, #25, #27) gave F ≈ 0.50–0.51.
- Gain was about 1250–1410 ADU and noise_overscan about 635–730 ADU.

**Reproducibility.**

- Near-identical settings scatter by roughly ±0.05 in F. For example, #26, #28 and #30 gave 0.47, 0.58 and 0.54.
- One exact repeat (#4 and #12) gave 0.59 and 0.69.
- Differences below about 0.1 should therefore not be trusted.

**Unreliable or broken settings.**

- **#1 is not reproducible.** It gave F = 0.269 with gain 3470 at (−12.0, −20.7, −7.8, 17). The exact repeat (#11) gave gain 17.5 and F = 51. Nearby points #9 and #10 gave gain ≈ 170 and F ≈ 5.5. Overscan noise in that region was also high (900–960 ADU). Treat #1 as a fluke and this region as unstable.
- **Negative gain** appeared at #2 (Vr −6.3, delay 27) and #5 (Vr −6.0, delay 20), both with Vdd around −18 to −20 and Vdrain −14 to −16.
- **Near-zero gain** (8 ADU, F = 106) appeared at #8: Vdd −10.3, Vdrain −12.5, Vr −5.2.
- **Long delays** (25–30) gave low gain (≈450–480) and F ≈ 1.4–1.9.

**Sensitivity.**

- F is driven mostly by gain. Gain collapses with the Vdd/Vdrain combination and with Vr less negative than about −6.5.
- noise_overscan was fairly flat (≈620–730 ADU) across the good region.
- Within the good region, F was mildly worse at:
  - Vr −7.9 to −8.0 (F 0.65–0.75)
  - Vdrain −14 (F 0.62)
  - delay 11–15 (F 0.52–0.69, versus mostly 0.47–0.57 at delay 10)
- Vdd between −21 and −22.4 mattered little.

**Next campaign.**

- Start at (−21.8, −13.0, −7.6, 10).
- Narrow the bounds to:
  - Vdd [−23, −20]
  - Vdrain [−14, −11]
  - Vr [−7.9, −7.2]
- Delay is pinned at the lower bound of 10. Test values below 10 if the hardware allows.
- Repeat the best point 3–5 times to quantify noise before chasing small improvements.

## 2026-10-06 09:37 | module skipper | amp 3 (HDU 4) | claude | 30 measurements (30 new) | best F = 0.46852 at Vdd=-12.0, Vdrain=-20.7, Vr=-7.8, delay_H_overlap=17.0

**Run facts** (recorded by the code)
- Optimizer: claude; config: config_compare_claude.json; images optimize_514.fz to optimize_543.fz; 09:26-09:37.
- Best F this run: 0.4685 at (Vdd=-12.0, Vdrain=-20.7, Vr=-7.8, delay_H_overlap=17.0), image optimize_514.fz. Next: 0.4719 at (Vdd=-20.5, Vdrain=-11.0, Vr=-7.4, delay_H_overlap=12.0); 0.4788 at (Vdd=-20.5, Vdrain=-11.0, Vr=-7.5, delay_H_overlap=12.0).
- Signal (gain = active minus overscan median, ADU): median 1095, max 2084; 2 of 30 images with negative gain.
- Overscan noise (ADU): median 679, range 612-996.

**Best region (reproducible).** The best stable optimum is around **Vdd = −20.5, Vdrain = −11.0, Vr = −7.4 to −7.5, delay_H_overlap = 12**.

| # | Vr | F | gain (ADU) |
|---|---|---|---|
| 30 | −7.4 | 0.472 | 1345 |
| 28 | −7.5 | 0.479 | 1342 |
| 29 | −7.3 | 0.501 | 1222 |

A broad plateau surrounds it, with F between 0.52 and 0.67. It spans Vdd −23 to −18, Vdrain −10.5 to −13.8, Vr −7.3 to −8.0 and delay 10–15 (e.g. #12, #20, #22, #26). Point-to-point scatter within the plateau is about ±0.05–0.1 in F, so differences inside it are mostly noise.

**Unreliable point.** #1 (Vdd −12, Vdrain −20.7, Vr −7.8, delay 17) gave the nominal best F = 0.469. Its exact repeat #14 gave F = 13.3 (gain only 67), so #1 should not be trusted.

**Broken or useless images:**
- **Negative gain** (LED signal below overscan): #2 and #5. Both had Vr −6.0 to −6.3, Vdrain −14 to −16 and delay 20–27, giving F of 2.5–3.0.
- **Very small gain** (130 ADU): #8 at Vr −5.2, giving F = 6.7.
- **Low |Vdd| with high |Vdrain|** (Vdd −11.5 to −13.6, Vdrain −20 to −22.3):
  - overscan noise was high, about 810–1000 ADU versus about 610–720 on the plateau;
  - gain was erratic, ranging from 67 to 2084 ADU (#6, #9, #10, #14);
  - this region is unstable and should be avoided.
- **Edge effects:** Vdrain −10.0 (#23) dropped gain to 857 (F 0.78), and Vdd −16.5 (#21) gave F 0.67.

**Sensitivity.**
- F is driven mainly by the gain, which depends strongly on the Vdd/Vdrain combination and on Vr. Less negative Vr (above about −6.5) collapsed the gain.
- Overscan noise varied only modestly on the plateau.
- F was least sensitive to Vr within −7.3 to −8.0 and to delay within 10–15.
- The effect of delay is confounded with the other parameters, because all of the larger delays were tested in poor regions.

**Suggestions for the next campaign:**
- Narrow the bounds to Vdd [−23, −18], Vdrain [−13, −10.5], Vr [−8, −7.0] and delay [10, 16].
- Start at (−20.5, −11.0, −7.4, 12).
- Spend early points on 2–3 repeats at the start point to quantify the noise floor.
- Scan delay alone (e.g. 10, 12, 15, 18, 22) at the best voltages to separate its effect.
- Probe Vr between −7.0 and −7.3 to see whether the gain keeps rising before it collapses.

## 2026-10-06 09:51 | module skipper | amp 3 (HDU 4) | claude | 30 measurements (30 new) | best F = 0.39315 at Vdd=-22.5, Vdrain=-10.5, Vr=-7.4, delay_H_overlap=10.0

**Run facts** (recorded by the code)
- Optimizer: claude; config: config_compare_claude.json; images optimize_544.fz to optimize_573.fz; 09:41-09:51.
- Best F this run: 0.3932 at (Vdd=-22.5, Vdrain=-10.5, Vr=-7.4, delay_H_overlap=10.0), image optimize_573.fz. Next: 0.4137 at (Vdd=-22.5, Vdrain=-10.5, Vr=-7.4, delay_H_overlap=10.0); 0.4147 at (Vdd=-22.5, Vdrain=-10.5, Vr=-7.5, delay_H_overlap=10.0).
- Signal (gain = active minus overscan median, ADU): median 1370, max 1618; 2 of 30 images with negative gain.
- Overscan noise (ADU): median 665, range 588-949.

**Best region.** The optimum is Vdd = −22.5, Vdrain = −10.5, Vr = −7.4 to −7.5, delay_H_overlap = 10.
- Three measurements at or next to this point gave F = 0.414, 0.393 (#27 and #30, both Vr −7.4) and 0.415 (#22, Vr −7.5).
- Gain was about 1600 ADU and noise_overscan about 630–670 ADU at these points.
- Nearby points (Vdd −22.2 to −23, Vdrain −10 to −12, Vr −7.2 to −7.6) all gave F = 0.44–0.50.
- Run-to-run scatter looks like ±0.03 or more. noise_overscan wanders between about 625 and 705 ADU with no clear dependence on any parameter, so differences below about 0.05 in F are not meaningful.

**Broken or useless settings.**
- **Low |Vdd| with low |Vdrain| and Vr ≈ −5** (#8: −10.3/−12.5/−5.2): gain was only 40 ADU, giving F = 21.
- **Negative gain** (#2: −18.5/−14.2/−6.3/27; #5: −20.1/−15.8/−6.0/20): in #5 charge_overscan was even positive.
  - F uses |gain|, so #2 still reported a deceptively moderate F = 1.76.
  - These points should be treated as invalid.
- **Very negative Vdrain (about −21 to −22) with low |Vdd|** (#1, #6): noise_overscan was about 890–950 ADU, compared with about 650 ADU elsewhere, and gain was low.

**Sensitivity.** Near the optimum, noise is roughly constant, so F is driven almost entirely by gain. Measured at or near Vdd −22, Vdrain −10:

| Parameter | Most sensitive? | Change | Result |
|---|---|---|---|
| Vr | Most | −7.4 → −7.0 / −6.6 | F 0.65 / 0.88 |
| Vr | Most | −7.4 → −8.0 | F 0.70 |
| delay_H_overlap | Strong | 10 → 15 | Gain fell from about 1500 to 808 ADU, F 0.73 |
| Vdrain | Weak | −10 to −12 | F within 0.41–0.47 |
| Vdd | Least | −20 to −23 | Nearly flat |

Changing Vdrain also strongly shifts the baseline: charge_overscan was about −3500 ADU at −10.0 and about −2400 ADU at −10.5.

**Suggestions for the next campaign.**
- Start at (−22.5, −10.5, −7.4, 10).
- Narrow the bounds to Vdd [−23, −20], Vdrain [−12, −10], Vr [−7.8, −7.0].
- delay_H_overlap was optimal at its lower bound of 10. If the hardware allows, test values below 10; this is the most promising unexplored direction.
- Add a penalty for gain ≤ 0 or very small gain.
- Spend some measurements on repeats at the best point to pin down the noise floor of F before fine-tuning.

## 2026-10-07 17:01 | module skipper | amp 3 (HDU 4) | claude | 30 measurements (30 new) | best F = 0.060675 at Vdd=-23.0, Vdrain=-22.0, Vr=-5.0, delay_H_overlap=19.0, hh=-2.2, hl=-6.2

**Run facts** (recorded by the code)
- Optimizer: claude; config: config_compare_claude.json; images optimize_574.fz to optimize_603.fz; 16:48-17:01.
- Best F this run: 0.06067 at (Vdd=-23.0, Vdrain=-22.0, Vr=-5.0, delay_H_overlap=19.0, hh=-2.2, hl=-6.2), image optimize_601.fz. Next: 0.06103 at (Vdd=-23.0, Vdrain=-22.0, Vr=-5.0, delay_H_overlap=19.0, hh=-2.0, hl=-6.2); 0.06441 at (Vdd=-23.0, Vdrain=-22.0, Vr=-5.0, delay_H_overlap=22.0, hh=-2.0, hl=-6.2).
- Signal (gain = active minus overscan median, ADU): median -57221, max 4942; 25 of 30 images with negative gain.
- Overscan noise (ADU): median 5024, range 665-16902.

**Best region by F (but see caveat).** The lowest F came from Vdd −23.0 (at the bound), Vdrain −22.0, Vr −5.0 (at the bound), hh −2.0 to −2.2, hl −6.2, delay_H_overlap 19–22:
- #28: F 0.0607
- #23: F 0.0610
- #22: F 0.0644

Reproducibility is moderate. Repeating #28 exactly (#30) gave F 0.079, so the scatter is about ±0.01–0.02. Most points in this region fall between 0.06 and 0.10.

**Caveat: these images look abnormal.** In this region:
- Gain is large and negative, about −6e4 to −9e4 ADU.
- Overscan median is about 1e5 ADU, far above the active median of about 1e4.
- Overscan noise is about 5000–6000 ADU, against about 700 ADU in normal-looking images.

F is low only because |gain| is huge. This is probably a baseline or overscan artifact, not low read noise. Check the images before trusting this region.

**Other broken or useless settings:**
- hh above about 3 or hl above about 0 (#1, #5, #6, #8) gave gain of only ±40–230 ADU and F of 3–20. There was essentially no LED signal.
- Inverted clocks (#3: hh −9.5, hl 5.6) gave 6074 ADU overscan noise and negative gain.
- #9 had 1.7e4 ADU noise and negative gain.

**Physically plausible images (positive gain, overscan noise about 700 ADU):**
- #4: Vdd −21.7, Vdrain −10.9, Vr −7.1, delay 12, hh 0.5, hl −4.4; F 0.654, gain +1072.
- #10: F 1.15.

**Sensitivities:**
- The horizontal clock levels mattered most. Changing hh by only 0.2 V (−1.8 vs −2.2) moved F from 0.095 to 0.061. Moving hl off −6.2 (to −6.4 or −6.8) also worsened F.
- Delay had some effect: 16 and 28 were worse than 19–22.
- Vdrain (−21 to −23) and Vr (−5.0 vs −5.5) changed F by less than the noise.

**Suggestions for the next campaign:**
1. Add a penalty or constraint requiring positive gain, and flag overscan median greater than active median. Otherwise the optimizer will keep exploiting the artifact.
2. Visually inspect a #28-type image and a #4-type image to identify which is a real readout.
3. If #28-type is an artifact, restart near #4 and explore:
   - hh −2 to 1 and hl −6 to −4.
   - Vdd −23 to −20.
   - The full Vdrain range, which is poorly sampled at the less-negative end.
4. Keep hh and hl in the normal ordered configuration (hh > hl, both negative).
5. Repeat the best point 2–3 times to estimate scatter.

## 2026-10-07 17:38 | module skipper | amp 3 (HDU 4) | claude | 66 measurements (36 new) | best F = 0.057177 at Vdd=-23.0, Vdrain=-22.0, Vr=-6.0, delay_H_overlap=19.0, hh=-2.1, hl=-6.2 | interrupted (KeyboardInterrupt)

**Run facts** (recorded by the code)
- Optimizer: claude; config: config_compare_claude.json; images optimize_604.fz to optimize_639.fz; 17:22-17:38; resumed from 30 earlier measurements.
- Best F this run: 0.05718 at (Vdd=-23.0, Vdrain=-22.0, Vr=-6.0, delay_H_overlap=19.0, hh=-2.1, hl=-6.2), image optimize_606.fz. Next: 0.06112 at (Vdd=-23.0, Vdrain=-21.0, Vr=-6.0, delay_H_overlap=19.0, hh=-2.1, hl=-6.2); 0.06418 at (Vdd=-23.0, Vdrain=-22.0, Vr=-6.0, delay_H_overlap=18.0, hh=-2.1, hl=-6.2).
- Signal (gain = active minus overscan median, ADU): median -13274, max 192300; 34 of 36 images with negative gain.
- Overscan noise (ADU): median 4018, range 868-18137.

## 2026-10-07 17:49 | module skipper | amp 3 (HDU 4) | claude | 8 measurements (8 new) | best F = 0.49335 at Vdd=-21.7, Vdrain=-10.9, Vr=-7.1, delay_H_overlap=12.0, hh=8.0, hl=-3.5 | interrupted (ZeroDivisionError)

**Run facts** (recorded by the code)
- Optimizer: claude; config: config_compare_claude.json; images optimize_640.fz to optimize_647.fz; 17:46-17:49.
- Best F this run: 0.4934 at (Vdd=-21.7, Vdrain=-10.9, Vr=-7.1, delay_H_overlap=12.0, hh=8.0, hl=-3.5), image optimize_643.fz. Next: 0.9909 at (Vdd=-13.6, Vdrain=-22.3, Vr=-7.5, delay_H_overlap=30.0, hh=8.0, hl=-3.5); 1.079 at (Vdd=-16.8, Vdrain=-19.0, Vr=-6.7, delay_H_overlap=25.0, hh=8.0, hl=-3.5).
- Signal (gain = active minus overscan median, ADU): median -260, max 1280; 5 of 8 images with negative gain.
- Overscan noise (ADU): median 894, range 631-5136.

## 2026-10-14 10:13 | module skipper | amp 3 (HDU 4) | claude | 8 measurements (8 new) | best F = 0.40409 at Vdd=-16.8, Vdrain=-19.0, Vr=-6.7, delay_H_overlap=25.0, hh=8.0, hl=-6.9 | interrupted (ZeroDivisionError)

**Run facts** (recorded by the code)
- Optimizer: claude; config: config_compare_claude.json; images optimize_648.fz to optimize_655.fz; 10:11-10:13.
- Best F this run: 0.4041 at (Vdd=-16.8, Vdrain=-19.0, Vr=-6.7, delay_H_overlap=25.0, hh=8.0, hl=-6.9), image optimize_654.fz. Next: 0.5084 at (Vdd=-21.7, Vdrain=-10.9, Vr=-7.1, delay_H_overlap=12.0, hh=8.0, hl=-4.4); 1.022 at (Vdd=-12.0, Vdrain=-20.7, Vr=-7.8, delay_H_overlap=17.0, hh=8.0, hl=0.6).
- Signal (gain = active minus overscan median, ADU): median -235, max 1209; 5 of 8 images with negative gain.
- Overscan noise (ADU): median 777, range 609-5784.

## 2026-10-14 10:32 | module skipper | amp 3 (HDU 4) | claude | 50 measurements (50 new) | best F = 0.28037 at Vdd=-19.5, Vdrain=-10.0, Vr=-7.6, delay_H_overlap=10.0, hh=4.6, hl=-9.1

**Run facts** (recorded by the code)
- Optimizer: claude; config: config_compare_claude.json; images optimize_656.fz to optimize_705.fz; 10:15-10:32.
- Best F this run: 0.2804 at (Vdd=-19.5, Vdrain=-10.0, Vr=-7.6, delay_H_overlap=10.0, hh=4.6, hl=-9.1), image optimize_705.fz. Next: 0.2959 at (Vdd=-19.0, Vdrain=-10.0, Vr=-7.6, delay_H_overlap=10.0, hh=4.6, hl=-9.1); 0.3024 at (Vdd=-21.5, Vdrain=-10.0, Vr=-7.6, delay_H_overlap=10.0, hh=4.6, hl=-9.1).
- Signal (gain = active minus overscan median, ADU): median 1674, max 4608; 4 of 50 images with negative gain.
- Overscan noise (ADU): median 688, range 612-5699.

**Best region.** The best point was #50: Vdd −19.5, Vdrain −10.0, Vr −7.6, delay_H_overlap 10, hh 4.6, hl −9.1, giving F = 0.280 (gain 2251, noise_overscan 631).

A broad plateau surrounds it, with F ≈ 0.30–0.35:
- Vdd −17.5 to −23
- Vdrain −10
- Vr −7.2 to −7.6
- delay 10–11
- hh 4.5–4.6
- hl −8.5 to −9.2

Repeats at identical settings scattered by about 0.03–0.05 (#13/#19: 0.389/0.337; #30/#35: 0.313/0.348). So #50 is not clearly better than #45–#47 (0.296–0.308).

**Broken or useless images.**
- **Negative gain:** #2, #3 and #5, at hh/hl far from the plateau. F uses |gain|, so these can still return modest F values. Check the sign of gain.
- **Near-zero gain, F of 6–72:** #1 (gain −12), #6, #8, and #27. #27 shows that Vdd −13 collapses gain to 153 even with otherwise good settings.
- **Huge overscan noise:** #3 had noise_overscan 5699 at hh −9.5, hl 5.6.
- **Saturated or offset baseline:** #7 had charge ~2.4e5 and noise 3232, yet F was only 0.70. Low F alone does not certify a sane image.

**Sensitivity.** In the good region noise_overscan is nearly constant (~630–750), so F is driven mainly by gain.
- **Most sensitive: hh.** The optimum is very narrow: 4.0 → 0.46–0.48, 4.7 → 0.45, 5.0 → 0.59–0.62.
- **Also sensitive:**
  - hl: −7.5 → 0.59, −8.0 → 0.41.
  - Vdd above about −16 collapses gain.
  - Vr at −6.6 → 0.60.
- **Vdrain is ambiguous.** Moving away from −10 hurt in #18 (0.58) and #28 (0.67), but #25 (Vdd −16.8, Vdrain −19) gave 0.368. This is under-sampled.
- **Least sensitive:** Vdd within −17.5 to −23, delay 10–16 (16 gave 0.438), and Vr −7.2 to −7.8.

**Suggestions for the next campaign.**
- Start at #50 and re-measure it 3–4 times to establish the noise floor.
- Narrow the bounds to hh [3.5, 5.5], hl [−10, −8], Vdd [−23, −16], Vr [−8, −7].
- delay (10) and Vdrain (−10) sit at their bounds. Test whether the hardware allows extending them.
- Map Vdrain properly at fixed Vdd to resolve the #25 vs #18/#28 conflict.
- The optimum (hh 4.6 > th = −1) violates the script's ordering constraints. Inspect the images for clock-induced artifacts before adopting these settings.
