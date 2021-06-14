#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from uuid import uuid4

import click

from helpers.concepts import OpenShiftTemplate, JenkinsMultibranchPipeline


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
    help="The folder of the project the files to.",
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
            env_vars = [env_vars.split("=")[0] for env_var in env_file.readlines()]
        except Exception as e:
            raise click.ClickException(f"Error parsing the env file: {e}")
    _create_openshift_template(
        app_name,
        output_folder,
        **dict(
            namespace=namespace,
            app_type=app_type,
            openshift_folder=openshift_folder,
            memory_requested=memory_requested,
            cpu_requested=cpu_requested,
            memory_limit=memory_limit,
            cpu_limit=cpu_limit,
            env_vars=env_vars,
        ),
    )
    # Create Jenkins multibranch pipeline
    _create_jenkins_multibranch_pipeline(
        app_name,
        output_folder,
        **dict(
            uuid=str(uuid4()),
            main_branch=main_branch,
        ),
    )


def _create_openshift_template(app_name, output_folder, **kwargs):
    template = OpenShiftTemplate(app_name, output_folder)
    template.create_concept(**kwargs)
    click.echo(f"Wrote OpenShift template file ({template.construct_filename()})")


def _create_jenkins_multibranch_pipeline(app_name, output_folder, **kwargs):
    pipeline = JenkinsMultibranchPipeline(app_name, output_folder)
    pipeline.create_concept(**kwargs)
    click.echo(
        f"Wrote Jenkins multibranch pipeline file ({pipeline.construct_filename()})"
    )


if __name__ == "__main__":
    create()
