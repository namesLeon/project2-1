#!/usr/bin/env python3
import argparse, math, random, time, os, sys

def clamp01(v): return max(0.0, min(1.0, v))

def pattern_circle(t, speed=0.2, radius=0.35, cx=0.5, cy=0.5):
    # normalized circular motion
    ang = 2.0 * math.pi * speed * t
    return clamp01(cx + radius * math.cos(ang)), clamp01(cy + radius * math.sin(ang))

def pattern_horizontal_scan(t, period=3.0, y=0.5):
    # 0→1→0 triangle wave
    phase = (t % period) / period
    x = phase if phase < 0.5 else (1.0 - (phase - 0.5) * 2.0)
    return clamp01(x), clamp01(y)

def pattern_randomwalk(state, step=0.05):
    x, y = state
    x = clamp01(x + random.uniform(-step, step))
    y = clamp01(y + random.uniform(-step, step))
    return x, y

def main():
    ap = argparse.ArgumentParser(description="Write gaze positions to gaze_out.txt for testing.")
    ap.add_argument("--file", default="gaze_out.txt", help="Output file path")
    ap.add_argument("--mode", choices=["circle","scan","random"], default="circle")
    ap.add_argument("--hz", type=float, default=30.0, help="Samples per second")
    ap.add_argument("--duration", type=float, default=0, help="Seconds to run (0 = infinite)")
    args = ap.parse_args()

    # Ensure parent dir exists
    os.makedirs(os.path.dirname(os.path.abspath(args.file)), exist_ok=True)

    print(f"[GEN] Writing {args.mode} gaze to: {os.path.abspath(args.file)} @ {args.hz:.1f} Hz")
    print("     Press Ctrl+C to stop.")

    t0 = time.perf_counter()
    dt = 1.0 / max(1e-6, args.hz)

    # Start from middle
    state = (0.5, 0.5)

    # (Optional) clear file at start so you see fresh data
    open(args.file, "w", encoding="utf-8").close()

    try:
        while True:
            t = time.perf_counter() - t0

            if args.mode == "circle":
                x, y = pattern_circle(t, speed=0.1, radius=0.35)
            elif args.mode == "scan":
                x, y = pattern_horizontal_scan(t, period=3.0, y=0.5)
            else:
                x, y = pattern_randomwalk(state)
                state = (x, y)

            # Append new line in your expected format
            with open(args.file, "a", encoding="utf-8") as f:
                f.write(f"x:{x:.6f} y:{y:.6f}\n")
                f.flush()  # make it visible immediately

            # Also print to console so you can watch it
            print(f"[GEN] x:{x:.3f} y:{y:.3f}", end="\r", flush=True)

            if args.duration and t >= args.duration:
                break
            time.sleep(dt)
    except KeyboardInterrupt:
        pass
    finally:
        print("\n[GEN] Stopped.")

if __name__ == "__main__":
    main()
