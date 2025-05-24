import logging
import time

import requests

from integrations.processor import Processor

logger = logging.getLogger(__name__)


class SentryApiProcessor(Processor):
    client = None

    def __init__(self, api_key, org_slug):
        self.__api_key = api_key
        self.org_slug = org_slug

    def test_connection(self, timeout=None):
        try:
            url = f"https://sentry.io/api/0/organizations/{self.org_slug}/projects/"
            headers = {"Authorization": f"Bearer {self.__api_key}"}
            response = requests.request("GET", url, headers=headers)
            if response:
                if response.status_code == 200:
                    return True
                elif response.status_code == 429 or response.status_code == 403:
                    reset_in_epoch_seconds = int(response.headers.get("X-Sentry-Rate-Limit-Reset", None))
                    if reset_in_epoch_seconds:
                        time.sleep(reset_in_epoch_seconds - int(time.time()))
                        return self.get_connection()
                    else:
                        time.sleep(100)
                        return self.get_connection()
                else:
                    logger.error(f"Error occurred while testing sentry connection with status_code: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Exception occurred while testing sentry connection with error: {e}")
            raise e

    def fetch_issue_details(self, issue_id):
        try:
            url = f"https://sentry.io/api/0/issues/{issue_id}/"
            payload = {}
            headers = {"Authorization": f"Bearer {self.__api_key}"}
            response = requests.request("GET", url, headers=headers, data=payload)
            if response:
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429 or response.status_code == 403:
                    reset_in_epoch_seconds = int(response.headers.get("X-Sentry-Rate-Limit-Reset", None))
                    if reset_in_epoch_seconds:
                        time.sleep(reset_in_epoch_seconds - int(time.time()))
                        return self.fetch_issue_details(issue_id)
                    else:
                        time.sleep(100)
                        return self.fetch_issue_details(issue_id)
                else:
                    logger.error(
                        f"Error occurred while fetching sentry issue details for issue_id: {issue_id} "
                        f"with status_code: {response.status_code} and response: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Exception occurred while fetching sentry issue details for issue_id: {issue_id} with error: {e}")
        return None

    def fetch_issue_last_event(self, issue_id):
        try:
            url = f"https://sentry.io/api/0/organizations/{self.org_slug}/issues/{issue_id}/hashes/"
            payload = {}
            headers = {"Authorization": f"Bearer {self.__api_key}"}
            response = requests.get(url, headers=headers, data=payload)
            if response:
                if response.status_code == 200:
                    events = response.json()
                    if events:
                        latest_event = events[0]
                        return latest_event
                    else:
                        print("No events found for the specified issue.")
                elif response.status_code == 429 or response.status_code == 403:
                    reset_in_epoch_seconds = int(response.headers.get("X-Sentry-Rate-Limit-Reset", None))
                    if reset_in_epoch_seconds:
                        time.sleep(reset_in_epoch_seconds - int(time.time()))
                        return self.fetch_issue_details(issue_id)
                    else:
                        time.sleep(100)
                        return self.fetch_issue_details(issue_id)
                else:
                    logger.error(
                        f"Error occurred while fetching sentry issue details for issue_id: {issue_id} "
                        f"with status_code: {response.status_code} and response: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Exception occurred while fetching sentry issue details for issue_id: {issue_id} with error: {e}")
            return None
        return None

    def fetch_issues_with_query(self, project_slug, query, start_time=None, end_time=None):
        try:
            if query:
                url = f"https://sentry.io/api/0/projects/{self.org_slug}/{project_slug}/issues/?query={query}"
            else:
                url = f"https://sentry.io/api/0/projects/{self.org_slug}/{project_slug}/issues/"

            headers = {"Authorization": f"Bearer {self.__api_key}"}

            params = {}
            if start_time:
                params["start"] = start_time
            if end_time:
                params["end"] = end_time

            response = requests.get(url, headers=headers, params=params)

            if response:
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in (429, 403):
                    reset_in_epoch_seconds = int(response.headers.get("X-Sentry-Rate-Limit-Reset", None))
                    if reset_in_epoch_seconds:
                        time.sleep(reset_in_epoch_seconds - int(time.time()))
                        return self.fetch_issues_with_query(project_slug, query, start_time, end_time)
                    else:
                        time.sleep(100)
                        return self.fetch_issues_with_query(project_slug, query, start_time, end_time)
                else:
                    logger.error(f"Error occurred while issues with query status_code: {response.status_code} and response: {response.text}")
        except Exception as e:
            logger.error(f"Exception occurred while fetching recent errors with error: {e}")
            raise e

        return None

    def fetch_events_inside_issue(self, issue_id, project_slug, start_time=None, end_time=None):
        try:
            url = f"https://sentry.io/api/0/organizations/{self.org_slug}/issues/{issue_id}/events/"
            headers = {"Authorization": f"Bearer {self.__api_key}"}
            params = {}
            if start_time:
                params["start"] = start_time
            if end_time:
                params["end"] = end_time

            response = requests.get(url, headers=headers, params=params)

            if response:
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in (429, 403):
                    reset_in_epoch_seconds = int(response.headers.get("X-Sentry-Rate-Limit-Reset", None))
                    if reset_in_epoch_seconds:
                        time.sleep(reset_in_epoch_seconds - int(time.time()))
                        return self.fetch_events_inside_issue(issue_id, project_slug, start_time, end_time)
                    else:
                        time.sleep(100)
                        return self.fetch_events_inside_issue(issue_id, project_slug, start_time, end_time)
                else:
                    logger.error(f"Error occurred while fetching recent errors status_code: {response.status_code} and response: {response.text}")
        except Exception as e:
            logger.error(f"Exception occurred while fetching recent errors with error: {e}")
            raise e

    def fetch_event_details(self, event_id, project_slug=None):
        """
        Fetch detailed information about a specific Sentry event.
        """
        try:
            if project_slug:
                url = f"https://sentry.io/api/0/projects/{self.org_slug}/{project_slug}/events/{event_id}/"
            else:
                url = f"https://sentry.io/api/0/events/{self.org_slug}/{event_id}/"

            headers = {"Authorization": f"Bearer {self.__api_key}"}

            response = requests.get(url, headers=headers)

            if response:
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in (429, 403):
                    reset_in_epoch_seconds = int(response.headers.get("X-Sentry-Rate-Limit-Reset", None))
                    if reset_in_epoch_seconds:
                        time.sleep(reset_in_epoch_seconds - int(time.time()))
                        return self.fetch_event_details(event_id, project_slug)
                    else:
                        time.sleep(100)
                        return self.fetch_event_details(event_id, project_slug)
                else:
                    logger.error(
                        f"Error occurred while fetching event details for event_id: {event_id} "
                        f"with status_code: {response.status_code} and response: {response.text}"
                    )
        except Exception as e:
            logger.error(f"Exception occurred while fetching event details for event_id: {event_id} with error: {e}")
            raise e

        return None
