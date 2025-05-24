import time

from datetime import datetime, timezone


def current_milli_time():
    return round(time.time() * 1000)


def current_epoch_timestamp():
    return int(time.time())

def format_to_github_timestamp(timestamp: int) -> str:
    dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

MAX_BUCKETS = 350
MIN_BUCKET_SECONDS = 60  # Global minimum bucket size: 1 minute
# Thresholds: (duration_threshold_seconds, minimum_bucket_size_for_threshold_seconds)
# Ordered from largest duration to smallest.
_INTERVAL_THRESHOLDS_SECONDS = [
    (2592001, 43200),  # > 30 days -> 12h minimum bucket
    (604801, 21600),  # > 7 days -> 6h minimum bucket
    (86401, 10800),  # > 1 day -> 3h minimum bucket
    (43201, 3600),  # > 12 hours -> 1h minimum bucket
    (21601, 1800),  # > 6 hours -> 30m minimum bucket
    (3601, 300),  # > 1 hour -> 5m minimum bucket
    (1801, 120),  # > 30 minutes -> 2m minimum bucket
    (1201, 60),  # > 20 minutes -> 1m minimum bucket
]
# Standard bucket sizes to round up to
STANDARD_BUCKET_SIZES_SECONDS = [
    60, 120, 300, 600, 900, 1800, 3600, 10800, 21600, 43200, 86400
]  # 1m, 2m, 5m, 10m, 15m, 30m, 1h, 3h, 6h, 12h, 1d

def calculate_timeseries_bucket_size(total_seconds):
    """Calculate appropriate bucket size based on duration, aiming for < MAX_BUCKETS buckets."""
    # The actual bucket size must be at least:
    # 1. The global minimum (MIN_BUCKET_SECONDS)
    # 2. The ideal size to stay under MAX_BUCKETS (ideal_bucket_size)
    # 3. The minimum required for the given duration (min_bucket_for_duration)

    if total_seconds <= 0:
        return MIN_BUCKET_SECONDS  # Fallback to minimum bucket size for invalid/zero duration

    # Calculate the ideal minimum bucket size to stay under MAX_BUCKETS
    ideal_bucket_size = (total_seconds + MAX_BUCKETS - 1) // MAX_BUCKETS

    min_bucket_for_duration = MIN_BUCKET_SECONDS  # Start with the global minimum
    for duration_threshold, min_bucket_for_threshold in _INTERVAL_THRESHOLDS_SECONDS:
        if total_seconds >= duration_threshold:
            min_bucket_for_duration = min_bucket_for_threshold
            break  # Found the largest applicable threshold, use its minimum

    calculated_bucket_size = max(MIN_BUCKET_SECONDS, ideal_bucket_size, min_bucket_for_duration)

    # Round up to the nearest standard bucket size
    for standard_size in STANDARD_BUCKET_SIZES_SECONDS:
        if calculated_bucket_size <= standard_size:
            return standard_size

    return STANDARD_BUCKET_SIZES_SECONDS[-1]
