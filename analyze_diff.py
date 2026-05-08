# -*- coding: utf-8 -*-
"""
Deep pixel-level analysis of Original.jpg vs Quality Enhanced.jpeg
to reverse-engineer the exact transformation applied.
"""

import numpy as np
from PIL import Image
import json

# Load both images
orig = Image.open(r"c:\Users\User\OneDrive\桌面\Image Upscaler\Original.jpg")
enhanced = Image.open(r"c:\Users\User\OneDrive\桌面\Image Upscaler\Quality Enhanced.jpeg")

print(f"Original   - size: {orig.size}, mode: {orig.mode}")
print(f"Enhanced   - size: {enhanced.size}, mode: {enhanced.mode}")

# Convert to same mode for comparison
orig_rgb = orig.convert("RGB")
enhanced_rgb = enhanced.convert("RGB")

# Check if sizes differ
if orig_rgb.size != enhanced_rgb.size:
    print(f"\n!!! SIZES DIFFER - Original: {orig_rgb.size}, Enhanced: {enhanced_rgb.size}")
    print(f"Scale factor X: {enhanced_rgb.size[0] / orig_rgb.size[0]:.6f}")
    print(f"Scale factor Y: {enhanced_rgb.size[1] / orig_rgb.size[1]:.6f}")
    # Resize enhanced to original size for pixel comparison
    # But first, let's also check if they'd match at enhanced size
    print("\nWe'll analyze at both scales.")

# Get numpy arrays
o = np.array(orig_rgb).astype(np.float32)
e = np.array(enhanced_rgb).astype(np.float32)

print(f"\nOriginal array shape: {o.shape}")
print(f"Enhanced array shape: {e.shape}")

# Convert to grayscale for analysis
o_gray = np.array(orig.convert("L")).astype(np.float32)
e_gray = np.array(enhanced.convert("L")).astype(np.float32)

print("\n" + "="*60)
print("BASIC STATISTICS")
print("="*60)

print(f"\nOriginal  - mean: {o_gray.mean():.4f}, std: {o_gray.std():.4f}, min: {o_gray.min()}, max: {o_gray.max()}")
print(f"Enhanced  - mean: {e_gray.mean():.4f}, std: {e_gray.std():.4f}, min: {e_gray.min()}, max: {e_gray.max()}")

