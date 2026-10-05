"""Support and Resistance Level Detection Service for Vibe Trader AI."""
from typing import List, Dict
from app.schemas.market import OHLCCandle
from app.schemas.analysis import SupportResistanceZone, SupportResistanceResponse


class SupportResistanceService:
    @staticmethod
    def calculate_zones(
        candles: List[OHLCCandle],
        symbol: str = "UNKNOWN",
        timeframe: str = "1h",
        tolerance: float = 0.008,  # 0.8% price clustering window
        k: int = 2                 # Swing window: local extremum within k bars on both sides
    ) -> SupportResistanceResponse:
        """
        Detects horizontal support and resistance levels using local swing highs/lows
        and clusters them based on a percentage tolerance window.
        """
        n = len(candles)
        if n < 5:
            current_price = candles[-1].close if n > 0 else 0.0
            return SupportResistanceResponse(
                symbol=symbol,
                timeframe=timeframe,
                current_price=current_price,
                zones=[]
            )

        current_price = candles[-1].close
        swing_highs: List[float] = []
        swing_lows: List[float] = []

        # 1. Identify local swing highs and swing lows
        for i in range(k, n - k):
            # Swing High
            is_high = True
            for offset in range(1, k + 1):
                if candles[i].high <= candles[i - offset].high or candles[i].high <= candles[i + offset].high:
                    is_high = False
                    break
            if is_high:
                swing_highs.append(candles[i].high)

            # Swing Low
            is_low = True
            for offset in range(1, k + 1):
                if candles[i].low >= candles[i - offset].low or candles[i].low >= candles[i + offset].low:
                    is_low = False
                    break
            if is_low:
                swing_lows.append(candles[i].low)

        # 2. Cluster swing points within tolerance percentage
        raw_points = swing_highs + swing_lows
        if not raw_points:
            # Fallback to absolute range extremes if no swing pivots detected
            highs = [c.high for c in candles]
            lows = [c.low for c in candles]
            raw_points = [max(highs), min(lows)]

        clusters: List[Dict] = []
        for price in raw_points:
            matched = False
            for cluster in clusters:
                avg = cluster["sum"] / cluster["count"]
                if abs(price - avg) / avg <= tolerance:
                    cluster["sum"] += price
                    cluster["count"] += 1
                    cluster["prices"].append(price)
                    matched = True
                    break
            if not matched:
                clusters.append({
                    "sum": price,
                    "count": 1,
                    "prices": [price]
                })

        # 3. For each cluster, compute touches across all candles
        zones: List[SupportResistanceZone] = []
        for cluster in clusters:
            avg_price = cluster["sum"] / cluster["count"]
            min_p = min(cluster["prices"])
            max_p = max(cluster["prices"])

            # Verify how many candles touched or wicked into this zone (+/- 0.4% band)
            band_half = avg_price * (tolerance * 0.5)
            band_low = avg_price - band_half
            band_high = avg_price + band_half

            touch_count = 0
            for c in candles:
                # Candle crosses or touches the band
                if not (c.high < band_low or c.low > band_high):
                    touch_count += 1

            touch_count = max(touch_count, cluster["count"])

            strength = "Minor"
            if touch_count >= 5:
                strength = "Strong"
            elif touch_count >= 3:
                strength = "Moderate"

            zone_type = "Resistance" if avg_price >= current_price else "Support"

            zones.append(SupportResistanceZone(
                price=round(avg_price, 4),
                zone_type=zone_type,
                touches=touch_count,
                strength=strength,
                timeframe=timeframe,
                min_price=round(min_p, 4),
                max_price=round(max_p, 4),
                calculation_method="Swing High/Low Cluster with Tolerance"
            ))

        # 4. Separate supports and resistances and rank by proximity to current price and strength
        supports = [z for z in zones if z.zone_type == "Support"]
        resistances = [z for z in zones if z.zone_type == "Resistance"]

        # Sort supports descending (closest to current price first)
        supports.sort(key=lambda z: (z.price), reverse=True)
        # Sort resistances ascending (closest to current price first)
        resistances.sort(key=lambda z: (z.price))

        # Keep top 3 supports and top 3 resistances
        final_zones = resistances[:3] + supports[:3]
        # Order by price descending overall for clean list representation
        final_zones.sort(key=lambda z: z.price, reverse=True)

        return SupportResistanceResponse(
            symbol=symbol,
            timeframe=timeframe,
            current_price=round(current_price, 4),
            zones=final_zones
        )
