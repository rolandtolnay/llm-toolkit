# Use coarse upload-date filters for YouTube research

The YouTube Research CLI changes `--after` from an exact `YYYY-MM-DD` date to coarse upload-date values (`today`, `this_week`, `this_month`, `this_year`). This deliberately breaks the old date-style contract because LLM callers can choose coarse freshness windows more reliably than inventing exact dates, and ScrapeCreators exposes the same coarse model natively.
