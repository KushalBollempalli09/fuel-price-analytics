# Fuel Price Analytics

A batch ELT pipeline analyzing real-time German fuel prices (Tankerkönig API) to answer a concrete operational question for a logistics fleet manager: where and when should trucks refuel to minimize cost?

**Stack:** Python (ingestion) → Postgres (raw + staging, via Docker) → dbt (transformation, testing) → Metabase (dashboard). Orchestrated via cron (scheduled ingestion) and a Makefile (`make all` runs the full pipeline).

---

## Stakeholder Brief: Fuel Cost Optimization for Fleet Operations

**The question:** Where and when should our trucks refuel to cut fuel spend, and which brands or regions show the most price volatility?

### Key finding: timing matters more than location

Diesel, E5, and E10 prices all follow the same daily pattern, confirmed independently across every day in the collection window: a low in the early morning (around 8-9am), a sharp spike between 10am-11am (roughly 15-18 cents/L above the morning low), then a steady decline through the afternoon into the cheapest window of the day, consistently in the evening (6pm-9pm).

This is not an artifact of this dataset — it matches published research from ADAC (Germany's automobile association) and the Bundeskartellamt's official fuel-price transparency office (Markttransparenzstelle für Kraftstoffe) on nationwide German fuel-pricing cycles.

**Recommendation: avoid refueling between 10am and 1pm. Prefer the evening window (6pm-9pm) when route scheduling allows.** At current price levels, this alone represents a ~6-7% swing in per-liter cost, before considering location.

### Regional findings

Among the 20 cities surveyed, the lowest average diesel prices were observed in:

| City | Avg. diesel price |
|---|---|
| München | €2.412 |
| Essen | €2.420 |
| Nürnberg | €2.428 |
| Bielefeld | €2.431 |
| Ludwigshafen am Rhein | €2.436 |

*(Full ranking and E5/E10 equivalents available in the Metabase dashboard.)*

### Brand consistency

Larger networks show tighter price spreads across their station footprint than smaller ones — ARAL and Shell (161 and 126 stations respectively) both show roughly a 34-cent spread between their cheapest and most expensive station, versus ~41 cents for AGIP ENI (16 stations). This suggests larger brands price more centrally/predictably, which may matter for a fleet building a preferred-station list rather than shopping station-by-station.

### Confidence and limitations

- **Sample window:** data collected over a 3-day period (Sept 15-17, 2026). The hourly and regional patterns held consistently across all 3 days individually, not just in the pooled average — but a longer collection window (2-4 weeks recommended) would materially strengthen confidence, particularly for the regional ranking.
- **"Region" means city, not corridor:** true route/corridor-level cost (accounting for actual driving distance between stations) would require road-network data not available to this project. "Cheapest region" here reflects average price by city.
- **Data quality:** raw station data included 61 inconsistent city-name spellings (casing, umlaut transliteration, neighborhood-level suffixes) for the 20 target cities, resolved via a mapping table (`city_name_mapping.csv`) with an accompanying dbt test to catch any future unmapped values.

### Next steps

- Extend data collection to 2-4 weeks to confirm seasonal/weekly stability of the hourly pattern
- If corridor-level (not city-level) recommendations become a priority, incorporate route-distance data (e.g., via a mapping/routing API) to model true "cheapest stop along the route" rather than "cheapest city"