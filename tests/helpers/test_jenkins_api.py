import responses
import pytest

from helpers.jenkins_api import JenkinsAPI


@pytest.fixture
def jenkins_api():
    return JenkinsAPI("https://localhost", "user", "token")


@responses.activate
def test_create_multibranch_pipeline(jenkins_api):
    url = "https://localhost/job/folder/createItem?name=appname"
    definition = "<xml/>"
    responses.add(
        responses.POST,
        url,
        body="",
    )
    assert jenkins_api.create_multibranch_pipeline("folder", "appname", data=definition)

    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == url
    assert responses.calls[0].request.method == "POST"
    assert responses.calls[0].request.body == definition

    assert responses.calls[0].response.status_code == 200


@responses.activate
def test_get_multibranch_pipeline(jenkins_api):
    url = "https://localhost/job/folder/job/appname/config.xml"
    definition = "<xml/>"
    responses.add(responses.GET, url, body=definition)
    response = jenkins_api.get_multibranch_pipeline("folder", "appname")
    assert response == definition

    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == url
    assert responses.calls[0].request.method == "GET"

    assert responses.calls[0].response.status_code == 200
    assert responses.calls[0].response.text == definition
