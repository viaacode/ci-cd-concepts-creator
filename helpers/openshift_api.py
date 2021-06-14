#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List

import click
import requests
import yaml


class OpenShiftAPI:
    """Communicates with OpenShift via the REST API."""

    def __init__(self, url: str, api_token: str):
        self.url = url
        self.api_token = api_token

    def create_process_template(
        self, project: str, app_name: str, envs: List[str], data: bytes
    ):
        """Create the template and resources in OpenShift.

        First, we create the template in OpenShift.

        Then for every env, we fill in the values of the parameters and process the
        template. The result is a template with all the parameters replaced with
        their respective values.

        Lastly, every object in that processed template will be created
        in OpenShift.

        Args:
            project: The project to create the resources in.
            app_name: The name of the application.
            envs: The environments.
            data: The template.
        """
        # Set the auth token
        headers = {"Authorization": f"Bearer {self.api_token}"}

        yaml_object = yaml.safe_load(data)

        # Create the template
        response_template = requests.post(
            f"{self.url}/apis/template.openshift.io/v1/namespaces/{project}/templates",
            headers=headers,
            json=yaml_object,
        )
        response_template.raise_for_status()
        click.echo("Template created")
        for env in envs:
            # Process the template with the parameters filled in
            yaml_object["parameters"][0]["value"] = env
            response_processed = requests.post(
                f"{self.url}/apis/template.openshift.io/v1/namespaces/{project}/processedtemplates",
                headers=headers,
                json=yaml_object,
            )
            response_processed.raise_for_status()

            # The processed template
            proc_template = response_processed.json()
            # Create the service
            response_service = requests.post(
                f"{self.url}/api/v1/namespaces/{project}/services",
                headers=headers,
                json=proc_template["objects"][0],
            )
            response_service.raise_for_status()
            click.echo("Service created")

            # Create the deployment
            response_deployment = requests.post(
                f"{self.url}/apis/apps/v1/namespaces/{project}/deployments",
                headers=headers,
                json=proc_template["objects"][1],
            )
            response_deployment.raise_for_status()
            click.echo("Deployment created")

            # Create the config map
            response_config_map = requests.post(
                f"{self.url}/api/v1/namespaces/{project}/configmaps",
                headers=headers,
                json=proc_template["objects"][2],
            )
            response_config_map.raise_for_status()
            click.echo("Config map created")