# Check if images are same size
if o.shape == e.shape:
    print("\n" + "="*60)
    print("PIXEL-BY-PIXEL DIFFERENCE ANALYSIS (same size)")
    print("="*60)
    
    diff = e_gray - o_gray
    abs_diff = np.abs(diff)
    
    print(f"\nDifference - mean: {diff.mean():.4f}, std: {diff.std():.4f}")
    print(f"Abs diff   - mean: {abs_diff.mean():.4f}, max: {abs_diff.max():.4f}")
    
    # How many pixels changed?
    changed = abs_diff > 0
    total_pixels = o_gray.size
    changed_count = changed.sum()
    print(f"\nTotal pixels: {total_pixels}")
    print(f"Changed pixels: {changed_count} ({100*changed_count/total_pixels:.2f}%)")
    print(f"Unchanged pixels: {total_pixels - changed_count} ({100*(total_pixels-changed_count)/total_pixels:.2f}%)")
    
    # Threshold analysis
    for thresh in [1, 2, 3, 5, 10, 20, 30, 50]:
        count = (abs_diff > thresh).sum()
        print(f"  Pixels differing by > {thresh}: {count} ({100*count/total_pixels:.2f}%)")
    
    # Brightened vs Darkened
    brightened = (diff > 1).sum()
    darkened = (diff < -1).sum()
    print(f"\nBrightened pixels (diff > 1): {brightened} ({100*brightened/total_pixels:.2f}%)")
    print(f"Darkened pixels (diff < -1): {darkened} ({100*darkened/total_pixels:.2f}%)")
    
    # Analyze by original intensity zone
    print("\n" + "="*60)
    print("ANALYSIS BY ORIGINAL INTENSITY ZONE")
    print("="*60)
    
    zones = [
        (0, 10, "Pure Black (0-10)"),
        (10, 30, "Near Black (10-30)"),
        (30, 60, "Dark (30-60)"),
        (60, 100, "Dark-Mid (60-100)"),
        (100, 140, "Mid (100-140)"),
        (140, 180, "Light-Mid (140-180)"),
        (180, 220, "Light (180-220)"),
        (220, 240, "Near White (220-240)"),
        (240, 256, "Pure White (240-255)"),
    ]
    
    for lo, hi, label in zones:
        mask = (o_gray >= lo) & (o_gray < hi)
        count = mask.sum()
        if count == 0:
            continue
        zone_diff = diff[mask]
        zone_e = e_gray[mask]
        zone_o = o_gray[mask]
        
        # Try to find a linear mapping: e = a*o + b
        # Using least squares
        if count > 10:
            A = np.vstack([zone_o.flatten(), np.ones(count)]).T
            result = np.linalg.lstsq(A, zone_e.flatten(), rcond=None)
            a, b = result[0]
            residual = np.sqrt(np.mean((zone_e.flatten() - a * zone_o.flatten() - b)**2))
        else:
            a, b, residual = 0, 0, 0
        
        print(f"\n{label}:")
        print(f"  Pixel count: {count} ({100*count/total_pixels:.2f}%)")
        print(f"  Original mean: {zone_o.mean():.2f}, Enhanced mean: {zone_e.mean():.2f}")
        print(f"  Mean diff: {zone_diff.mean():.2f}, Std diff: {zone_diff.std():.2f}")
        print(f"  Linear fit: enhanced = {a:.4f} * original + {b:.4f} (RMSE: {residual:.4f})")
    
    # Global linear fit
    print("\n" + "="*60)
    print("GLOBAL MAPPING ANALYSIS")
    print("="*60)
    
    flat_o = o_gray.flatten()
    flat_e = e_gray.flatten()
    
    # Linear fit
    A = np.vstack([flat_o, np.ones(len(flat_o))]).T
    result = np.linalg.lstsq(A, flat_e, rcond=None)
    a, b = result[0]
    residual = np.sqrt(np.mean((flat_e - a * flat_o - b)**2))
    print(f"\nGlobal linear fit: e = {a:.6f} * o + {b:.6f} (RMSE: {residual:.4f})")
    
    # Polynomial fit (degree 2, 3)
    for deg in [2, 3, 4]:
        coeffs = np.polyfit(flat_o, flat_e, deg)
        pred = np.polyval(coeffs, flat_o)
        rmse = np.sqrt(np.mean((flat_e - pred)**2))
        print(f"Poly degree {deg}: coeffs={[f'{c:.8f}' for c in coeffs]} (RMSE: {rmse:.4f})")
    
    # Build a lookup table: for each original value, what's the median enhanced value?
    print("\n" + "="*60)
    print("LOOKUP TABLE (Original -> Enhanced median)")
    print("="*60)
    
    lut = {}
    for v in range(256):
        mask = o_gray == v
        if mask.sum() > 0:
            lut[v] = {
                'median': float(np.median(e_gray[mask])),
                'mean': float(np.mean(e_gray[mask])),
                'std': float(np.std(e_gray[mask])),
                'count': int(mask.sum()),
                'min': float(np.min(e_gray[mask])),
                'max': float(np.max(e_gray[mask])),
            }
    
    print(f"\n{'Orig':>4} -> {'Med':>5} {'Mean':>7} {'Std':>6} {'Min':>4} {'Max':>4} {'Count':>8}")
    print("-" * 55)
    for v in sorted(lut.keys()):
        d = lut[v]
        print(f"{v:4d} -> {d['median']:5.1f} {d['mean']:7.2f} {d['std']:6.2f} {d['min']:4.0f} {d['max']:4.0f} {d['count']:8d}")
    
    # Check for spatial patterns - is the transformation spatially uniform?
    print("\n" + "="*60)
    print("SPATIAL UNIFORMITY CHECK")
    print("="*60)
    
    h, w = o_gray.shape
    quadrants = {
        "Top-Left": (slice(0, h//2), slice(0, w//2)),
        "Top-Right": (slice(0, h//2), slice(w//2, w)),
        "Bottom-Left": (slice(h//2, h), slice(0, w//2)),
        "Bottom-Right": (slice(h//2, h), slice(w//2, w)),
    }
    
    for name, (ys, xs) in quadrants.items():
        q_o = o_gray[ys, xs].flatten()
        q_e = e_gray[ys, xs].flatten()
        q_diff = q_e - q_o
        A = np.vstack([q_o, np.ones(len(q_o))]).T
        result = np.linalg.lstsq(A, q_e, rcond=None)
        qa, qb = result[0]
        qrmse = np.sqrt(np.mean((q_e - qa * q_o - qb)**2))
        print(f"{name}: linear fit e = {qa:.4f}*o + {qb:.4f} (RMSE: {qrmse:.4f}, mean_diff: {q_diff.mean():.2f})")
    
    # Check if it's a simple gamma correction
    print("\n" + "="*60)
    print("GAMMA / CURVE ANALYSIS")
    print("="*60)
    
    # For non-zero, non-255 pixels, try to find gamma
    mid_mask = (o_gray > 5) & (o_gray < 250) & (e_gray > 5) & (e_gray < 250)
    if mid_mask.sum() > 100:
        o_norm = o_gray[mid_mask] / 255.0
        e_norm = e_gray[mid_mask] / 255.0
        
        # log(e/255) = gamma * log(o/255)
        # gamma = log(e_norm) / log(o_norm)
        valid = (o_norm > 0.01) & (e_norm > 0.01)
        if valid.sum() > 100:
            gammas = np.log(e_norm[valid]) / np.log(o_norm[valid])
            gammas = gammas[(gammas > 0) & (gammas < 10)]  # filter outliers
            print(f"Estimated gamma (median): {np.median(gammas):.6f}")
            print(f"Estimated gamma (mean): {np.mean(gammas):.6f}")
            print(f"Gamma std: {np.std(gammas):.6f}")
            
            # Try applying this gamma and see residual
            test_gamma = np.median(gammas)
            gamma_pred = 255.0 * np.power(o_gray / 255.0, test_gamma)
            gamma_rmse = np.sqrt(np.mean((e_gray - gamma_pred)**2))
            print(f"RMSE with pure gamma={test_gamma:.4f}: {gamma_rmse:.4f}")
    
    # Check RGB channels independently
    print("\n" + "="*60)
    print("RGB CHANNEL ANALYSIS")
    print("="*60)
    
    for c, name in enumerate(["Red", "Green", "Blue"]):
        o_c = o[:,:,c].flatten()
        e_c = e[:,:,c].flatten()
        diff_c = e_c - o_c
        print(f"\n{name} channel:")
        print(f"  Original  - mean: {o_c.mean():.2f}, std: {o_c.std():.2f}")
        print(f"  Enhanced  - mean: {e_c.mean():.2f}, std: {e_c.std():.2f}")
        print(f"  Diff      - mean: {diff_c.mean():.4f}, std: {diff_c.std():.4f}")
        
        # Are all 3 channels the same in each image? (grayscale check)
    
    # Check if original is truly grayscale
    r, g, b = o[:,:,0], o[:,:,1], o[:,:,2]
    rg_diff = np.abs(r - g).max()
    rb_diff = np.abs(r - b).max()
    gb_diff = np.abs(g - b).max()
    print(f"\nOriginal grayscale check: max(R-G)={rg_diff:.0f}, max(R-B)={rb_diff:.0f}, max(G-B)={gb_diff:.0f}")
    
    r, g, b = e[:,:,0], e[:,:,1], e[:,:,2]
    rg_diff = np.abs(r - g).max()
    rb_diff = np.abs(r - b).max()
    gb_diff = np.abs(g - b).max()
    print(f"Enhanced grayscale check: max(R-G)={rg_diff:.0f}, max(R-B)={rb_diff:.0f}, max(G-B)={gb_diff:.0f}")

    # Check JPEG compression artifacts - histogram of differences
    print("\n" + "="*60)
    print("DIFFERENCE HISTOGRAM")
    print("="*60)
    
    hist_diff = diff.astype(np.int32).flatten()
    unique, counts = np.unique(hist_diff, return_counts=True)
    print(f"\nDifference value distribution (top 30 most common):")
    sorted_idx = np.argsort(-counts)[:30]
    for i in sorted_idx:
        print(f"  diff={unique[i]:+4d}: {counts[i]:>8d} pixels ({100*counts[i]/total_pixels:.2f}%)")

    # Try to find if it's levels/curves adjustment
    print("\n" + "="*60)
    print("CONTRAST / LEVELS ANALYSIS")
    print("="*60)
    
    # Check if a simple Levels adjustment (black point, white point, gamma) fits
    # Levels: output = ((input - black_in) / (white_in - black_in))^gamma * (white_out - black_out) + black_out
    # pyrefly: ignore [missing-import]
    from scipy.optimize import minimize
    
    def levels_model(params, o_flat, e_flat):
        black_in, white_in, gamma, black_out, white_out = params
        normalized = np.clip((o_flat - black_in) / max(white_in - black_in, 1), 0, 1)
        output = np.power(normalized, gamma) * (white_out - black_out) + black_out
        return np.sqrt(np.mean((e_flat - output)**2))
    
    try:
        # Subsample for speed
        n = min(500000, len(flat_o))
        idx = np.random.choice(len(flat_o), n, replace=False)
        sub_o = flat_o[idx]
        sub_e = flat_e[idx]
        
        result = minimize(levels_model, [0, 255, 1.0, 0, 255], args=(sub_o, sub_e),
                         method='Nelder-Mead', options={'maxiter': 10000})
        bp_in, wp_in, gamma, bp_out, wp_out = result.x
        print(f"\nBest-fit Levels adjustment:")
        print(f"  Black point in:  {bp_in:.2f}")
        print(f"  White point in:  {wp_in:.2f}")
        print(f"  Gamma:           {gamma:.4f}")
        print(f"  Black point out: {bp_out:.2f}")
        print(f"  White point out: {wp_out:.2f}")
        print(f"  RMSE:            {result.fun:.4f}")
    except Exception as ex:
        print(f"  Levels fitting failed: {ex}")

else:
    print("\n!!! Images are different sizes, analyzing at original scale...")
    print("Resizing Enhanced to match Original for comparison...")
    
    enhanced_resized = enhanced_rgb.resize(orig_rgb.size, Image.LANCZOS)
    e_resized_gray = np.array(enhanced_resized.convert("L")).astype(np.float32)
    
    diff = e_resized_gray - o_gray
    abs_diff = np.abs(diff)
    
    print(f"\nDifference after resize - mean: {diff.mean():.4f}, std: {diff.std():.4f}")
    print(f"Abs diff - mean: {abs_diff.mean():.4f}, max: {abs_diff.max():.4f}")

print("\n\nAnalysis complete!")
