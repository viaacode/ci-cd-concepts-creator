#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click
import requests


class JenkinsAPI:
    """Communicates with Jenkins via the REST API."""

    def __init__(self, url: str, api_user: str, api_token: str):
        self.url = url
        self.user = api_user
        self.token = api_token

    def create_multibranch_pipeline(
        self, folder: str, app_name: str, data: bytes
    ) -> bool:
        """Create the multibranch job in Jenkins.

        Args:
            folder: The folder of the multibranch pipeline.
            app_name: The name of the application.
            data: The template.

        Returns:
            True if successful.
        """
        headers = {"Content-Type": "application/xml"}
        query_params = {"name": app_name}
        response = requests.post(
            f"{self.url}/job/{folder}/createItem",
            auth=(self.user, self.token),
            headers=headers,
            params=query_params,
            data=data,
            verify=False,
        )
        response.raise_for_status()
        click.echo("Jenkins multibranch pipeline created")
        return response.status_code == 200

    def get_multibranch_pipeline(self, folder: str, app_name: str) -> str:
        """Get the multibranch job in Jenkins.

        Args:
            folder: The folder of the multibranch pipeline.
            app_name: The name of the application.

        Returns:
            The multibranch pipeline in XML format.
        """
        response = requests.get(
            f"{self.url}/job/{folder}/job/{app_name}/config.xml",
            auth=(self.user, self.token),
            verify=False,
        )
        return response.text
