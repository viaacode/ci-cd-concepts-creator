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
        name = f"{self.app_name}_{self._template_basename()}"
        return os.path.join(self.output_folder, name)

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
        """The path to the template file."""
        pass

    @abstractmethod
    def _template_basename(self) -> str:
        """The basename of the template file."""
        pass
