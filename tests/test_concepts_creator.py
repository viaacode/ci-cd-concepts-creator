from unittest.mock import patch
from uuid import UUID

from click.testing import CliRunner

from concepts_creator import create

APP_NAME = "test"
ENVIRONMENT = "env"

PARAMS_MANDATORY = [
    APP_NAME,
    ENVIRONMENT,
]


@patch("concepts_creator.JenkinsAPI")
@patch("concepts_creator.OpenShiftAPI")
@patch("concepts_creator.OpenShiftTemplate")
@patch("concepts_creator.JenkinsMultibranchPipeline")
def test_create(
    jenkins_multibranch_pipeline, open_shift_template, open_shift_api, jenkins_api
):
    runner = CliRunner()
    result = runner.invoke(
        create,
        PARAMS_MANDATORY,
    )
    assert result.exit_code == 0
    assert jenkins_api.call_count == 0
    assert open_shift_api.call_count == 0

    jenkins_multibranch_pipeline.assert_called_once_with("env", "./openshift")
    j_kwargs = jenkins_multibranch_pipeline().create_concept.call_args.kwargs
    assert j_kwargs["main_branch"] == "main"
    assert UUID(j_kwargs["uuid"], version=4)  # Check if UUID

    assert open_shift_template.call_count == 1
    open_shift_template.assert_called_once_with("env", "./openshift")
    open_shift_template().create_concept.assert_called_once_with(
        **dict(
            namespace="test",
            app_type="exec",
            memory_requested=128,
            cpu_requested=100,
            memory_limit=328,
            cpu_limit=300,
            env_vars=[],
            replicas=0,
        )
    )
