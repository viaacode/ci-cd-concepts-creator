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


@click.command("create", short_help="Create the concepts")
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
    "--env-file",
    help="Env file",
    type=click.File("r"),
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
    env_file,
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
    env_vars = []
    if env_file:
        try:
            env_vars = [env_var.split("=")[0] for env_var in env_file.readlines()]
        except Exception as e:
            raise click.ClickException(f"Error parsing the env file: {e}")
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
    _create_jenkinsfile(app_name, openshift_folder, **dict(namespace=namespace))
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
        jenkins_api.create_job(namespace, app_name, job_definition)


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


if __name__ == "__main__":
    create()
