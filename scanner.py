def score_stock(d):
    score = 50

    # =====================
    # 1. Momentum
    # =====================
    change = d.get("changePercentage", 0)
    if change > 3:
        score += 12
    elif change > 1:
        score += 6
    elif change < -3:
        score -= 10

    # =====================
    # 2. Trend
    # =====================
    price = d.get("price", 0)
    avg50 = d.get("priceAvg50", 0)

    if price and avg50:
        if price > avg50:
            score += 10
        else:
            score -= 5

    # =====================
    # 3. Quality (ROE / ROIC / Debt)
    # =====================
    roe = d.get("returnOnEquity")
    roic = d.get("returnOnInvestedCapital")
    debt = d.get("debtToEquity")

    if roe:
        score += 15 if roe > 0.15 else 8

    if roic:
        score += 15 if roic > 0.12 else 5

    if debt is not None:
        score += 10 if debt < 1 else -10

    # =====================
    # 4. Growth (V5核心)
    # =====================
    eps_growth = d.get("epsgrowth")
    revenue_growth = d.get("revenuegrowth")

    if eps_growth:
        score += 15 if eps_growth > 0.10 else 5

    if revenue_growth:
        score += 10 if revenue_growth > 0.08 else 3

    # =====================
    # 5. PEG (关键估值)
    # =====================
    peg = d.get("pegRatio")
    if peg:
        if peg < 1:
            score += 15
        elif peg < 1.5:
            score += 8
        else:
            score -= 5

    return score