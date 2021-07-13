import os

import responses
import pytest

from helpers.openshift_api import OpenShiftAPI


@pytest.fixture
def open_shift_api():
    return OpenShiftAPI("https://localhost", "token")


@responses.activate
def test_create_process_template(open_shift_api):
    template_url = (
        "https://localhost/apis/template.openshift.io/v1/namespaces/project/templates"
    )
    processed_template_url = "https://localhost/apis/template.openshift.io/v1/namespaces/project/processedtemplates"
    service_url = "https://localhost/api/v1/namespaces/project/services"
    deployments_url = "https://localhost/apis/apps/v1/namespaces/project/deployments"
    trigger_url = (
        "https://localhost/apis/apps/v1/namespaces/project/deployments/appname-tst"
    )
    config_map_url = "https://localhost/api/v1/namespaces/project/configmaps"

    processed_template = {"objects": ["service", "deployment", "configmap"]}

    responses.add(responses.POST, template_url)
    responses.add(responses.POST, processed_template_url, json=processed_template)
    responses.add(responses.POST, service_url)
    responses.add(responses.POST, deployments_url)
    responses.add(responses.PATCH, trigger_url)
    responses.add(responses.POST, config_map_url)

    template_path = os.path.join(os.getcwd(), "tests", "resources", "template.yml")
    with open(template_path, "r") as file:
        yaml_object = file.read()

    open_shift_api.create_process_template("project", "appname", ["tst"], yaml_object)

    assert len(responses.calls) == 6
