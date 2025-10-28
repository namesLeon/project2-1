from typing import Optional, Tuple
import cv2
import numpy as np


def _suppress_highlights(gray: np.ndarray) -> np.ndarray:
    """removes bright spots from grayscaled image"""
    se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, se)
    _, mask = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=1)
    return cv2.inpaint(gray, mask, 3, cv2.INPAINT_TELEA)


def _subpixel_refine(
    gray: np.ndarray, pt: Tuple[int, int], win: int = 5
) -> Tuple[float, float]:
    """takes integer point and returns subpixel refined point"""
    x, y = pt
    h, w = gray.shape[:2]  # get height and width
    x = max(0, min(w - 1, x))  # clamp x to image bounds
    y = max(0, min(h - 1, y))  # clamp y to image bounds
    pts = np.array(
        [[np.float32(x), np.float32(y)]], dtype=np.float32
    )  # 1x2 array of the point
    term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.01)

    # run cornerSubPix to refine the point, if succeed return (x,y) as a float otherwise return original point
    try:
        refined = cv2.cornerSubPix(
            gray.astype(np.uint8), pts, (win, win), (-1, -1), term
        )
        return float(refined[0, 0, 0]), float(refined[0, 0, 1])
    except Exception:
        return float(x), float(y)


def pupil_center_precise(eye_gray: np.ndarray) -> Optional[Tuple[int, int]]:
    """
    single-eye pupil center finder.
    returns (cx, cy) in the eye ROI coordinate system, or None if not found.
    """
    h, w = eye_gray.shape[:2]  # get height and width of ROI
    if h < 10 or w < 10:  # rejects small ROIs
        return None

    # skip top 18% of eye (eyelid leads to errors) - we can play with this to try get better results
    top_crop = int(0.18 * h)
    g = eye_gray[top_crop:, :]  # cropped grayscale image
    if g.size == 0:
        return None

    clahe = cv2.createCLAHE(
        clipLimit=2.0, tileGridSize=(8, 8)
    )  # dont really understand it boosts contrast
    g = clahe.apply(g)
    g = cv2.bilateralFilter(
        g, d=5, sigmaColor=50, sigmaSpace=7
    )  # reduces noise while preserving edges
    g = _suppress_highlights(g)  # removes bright spots from the image

    # lighting adaptation using Canny edges
    v = np.median(g)
    lo = int(max(0, 0.66 * v))
    hi = int(min(255, 1.33 * v))
    edges = cv2.Canny(g, lo, hi, apertureSize=3, L2gradient=True)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # define allowed contour size range
    H, W = g.shape[:2]
    area_min = 0.005 * (W * H)
    area_max = 0.25 * (W * H)

    best_pt = None  # initialize best candidate
    best_score = -1.0
    mean_all = float(np.mean(g))  # compute mean intensity of g

    for c in contours:
        if len(c) < 20:  # skip small contours
            continue
        # compute bounding box
        (x, y, ww, hh) = cv2.boundingRect(c)
        area = float(ww * hh)  # area of bounding box
        if area < area_min or area > area_max:
            continue
        if ww < 4 or hh < 4:
            continue
        try:
            ellipse = cv2.fitEllipse(c)
        except cv2.error:
            continue
        (cx, cy), (MA, ma), _ = ellipse
        if min(MA, ma) < 3:
            continue
        mask = np.zeros_like(g)
        cv2.ellipse(mask, ellipse, 255, -1)
        dark_mean = float(cv2.mean(g, mask=mask)[0])
        circularity = min(MA, ma) / max(MA, ma)
        center_y = cy
        top_penalty = 1.0 - min(1.0, center_y / (0.35 * H))
        # higher score if darker than surroundings, more circular, lower in the eye
        score = (mean_all - dark_mean) * (0.7 + 0.3 * circularity) - 1.6 * top_penalty
        # keep best score
        if score > best_score:
            best_score = score
            best_pt = (int(round(cx)), int(round(cy)))

    # only runs when no good pupil is found
    if best_pt is None:
        p = np.percentile(g, 12)  # 12th percentile intensity
        _, th = cv2.threshold(
            g, int(p), 255, cv2.THRESH_BINARY_INV
        )  # threshold to get dark regions
        th = cv2.morphologyEx(
            th, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1
        )
        th = cv2.morphologyEx(
            th, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=1
        )
        contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            # define acceptable area range for contours
            area_min2 = 0.006 * (W * H)
            area_max2 = 0.22 * (W * H)
            best_score = -1.0
            # skip blobs that are too small or too large to be a pupil
            for c in contours:
                area = cv2.contourArea(c)
                if area < area_min2 or area > area_max2:
                    continue
                # rejects blobs that touch border
                x, y, ww, hh = cv2.boundingRect(c)
                if x <= 0 or y <= 0 or (x + ww) >= (W - 1) or (y + hh) >= (H - 1):
                    continue
                if y < int(0.10 * H):  # rejects blobs that lie in upper 10% of eye
                    continue
                # compute circularity - closer to one means more pupil-like
                perim = cv2.arcLength(c, True)
                if perim <= 1e-6:
                    continue
                circularity = 4.0 * np.pi * area / (perim * perim)
                mask = np.zeros_like(th)
                cv2.drawContours(mask, [c], -1, 255, -1)
                dark_mean = float(cv2.mean(g, mask=mask)[0])
                # compute penalty for blobs that are high in the eye
                cy = y + hh / 2.0
                top_penalty = 1.0 - min(1.0, cy / (0.35 * H))
                # final score = how dark, how circular, how low in eye. higher = better
                score = (float(np.mean(g)) - dark_mean) * (
                    0.6 + 0.4 * circularity
                ) - 1.6 * top_penalty
                if score > best_score:
                    # if blob wins then compute its center and store as a candidate pupil centre
                    M = cv2.moments(c)
                    if M["m00"] > 1e-6:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        best_pt = (cx, cy)

    # only runs when a good pupil is found
    if best_pt is None:
        return None

    rx, ry = _subpixel_refine(g, best_pt, win=5)  # refine chosen center
    return (
        int(round(rx)),
        int(round(ry + top_crop)),
    )  # returns integer center with top crop offset


def pupil_confidence(g: np.ndarray, cx: int, cy: int) -> float:
    """gives a confidence score based on how much darker the pupil area is compared to the outside"""
    h, w = g.shape[:2]
    r = max(3, int(0.06 * min(h, w)))  # radius for pupil area
    yy, xx = np.ogrid[:h, :w]
    mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
    if not np.any(mask):
        return 0.0
    inside = float(np.mean(g[mask]))  # mean intensity inside the pupil area
    border = (
        float(np.mean(g[~mask])) if np.any(~mask) else inside
    )  # mean intensity outside the pupil area
    return max(0.0, (border - inside))  # we force scores to be non-negative
