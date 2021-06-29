#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from abc import ABC, abstractmethod

from helpers.jinja_template import JinjaTemplate


class Concept(ABC):
    """Creates a serialized file of a concept.

    Loads in the appropriate template and renders it given the template parameters.
    The result will be written to the given output folder.

    Args:
        app_name: The name of the app.
        output_folder: Folder to write the processed template to.
    """

    def __init__(self, app_name: str, output_folder: str = os.getcwd()):
        self.app_name = app_name
        self.output_folder = output_folder

    def render_template(self, **kwargs) -> str:
        """Loads in the jinja2 template and renders it.

        Args:
            kwargs: The key-values to render the template with.

        Returns:
            The rendered template.
        """
        jinja = JinjaTemplate(self._template_path())
        return jinja.render_template(
            self._template_basename(), app_name=self.app_name, **kwargs
        )

    def construct_filename(self) -> str:
        """The filename to write to concept to."""
        return os.path.join(self.output_folder, self._output_basename())

    def create_concept(self, **kwargs) -> str:
        """Create and write the concept to a file.

        Args:
            **kwargs: The parameters to render the template with.
        Returns:
            The rendered template."""
        concept = self.render_template(**kwargs)
        with open(self.construct_filename(), "w") as f:
            f.writelines(concept)
        return concept

    @abstractmethod
    def _template_path(self) -> str:
        """The path to the Jinja2 template file."""
        pass

    @abstractmethod
    def _template_basename(self) -> str:
        """The basename of the Jinja2 template file."""
        pass

    @abstractmethod
    def _output_basename(self) -> str:
        """The basename of the rendered file."""
        pass


class JenkinsMultibranchPipeline(Concept):
    """Create a multibranch pipeline file in the XML format."""

    def _template_path(self) -> str:
        return os.path.join(os.getcwd(), "templates", "jenkins")

    def _template_basename(self) -> str:
        return "multibranch_pipeline.xml"

    def _output_basename(self) -> str:
        return f"{self.app_name}_{self._template_basename()}"


class OpenShiftTemplate(Concept):
    """Create an OpenShift template file in the YAML format."""

    def _template_path(self) -> str:
        return os.path.join(os.getcwd(), "templates", "openshift")

    def _template_basename(self) -> str:
        return "template.yml"

    def _output_basename(self) -> str:
        return f"{self.app_name}_{self._template_basename()}"


class JenkinsFile(Concept):
    """Create a Jenkinsfile for a declarative pipeline."""

    def _template_path(self) -> str:
        return os.path.join(os.getcwd(), "templates", "jenkins")

    def _template_basename(self) -> str:
        return "Jenkinsfile"

    def _output_basename(self) -> str:
        return self._template_basename()


class MakeFile(Concept):
    """Create a Makefile to be used in the pipeline."""

    def _template_path(self) -> str:
        return os.path.join(os.getcwd(), "templates", "jenkins")

    def _template_basename(self) -> str:
        return "Makefile"

    def _output_basename(self) -> str:
        return self._template_basename()
