#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from uuid import uuid4

import click

from helpers.jenkins_api import JenkinsAPI
from helpers.openshift_api import OpenShiftAPI
from helpers.concepts import (
    MakeFile,
    OpenShiftTemplate,
    JenkinsMultibranchPipeline,
    JenkinsFile,
)


@click.group()
def group():
    pass


@group.command("create", short_help="Create the concepts")
@click.argument("namespace")
@click.argument("app_name")
@click.option(
    "--main-branch",
    default="main",
    help="The name of the main branch of the repository",
    show_default=True,
)
@click.option(
    "--envs",
    multiple=True,
    default=[
        "int",
        "qas",
        "prd",
    ],
    help="environments",
    type=click.Choice(
        [
            "int",
            "qas",
            "prd",
        ],
        case_sensitive=False,
    ),
    show_default=True,
)
@click.option(
    "--app-type",
    default="exec",
    help="Type of the app.",
    type=click.Choice(["web-app", "exec"], case_sensitive=False),
    show_default=True,
)
@click.option(
    "-o",
    "--output-folder",
    default=".",
    help="The folder of the project the files to. The files will be written in a subfolder 'openshift'.",
    type=click.Path(file_okay=False, writable=True),
    show_default=True,
)
@click.option(
    "--base-image",
    default="python:3.7",
    help="The base image used to run the tests in.",
    type=str,
    show_default=True,
)
@click.option(
    "--env-file",
    help="File containing the keys which will be added as separate env vars in the deployment",
    type=click.File("r"),
)
@click.option(
    "--config-map-file",
    help="File containing the keys which will be added in a config map",
    type=click.File("r"),
)
@click.option(
    "--secrets-file",
    help="File containing the keys which will be added in a secrets",
    type=click.File("r"),
)
@click.option(
    "--replicas",
    default=0,
    help="Amount of replicas of the deployment.",
    type=int,
    show_default=True,
)
@click.option(
    "--service-port",
    default=8080,
    help="The port the service should run on.",
    type=int,
    show_default=True,
)
@click.option(
    "--memory-requested",
    default=128,
    help="Minimum requested memory in Mebibytes.",
    type=int,
    show_default=True,
)
@click.option(
    "--cpu-requested",
    default=100,
    help="Minimum requested CPU.",
    type=int,
    show_default=True,
)
@click.option(
    "--memory-limit",
    default=328,
    help="Maximum limit of memory in Mebibytes.",
    type=int,
    show_default=True,
)
@click.option(
    "--cpu-limit",
    default=300,
    help="Maximum limit of CPU.",
    type=int,
    show_default=True,
)
@click.option(
    "--upload",
    default=False,
    help="Upload/create in Openshift/Jenkins.",
    type=bool,
    is_flag=True,
    show_default=True,
)
@click.option("--openshift-api-url", envvar="OPENSHIFT_API_URL")
@click.option("--openshift-api-token", envvar="OPENSHIFT_API_TOKEN")
@click.option("--jenkins-api-url", envvar="JENKINS_API_URL")
@click.option("--jenkins-api-user", envvar="JENKINS_API_USER")
@click.option("--jenkins-api-token", envvar="JENKINS_API_TOKEN")
def create(
    namespace,
    app_name,
    main_branch,
    envs,
    app_type,
    output_folder,
    base_image,
    env_file,
    config_map_file,
    secrets_file,
    replicas,
    service_port,
    memory_requested,
    cpu_requested,
    memory_limit,
    cpu_limit,
    upload,
    openshift_api_url,
    openshift_api_token,
    jenkins_api_url,
    jenkins_api_user,
    jenkins_api_token,
):
    """Create the openshift concepts

    NAMESPACE: The namespace of the app.\n
    APP NAME: The name of the app.

    """
    # Assemble openshift folder to write to.
    openshift_folder = os.path.join(output_folder, "openshift")
    # Create openshift subfolder if it not yet exists.
    Path(openshift_folder).mkdir(parents=True, exist_ok=True)

    # Create OpenShift template
    env_vars, cm_keys, secrets = [], [], []
    if env_file:
        try:
            env_vars: list = [
                env_var.strip().split("=")[0] for env_var in env_file.readlines()
            ]
        except Exception as e:
            raise click.ClickException(f"Error parsing the env file: {e}")
    if config_map_file:
        try:
            cm_keys: list = [
                cm_key.strip().split("=")[0] for cm_key in config_map_file.readlines()
            ]
        except Exception as e:
            raise click.ClickException(f"Error parsing the config map file: {e}")
    if secrets_file:
        try:
            secrets: list = [
                secret.strip().split("=")[0] for secret in secrets_file.readlines()
            ]
        except Exception as e:
            raise click.ClickException(f"Error parsing the secrets file: {e}")
    template_definition = _create_openshift_template(
        app_name,
        openshift_folder,
        **dict(
            namespace=namespace,
            app_type=app_type,
            memory_requested=memory_requested,
            cpu_requested=cpu_requested,
            memory_limit=memory_limit,
            cpu_limit=cpu_limit,
            env_vars=env_vars,
            cm_keys=cm_keys,
            secrets=secrets,
            replicas=replicas,
            service_port=service_port,
        ),
    )
    # Create Jenkins multibranch pipeline
    job_definition = _create_jenkins_multibranch_pipeline(
        app_name,
        openshift_folder,
        **dict(
            uuid=str(uuid4()),
            main_branch=main_branch,
        ),
    )
    # Create Jenkinsfile with declarative pipeline
    _create_jenkinsfile(
        app_name, openshift_folder, **dict(namespace=namespace, base_image=base_image)
    )
    # Create Makefile
    _create_makefile(app_name, openshift_folder)

    if upload:
        # OpenShift
        openshift_api = OpenShiftAPI(openshift_api_url, openshift_api_token)
        openshift_api.create_process_template(
            namespace, app_name, envs, template_definition
        )
        # Jenkins
        jenkins_api = JenkinsAPI(jenkins_api_url, jenkins_api_user, jenkins_api_token)
        jenkins_api.create_multibranch_pipeline(namespace, app_name, job_definition)


