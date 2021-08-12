import os
from unittest.mock import patch
from uuid import UUID

from click.testing import CliRunner

from concepts_creator import create, upload


NAMESPACE = "namespace"
APP_NAME = "test"
OUTPUT_FOLDER = "."

PARAMS_MANDATORY_CREATE = [
    NAMESPACE,
    APP_NAME,
]

PARAMS_MANDATORY_UPLOAD = [
    NAMESPACE,
    APP_NAME,
    OUTPUT_FOLDER,
]


@patch("concepts_creator.JenkinsAPI")
@patch("concepts_creator.OpenShiftAPI")
@patch("concepts_creator.OpenShiftTemplate")
@patch("concepts_creator.JenkinsMultibranchPipeline")
@patch("concepts_creator.JenkinsFile")
@patch("concepts_creator.MakeFile")
def test_create(
    make_file,
    jenkins_file,
    jenkins_multibranch_pipeline,
    open_shift_template,
    open_shift_api,
    jenkins_api,
):
    runner = CliRunner()
    result = runner.invoke(
        create,
        PARAMS_MANDATORY_CREATE,
    )
    assert result.exit_code == 0
    assert jenkins_api.call_count == 0
    assert open_shift_api.call_count == 0

    jenkins_multibranch_pipeline.assert_called_once_with(APP_NAME, "./openshift")
    j_kwargs = jenkins_multibranch_pipeline().create_concept.call_args.kwargs
    assert j_kwargs["main_branch"] == "main"
    assert UUID(j_kwargs["uuid"], version=4)  # Check if UUID

    open_shift_template.assert_called_once_with(APP_NAME, "./openshift")
    open_shift_template().create_concept.assert_called_once_with(
        **dict(
            namespace=NAMESPACE,
            app_type="exec",
            memory_requested=128,
            cpu_requested=100,
            memory_limit=328,
            cpu_limit=300,
            env_vars=[],
            replicas=0,
        )
    )
    # Jenkinsfile
    jenkins_file.assert_called_once_with(APP_NAME, "./openshift")
    jenkins_file().create_concept.assert_called_once_with(
        **dict(namespace=NAMESPACE, base_image="python:3.7")
    )
    # Makefile
    make_file.assert_called_once_with(APP_NAME, "./openshift")
    make_file().create_concept.assert_called_once()


@patch("concepts_creator.JenkinsAPI")
@patch("concepts_creator.OpenShiftAPI")
@patch("concepts_creator.OpenShiftTemplate")
@patch("concepts_creator.JenkinsMultibranchPipeline")
@patch.dict(
    os.environ,
    {
        "OPENSHIFT_API_URL": "OPENSHIFT_API_URL",
        "OPENSHIFT_API_TOKEN": "OPENSHIFT_API_TOKEN",
        "JENKINS_API_URL": "JENKINS_API_URL",
        "JENKINS_API_USER": "JENKINS_API_USER",
        "JENKINS_API_TOKEN": "JENKINS_API_TOKEN",
    },
)
def test_upload(
    jenkins_multibranch_pipeline, open_shift_template, open_shift_api, jenkins_api
):
    runner = CliRunner()
    result = runner.invoke(
        upload,
        PARAMS_MANDATORY_UPLOAD,
    )
    assert result.exit_code == 0

    # OpenShift
    open_shift_template.assert_called_once_with(APP_NAME, ".")
    open_shift_template().load_rendered_concept.assert_called_once()
    open_shift_api.assert_called_once_with("OPENSHIFT_API_URL", "OPENSHIFT_API_TOKEN")
    open_shift_api().create_process_template.assert_called_once_with(
        NAMESPACE,
        APP_NAME,
        ("int", "qas", "prd"),
        open_shift_template().load_rendered_concept.return_value,
    )

    # Jenkins
    jenkins_multibranch_pipeline.assert_called_once_with(APP_NAME, ".")
    jenkins_multibranch_pipeline().load_rendered_concept.assert_called_once()
    jenkins_api.assert_called_once_with(
        "JENKINS_API_URL", "JENKINS_API_USER", "JENKINS_API_TOKEN"
    )
    jenkins_api().create_multibranch_pipeline.assert_called_once_with(
        NAMESPACE,
        APP_NAME,
        jenkins_multibranch_pipeline().load_rendered_concept.return_value,
    )
