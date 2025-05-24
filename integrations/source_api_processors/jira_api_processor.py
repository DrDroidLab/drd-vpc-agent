import json
import logging
import re

import requests
from base64 import b64encode
from integrations.processor import Processor

logger = logging.getLogger(__name__)


class JiraApiProcessor(Processor):
    def __init__(self, jira_cloud_api_key, jira_domain, jira_email):
        if not all([jira_cloud_api_key, jira_domain, jira_email]):
            raise ValueError("All JIRA credentials (api_key, domain, email) are required")

        self.domain = jira_domain
        self.__username = jira_email
        self.__api_token = jira_cloud_api_key
        self.base_url = f"https://{jira_domain}.atlassian.net/rest/api/3"

    @staticmethod
    def _is_account_id(id_string):
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        # Pattern for Atlassian Cloud account IDs which often have a prefix like '712020:'
        atlassian_pattern = r'^[0-9]+:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'

        return bool(re.match(uuid_pattern, id_string, re.IGNORECASE) or
                    re.match(atlassian_pattern, id_string, re.IGNORECASE))

    @property
    def _auth_headers(self):
        credentials = f"{self.__username}:{self.__api_token}"
        encoded_credentials = b64encode(credentials.encode('utf-8')).decode('utf-8')
        return {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def test_connection(self, timeout=None):
        """Test JIRA connection by fetching current user"""
        try:
            url = f"{self.base_url}/myself"
            response = requests.get(url, headers=self._auth_headers, timeout=timeout)
            if response.status_code == 200:
                return True
            else:
                logger.error(f"JiraApiProcessor.test_connection:: Error testing JIRA connection for domain: "
                             f"{self.domain}. Status: {response.status_code}. Text: {response.text}")
                return False
        except Exception as e:
            logger.error(f"JiraApiProcessor.test_connection:: Exception occurred while testing JIRA connection for "
                         f"domain: {self.domain}. Error: {e}")
            return e

    def get_users(self, query=None):
        """Get a user in the JIRA instance"""
        try:
            url = f"{self.base_url}/user/search"
            params = {"query": query}
            response = requests.get(url, headers=self._auth_headers, params=params)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"JiraApiProcessor.get_users:: Error fetching JIRA users for domain: {self.domain}. "
                             f"Status {response.status_code}. Text: {response.text}")
                return None
        except Exception as e:
            logger.error(f"JiraApiProcessor.get_users:: Exception occurred while fetching JIRA users for domain: "
                         f"{self.domain}. Error: {e}")
            raise e

    def list_all_projects(self):
        try:
            url = f"{self.base_url}/project"
            response = requests.get(url, headers=self._auth_headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"JiraApiProcessor.list_all_projects:: Error fetching JIRA projects for domain: "
                             f"{self.domain}. Status: {response.status_code}. Text: {response.text}")
                return None
        except Exception as e:
            logger.error(f"JiraApiProcessor.list_all_projects:: Exception occurred while fetching JIRA projects for "
                         f"domain: {self.domain}. Error: {e}")
            raise e

    def list_all_users(self):
        try:
            url = f"{self.base_url}/users/search"
            response = requests.get(url, headers=self._auth_headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"JiraApiProcessor.list_all_users:: Error fetching JIRA all users for domain: "
                             f"{self.domain}. Status: {response.status_code}. Text: {response.text}")
                return None
        except Exception as e:
            logger.error(f"JiraApiProcessor.list_all_users:: Exception occurred while fetching JIRA all users for "
                         f"domain: {self.domain}. Error: {e}")
            raise e

    def get_ticket(self, ticket_key):
        try:
            url = f"{self.base_url}/issue/{ticket_key}"
            response = requests.get(url, headers=self._auth_headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"JiraApiProcessor.list_all_users:: Error fetching JIRA ticket for domain: {self.domain}. "
                             f"Status: {response.status_code}. Text: {response.text}")
                return None
        except Exception as e:
            logger.error(f"JiraApiProcessor.list_all_users:: Exception occurred while fetching JIRA ticket for domain: "
                         f"{self.domain}. Error: {e}")
            raise e

    def create_ticket(self, project_key, summary, description, issue_type="Task", priority=None,
                      labels=None, components=None, assignee=None, image_urls=None):
        try:
            url = f"{self.base_url}/issue"
            content = [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]
            if image_urls and len(image_urls) > 0:
                for img_url in image_urls:
                    if img_url and img_url.strip():
                        image_node = {
                            "type": "mediaSingle",
                            "content": [
                                {
                                    "type": "media",
                                    "attrs": {
                                        "type": "external",
                                        "url": img_url.strip()
                                    }
                                }
                            ]
                        }
                        content.append(image_node)
            adf_description = {"type": "doc", "version": 1, "content": content}

            fields = {"project": {"key": project_key}, "summary": summary, "description": adf_description,
                      "issuetype": {"name": issue_type}}

            # Clean and validate labels if provided
            if labels:
                if isinstance(labels, str):
                    # Split string into list and clean each label
                    cleaned_labels = [label.replace(" ", "").strip() for label in labels.split(',') if label.strip()]
                else:
                    # Clean each label in the list
                    cleaned_labels = [label.replace(" ", "").strip() for label in labels if label.strip()]

                if cleaned_labels:
                    fields["labels"] = cleaned_labels

            if priority:
                fields["priority"] = {"name": priority}

            # Add assignee if provided
            if assignee:
                if self._is_account_id(assignee):
                    logger.info(f"JiraApiProcessor.create_ticket:: Using direct account ID for domain: {self.domain} "
                                f"and assignee: {assignee}")
                    fields["assignee"] = {"accountId": assignee}
                else:
                    logger.info(f"JiraApiProcessor.create_ticket:: Looking up user with name/query: {assignee} for "
                                f"domain: {self.domain}")
                    users = self.get_users(query=assignee)
                    if users and len(users) > 0:
                        account_id = users[0]['accountId']
                        logger.info(f"Found account ID {account_id} for user {assignee}")
                        fields["assignee"] = {"accountId": account_id}
                    else:
                        logger.warning(f"JiraApiProcessor.create_ticket:: Could not find user with name '{assignee}', "
                                       f"ticket will be created unassigned for domain: {self.domain}")
            payload = {"fields": fields}
            logger.debug(f"Creating JIRA ticket with payload: {payload}")
            response = requests.post(url, headers=self._auth_headers, json=payload)
            if response.status_code in (200, 201):
                return response.json()
            elif response.status_code == 400:
                error_json = response.json()
                error_details = error_json.get('errors', {})
                if 'priority' in error_details:
                    logger.warning(f"JiraApiProcessor.create_ticket:: Priority field not supported, retrying without "
                                   f"priority for domain: {self.domain}")
                    if "priority" in fields:
                        del fields["priority"]
                    payload = {"fields": fields}
                    response = requests.post(url, headers=self._auth_headers, json=payload)
                    if response.status_code in (200, 201):
                        return response.json()
                if 'assignee' in error_details:
                    logger.warning(f"JiraApiProcessor.create_ticket:: Assignee field caused an error, retrying "
                                   f"without assignee for domain: {self.domain}")
                    if "assignee" in fields:
                        del fields["assignee"]
                    payload = {"fields": fields}
                    response = requests.post(url, headers=self._auth_headers, json=payload)
                    if response.status_code in (200, 201):
                        return response.json()
                logger.error(f"JiraApiProcessor.create_ticket:: JIRA API error details: {error_details} for domain: "
                             f"{self.domain}")
            logger.error(f"JiraApiProcessor.create_ticket:: Error creating JIRA ticket for domain: {self.domain}. "
                         f"Status: {response.status_code}. Text: {response.text}")
            return None
        except Exception as e:
            logger.error(f"JiraApiProcessor.create_ticket:: Exception occurred while creating JIRA ticket for domain: "
                         f"{self.domain}. Error: {e}")
            raise e

    def get_issue_types_for_project(self, project_key):
        try:
            # Get project metadata which includes issue types
            project_data = self.get_project_metadata(project_key)
            if not project_data or 'issueTypes' not in project_data:
                logger.error(f"JiraApiProcessor.get_issue_types_for_project:: Could not fetch issue types for project "
                             f"{project_key} and domain: {self.domain}")
                return None
            # Extract issue types
            issue_types = []
            for issue_type in project_data['issueTypes']:
                issue_types.append({
                    'id': issue_type.get('id'),
                    'name': issue_type.get('name')
                })
            return issue_types
        except Exception as e:
            logger.error(f"JiraApiProcessor.get_issue_types_for_project:: Exception while fetching issue types for "
                         f"project {project_key} and domain: {self.domain}. Error: {e}")
            return None

    def assign_ticket(self, ticket_key, assignee):
        try:
            url = f"{self.base_url}/issue/{ticket_key}/assignee"
            payload = {"accountId": assignee}

            response = requests.put(url, headers=self._auth_headers, json=payload)

            if response.status_code == 204:
                return True
            else:
                logger.error(f"JiraApiProcessor.assign_ticket:: Error assigning JIRA ticket for domain: "
                             f"{self.domain}. Statue: {response.status_code}. Text: {response.text}")
                return False
        except Exception as e:
            logger.error(f"JiraApiProcessor.assign_ticket:: Exception occurred while assigning JIRA ticket for domain: "
                         f"{self.domain}. Error: {e}")
            raise e

    def get_project_metadata(self, project_key):
        try:
            url = f"{self.base_url}/project/{project_key}"
            response = requests.get(url, headers=self._auth_headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"JiraApiProcessor.get_project_metadata:: Error fetching project metadata for domain: "
                             f"{self.domain}. Status: {response.status_code}. Text: {response.text}")
                return None
        except Exception as e:
            logger.error(f"JiraApiProcessor.get_project_metadata:: Exception occurred while fetching project metadata "
                         f"for domain: {self.domain}. Error: {e}")
            raise e

    def search_tickets(self, query, max_results=10):
        try:
            url = f"{self.base_url}/search/jql"
            payload = {"jql": query, "maxResults": max_results}
            response = requests.post(url, headers=self._auth_headers, data=json.dumps(payload))
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"JiraApiProcessor.search_tickets:: Error searching JIRA tickets for domain: "
                             f"{self.domain}. Status: {response.status_code}. Text: {response.text}")
                return None
        except Exception as e:
            logger.error(f"JiraApiProcessor.search_tickets:: Exception occurred while searching JIRA tickets for "
                         f"domain: {self.domain}. Error: {e}")
            raise e

    def add_comment(self, ticket_key, comment_text, image_urls=None):
        try:
            url = f"{self.base_url}/issue/{ticket_key}/comment"
            content = [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": comment_text
                        }
                    ]
                }
            ]
            if image_urls and len(image_urls) > 0:
                for img_url in image_urls:
                    if img_url and img_url.strip():
                        image_node = {
                            "type": "mediaSingle",
                            "content": [
                                {
                                    "type": "media",
                                    "attrs": {
                                        "type": "external",
                                        "url": img_url.strip()
                                    }
                                }
                            ]
                        }
                        content.append(image_node)

            comment_body = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": content
                }
            }

            logger.debug(f"JiraApiProcessor.add_comment:: Adding comment to JIRA ticket {ticket_key} for domain: "
                         f"{self.domain}")
            response = requests.post(url, headers=self._auth_headers, json=comment_body)
            if response.status_code in (201, 200):
                return response.json()
            else:
                logger.error(f"JiraApiProcessor.add_comment:: Error adding comment to JIRA ticket for domain: "
                             f"{self.domain}. Ticket: {ticket_key}. Status: {response.status_code}. Text: "
                             f"{response.text}")
                return None
        except Exception as e:
            logger.error(f"JiraApiProcessor.add_comment:: Exception occurred while adding comment to JIRA ticket "
                         f"{ticket_key} and domain: {self.domain}. Error: {e}")
            raise e