def _create_openshift_template(app_name, output_folder, **kwargs) -> str:
    template = OpenShiftTemplate(app_name, output_folder)
    template_yaml = template.create_concept(**kwargs)
    click.echo(f"Wrote OpenShift template file ({template.construct_filename()})")
    return template_yaml


def _create_jenkins_multibranch_pipeline(app_name, output_folder, **kwargs) -> str:
    pipeline = JenkinsMultibranchPipeline(app_name, output_folder)
    pipeline_xml = pipeline.create_concept(**kwargs)
    click.echo(
        f"Wrote Jenkins multibranch pipeline file ({pipeline.construct_filename()})"
    )
    return pipeline_xml


def _create_jenkinsfile(app_name, output_folder, **kwargs) -> str:
    jenkinsfile = JenkinsFile(app_name, output_folder)
    jenkinsfile_text = jenkinsfile.create_concept(**kwargs)
    click.echo(f"Wrote Jenkinsfile ({jenkinsfile.construct_filename()})")
    return jenkinsfile_text


def _create_makefile(app_name, output_folder, **kwargs) -> str:
    makefile = MakeFile(app_name, output_folder)
    makefile_text = makefile.create_concept(**kwargs)
    click.echo(f"Wrote Makefile ({makefile.construct_filename()})")
    return makefile_text


@group.command("upload", short_help="Upload the concepts")
@click.argument("namespace")
@click.argument("app_name")
@click.argument(
    "output_folder",
    type=click.Path(file_okay=False),
)
@click.option(
    "--envs",
    multiple=True,
    default=[
        "int",
        "qas",
        "prd",
    ],
    help="environments",
    type=click.Choice(
        [
            "int",
            "qas",
            "prd",
        ],
        case_sensitive=False,
    ),
    show_default=True,
)
@click.option("--openshift-api-url", envvar="OPENSHIFT_API_URL")
@click.option("--openshift-api-token", envvar="OPENSHIFT_API_TOKEN")
@click.option("--jenkins-api-url", envvar="JENKINS_API_URL")
@click.option("--jenkins-api-user", envvar="JENKINS_API_USER")
@click.option("--jenkins-api-token", envvar="JENKINS_API_TOKEN")
def upload(
    namespace,
    app_name,
    output_folder,
    envs,
    openshift_api_url,
    openshift_api_token,
    jenkins_api_url,
    jenkins_api_user,
    jenkins_api_token,
):
    """Upload the openshift concepts

    NAMESPACE: The namespace of the app.\n
    APP NAME: The name of the app.\n
    FOLDER: The folder where the concepts reside.\n

    """

    # OpenShift
    template = OpenShiftTemplate(app_name, output_folder)
    template_yaml = template.load_rendered_concept()
    if template_yaml:
        openshift_api = OpenShiftAPI(openshift_api_url, openshift_api_token)
        openshift_api.create_process_template(namespace, app_name, envs, template_yaml)

    # Jenkins
    pipeline = JenkinsMultibranchPipeline(app_name, output_folder)
    pipeline_xml = pipeline.load_rendered_concept()
    if pipeline_xml:
        jenkins_api = JenkinsAPI(jenkins_api_url, jenkins_api_user, jenkins_api_token)
        jenkins_api.create_multibranch_pipeline(namespace, app_name, pipeline_xml)


if __name__ == "__main__":
    group()
