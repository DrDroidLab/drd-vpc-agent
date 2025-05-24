import time

import requests


def make_request_with_retry(method, url, headers=None, payload=None, max_retries=3, default_resend_delay=1):
    retries = 0
    while retries < max_retries:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, data=payload)
        else:
            raise ValueError(f"make_request_with_retry:: Unsupported method: {method}")

        # Check if we hit the rate limit
        if response.status_code == 429:  # Rate limit exceeded
            rate_limit_reset = int(response.headers.get("x-ratelimit-reset", default_resend_delay))
            print(f"Rate limit exceeded. Retrying in {rate_limit_reset} seconds...")
            time.sleep(rate_limit_reset)  # Wait until reset time
            retries += 1
        else:
            return response  # Return successful response

    raise Exception("make_request_with_retry:: Max retries reached")
