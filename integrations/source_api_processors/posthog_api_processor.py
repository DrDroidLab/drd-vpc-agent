import logging

import requests

from integrations.processor import Processor

logger = logging.getLogger(__name__)

class PosthogApiProcessor(Processor):
    def __init__(self, posthog_host, personal_api_key, project_id):
        self.__host = posthog_host
        self.__api_key = personal_api_key
        self.__project_id = project_id
        self.headers = {
            "Authorization": f"Bearer {self.__api_key}",
            "Accept": "application/json"
        }

    def test_connection(self):
        try:
            url = f"{self.__host}/api/users/@me/"
            response = requests.get(url, headers=self.headers, timeout=20)
            response.raise_for_status()
            data = response.json()
            team = data.get("team", {}) if data else {}
            if str(team.get("project_id")) == self.__project_id:
                return True
            else:
                raise Exception(f"No project with id {self.__project_id} found.")
        except Exception as e:
            logger.error(f"Exception occurred while testing PostHog connection: {e}")
            raise e

    def fetch_projects(self):
        try:
            url = f"{self.__host}/api/projects/"
            response = requests.get(url, headers=self.headers)
            if response and response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to fetch PostHog projects. Status Code: {response.status_code}. Response Text: {response.text}")
        except Exception as e:
            logger.error(f"Exception occurred while fetching PostHog projects: {e}")
            raise e

    def fetch_dashboard_templates(self):
        try:
            url = f"{self.__host}/api/dashboard_templates/"
            response = requests.get(url, headers=self.headers)
            if response and response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to fetch PostHog dashboard templates. Status Code: {response.status_code}. Response Text: {response.text}")
        except Exception as e:
            logger.error(f"Exception occurred while fetching PostHog dashboard templates: {e}")
            raise e

    def fetch_events(self, event_name=None, properties=None, person_id=None, limit=100, after=None, before=None):
        """
        Fetch events from PostHog
        
        Args:
            event_name: Optional name of the event to filter by
            properties: Optional dictionary of property key-values to filter by 
            person_id: Optional person/user ID to filter events for a specific user
            limit: Number of events to return (default 100)
            
        Returns:
            List of event objects
        """
        try:
            url = f"{self.__host}/api/projects/{self.__project_id}/events/"
            params = {
                "limit": limit
            }
            
            if event_name:
                params["event"] = event_name
                
            # Add properties filtering if provided
            if properties and isinstance(properties, dict):
                property_filters = []
                for key, value in properties.items():
                    property_filters.append({"key": key, "value": value, "operator": "exact"})
                if property_filters:
                    params["properties"] = property_filters
            
            if person_id:
                params["person_id"] = person_id

            if after is not None:
                params["after"] = after
                
            if before is not None:
                params["before"] = before

            response = requests.get(url, headers=self.headers, params=params)
            return response.json().get("results", [])

        except Exception as e:
            logger.error(f"Exception occurred while fetching PostHog events: {e}")
            return []

    def fetch_persons(self, distinct_id=None, search=None, properties=None, limit=100, offset=0):
        """
        Fetch persons from PostHog
        
        Args:
            distinct_id: Optional distinct_id to filter by
            search: Optional search term to filter persons
            properties: Optional dictionary of property key-values to filter by
            limit: Number of persons to return (default 100)
            offset: Offset for pagination
            
        Returns:
            List of person objects
        """
        try:
            url = f"{self.__host}/api/projects/{self.__project_id}/persons/"
            params = {
                "limit": limit,
                "offset": offset
            }
            
            if distinct_id:
                url = f"{url}{distinct_id}/"
                
            if search:
                params["search"] = search
                
            # Add properties filtering if provided
            if properties and isinstance(properties, dict):
                property_filters = []
                for key, value in properties.items():
                    property_filters.append({"key": key, "value": value, "operator": "exact"})
                if property_filters:
                    params["properties"] = property_filters
                    
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                if distinct_id:
                    # When fetching a specific person by ID, the response is a single object
                    return [response.json()]
                else:
                    # When fetching multiple persons, results are in a 'results' field
                    return response.json().get("results", [])
            else:
                logger.error(f"Failed to fetch PostHog persons. Status Code: {response.status_code}. Response Text: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Exception occurred while fetching PostHog persons: {e}")
            return []
            
    def fetch_groups(self, group_type=None, group_key=None, search=None, limit=100, offset=0):
        """
        Fetch groups from PostHog
        
        Args:
            group_type: Optional group type to filter by
            group_key: Optional group key to filter by
            search: Optional search term to filter groups
            limit: Number of groups to return (default 100)
            offset: Offset for pagination
            
        Returns:
            List of group objects
        """
        try:
            url = f"{self.__host}/api/projects/{self.__project_id}/groups/"
            params = {
                "limit": limit,
                "offset": offset
            }
            
            if group_type is not None:
                params["group_type"] = group_type
                
            if group_key:
                params["group_key"] = group_key
                
            if search:
                params["search"] = search
                
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return response.json().get("results", [])
            else:
                logger.error(f"Failed to fetch PostHog groups. Status Code: {response.status_code}. Response Text: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Exception occurred while fetching PostHog groups: {e}")
            return []
            
    def fetch_group_types(self):
        """
        Fetch group types from PostHog
        
        Returns:
            List of group type objects
        """
        try:
            url = f"{self.__host}/api/projects/{self.__project_id}/groups_types/"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json().get("results", [])
            else:
                logger.error(f"Failed to fetch PostHog group types. Status Code: {response.status_code}. Response Text: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Exception occurred while fetching PostHog group types: {e}")
            return []
            
    def fetch_cohorts(self, cohort_id=None, search=None, limit=100, offset=0):
        """
        Fetch cohorts from PostHog
        
        Args:
            cohort_id: Optional cohort ID to filter by
            search: Optional search term to filter cohorts
            limit: Number of cohorts to return (default 100)
            offset: Offset for pagination
            
        Returns:
            List of cohort objects
        """
        try:
            url = f"{self.__host}/api/projects/{self.__project_id}/cohorts/"
            params = {
                "limit": limit,
                "offset": offset
            }
            
            if cohort_id:
                url = f"{url}{cohort_id}/"
                
            if search:
                params["search"] = search
                
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                if cohort_id:
                    # When fetching a specific cohort by ID, the response is a single object
                    return [response.json()]
                else:
                    # When fetching multiple cohorts, results are in a 'results' field
                    return response.json().get("results", [])
            else:
                logger.error(f"Failed to fetch PostHog cohorts. Status Code: {response.status_code}. Response Text: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Exception occurred while fetching PostHog cohorts: {e}")
            return []

    def execute_hogql_query(self, query):
        """
        Execute a HogQL query against PostHog
        
        Args:
            query: HogQL query string to execute
            
        Returns:
            Query results as a dictionary with 'results' and 'columns' keys
        """
        try:
            url = f"{self.__host}/api/projects/{self.__project_id}/query/"
            payload = {
                "query": {
                    "kind": "HogQLQuery",
                    "query": query
                }
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "results": data.get("results", []),
                    "columns": data.get("columns", [])
                }
            else:
                error_msg = f"Failed to execute HogQL query. Status Code: {response.status_code}. Response Text: {response.text}"
                logger.error(error_msg)
                return {
                    "error": error_msg,
                    "results": [],
                    "columns": []
                }
                
        except Exception as e:
            error_msg = f"Exception occurred while executing HogQL query: {e}"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "results": [],
                "columns": []
            }

    def fetch_property_definitions(self, limit=1000, offset=0):
        """
        Fetch property definitions from PostHog
        
        Args:
            limit: Number of properties to return (default 1000)
            offset: Offset for pagination
            
        Returns:
            List of property definition objects
        """
        try:
            url = f"{self.__host}/api/projects/{self.__project_id}/property_definitions/"
            params = {
                "limit": limit,
                "offset": offset
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                return response.json().get("results", [])
            else:
                logger.error(f"Failed to fetch PostHog property definitions. Status Code: {response.status_code}. Response Text: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Exception occurred while fetching PostHog property definitions: {e}")
            return []
