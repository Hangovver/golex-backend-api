import math, bisect

# Platt scaling: p' = 1 / (1 + exp(A*p + B)), where p is logit or probability proxy
def fit_platt(probs, labels, lr=0.1, steps=400):
    # simple logistic regression on probability (not logit) as feature for MVP
    A, B = 0.0, 0.0
    for _ in range(steps):
        gA, gB = 0.0, 0.0
        for p, y in zip(probs, labels):
            z = A * p + B
            yhat = 1.0 / (1.0 + math.exp(-z))
            g = (yhat - y)
            gA += g * p
            gB += g
        A -= lr * gA / max(1, len(probs))
        B -= lr * gB / max(1, len(probs))
    return {"A": A, "B": B}

def apply_platt(p, params):
    A = float(params.get("A", 0.0)); B = float(params.get("B", 0.0))
    z = A * float(p) + B
    yhat = 1.0 / (1.0 + math.exp(-z))
    return max(0.0, min(1.0, yhat))

# Isotonic: monotonically increasing mapping using bin averages
def fit_isotonic(probs, labels, bins=10):
    if len(probs) == 0:
        return {"points": [[0.0, 0.0],[1.0,1.0]]}
    pairs = sorted([(probs[i], labels[i]) for i in range(len(probs))], key=lambda x: x[0])
    n = max(2, bins)
    size = max(1, len(pairs)//n)
    points = []
    for i in range(0, len(pairs), size):
        chunk = pairs[i:i+size]
        if not chunk: break
        px = sum([p for p,_ in chunk]) / len(chunk)
        py = sum([y for _,y in chunk]) / len(chunk)
        if points and py < points[-1][1]:
            py = points[-1][1]  # enforce monotonic non-decreasing
        points.append([px, min(1.0, max(0.0, py))])
    # ensure boundary points
    if points[0][0] > 0.0: points.insert(0, [0.0, points[0][1]])
    if points[-1][0] < 1.0: points.append([1.0, points[-1][1]])
    return {"points": points}

def apply_isotonic(p, model):
    pts = model.get("points", [[0.0, 0.0],[1.0,1.0]])
    xs = [x for x,_ in pts]; ys = [y for _,y in pts]
    i = bisect.bisect_left(xs, p)
    if i == 0: return ys[0]
    if i >= len(xs): return ys[-1]
    x0, x1 = xs[i-1], xs[i]; y0, y1 = ys[i-1], ys[i]
    if x1 == x0: return y1
    t = (p - x0) / (x1 - x0)
    return y0 + t * (y1 - y0)
