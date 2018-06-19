"""
Classes that processes printing engine's data to yaml file via templates
"""

from string import Template

from helpers.config import yaml as yaml_config


class YamlGenerator:
    template_dir = "templates/"
    template_separator = "\n###############################################" "################################\n\n"
    template_empty_arr = "[]"
    level_indent = " " * 2

    def __init__(self, config):
        self.config = config

    def get_header(self, header, empty=False, level=0):
        """
        Get header form yaml section

        Arguments:
            header (str): name of the section
            empty (boolean): True - section contains empty array, False -
                section items will follow
        Returns: (string) section header
        """
        add = separator = ""
        if empty:
            add = " " + self.template_empty_arr
        if level == 0:
            separator = self.template_separator
        return "{separator}{indent}{header}:{add}\n".format(
            separator=separator,
            indent=self.level_indent * level,
            header=header,
            add=add,
        )

    def get_template(self, name):
        """
        Get template with specific name

        Arguments:
            name (str): name of template
        Returns: (Template) template object with proper content loaded
        """
        template_text = ""
        with open(self.template_dir + name + ".yaml", "r") as temp_file:
            template_text = temp_file.read()
        return Template(template_text)

    def write_template(self, temp_name, temp_vars, file_out=None):
        """
        Write template to give file (or return as string)

        Arguments:
            temp_name (str): name of template
            temp_vars (dict): values to substitute in template
            file_out (file): if not defined, yaml content returned, else yaml
                content written to the file (default None)
        Returns (str/None): if file_out not defined, yaml content returned
        Raises (YamlTemplateException): In case some value is missing
        """
        try:
            engine_template = self.get_template(temp_name)
            if file_out:
                file_out.write(engine_template.substitute(temp_vars))
            else:
                return engine_template.substitute(temp_vars)
        except KeyError as err:
            raise YamlTemplateException(
                "Value not found: {} - {}".format(temp_name, err)
            )

    def process_subtemplate(self, subtemplate, data, file_out=None, level=0):
        """
        Write subtemplate to give file (or return as string)

        Arguments:
            subtemplate (dict): definition of subtemplate from yaml_config
            data (dict): values to substitute in template
            file_out (file): if not defined, yaml content returned, else yaml
                content written to the file (default None)
        Returns (str/None): if file_out not defined, yaml content returned
        """
        result = ""
        if "header" in subtemplate:
            header = self.get_header(
                header=subtemplate["header"], empty=not data, level=level
            )
            if file_out:
                file_out.write(header)
            else:
                result += header
        if not data and "no_data" not in subtemplate:
            return result
        if not isinstance(data, list):
            data = [data]
        else:
            # is ansible array - have to add one more indent
            level += 1
        for item in data:
            if file_out:
                self.write_template(subtemplate["template"], item, file_out)
            else:
                result += self.write_template(subtemplate["template"], item)
            if "additional" in subtemplate:
                for key2 in subtemplate["additional"]:
                    if key2 in item:
                        result += self.process_subtemplate(
                            subtemplate["additional"][key2],
                            item[key2],
                            file_out,
                            level + 1,
                        )
        return result

    def write_engine(self, engine_vars, file_out):
        """
        Write whole yaml content for engine to given file

        Arguments:
            engine_vars (dict): data of engine to substitute in templates
            file_out (file): file to write to
        Returns: (tuple) True/False - result ok/nook, None/Str - error
        Raises: (YamlTemplateException) In case of some template error
        """
        try:
            macpool_temp = ""
            for macpool in engine_vars["mac_pools"]:
                macpool_temp += self.write_template("macpool", macpool)
                for macrange in macpool["ranges"]:
                    macpool_temp += self.write_template("row3", {"value": macrange})
            engine_vars["macpools"] = macpool_temp
            self.write_template("engine", engine_vars, file_out)

            for key in yaml_config.SUBTEMPLATES_ORDER:
                template_def = yaml_config.SUBTEMPLATES[key]
                if template_def.get("no_data", False):
                    data = [{}]
                else:
                    try:
                        data = engine_vars[key]
                    except KeyError:
                        data = [{}]
                self.process_subtemplate(template_def, data, file_out)

            self.write_template(
                "engine_end", dict(self.config["extra_yaml_conf"]), file_out
            )

            return True, None

        except KeyError as err:
            return False, str(
                YamlTemplateException(
                    "engine variable '{}' missing".format(err.message)
                )
            )
        except YamlTemplateException as err:
            return False, str(err)


class YamlTemplateException(Exception):
    """
    Class for template exceptions
    """

    def __str__(self):
        return "[Template] {}".format(self.message)
