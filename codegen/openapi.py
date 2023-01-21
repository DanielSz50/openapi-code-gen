from codegen.gin import GinServer


def get_type_name_from_ref(ref):
    tokens = ref.split("/")
    return tokens[len(tokens) - 1].replace("'", "")


class OpenApi:

    def __init__(self, spec_data):
        self.paths = self.__parse_paths(spec_data["paths"].items())
        self.schemas = self.__parse_schemas(spec_data["components"]["schemas"].items())

    def __parse_paths(self, path_items):
        paths = []
        for path, path_data in path_items:
            parameters = path_data.get("parameters")
            if path_data.get("get") is not None:
                paths.append(Path(path, 'get', parameters, path_data["get"]))
            if path_data.get("put") is not None:
                paths.append(Path(path, 'put', parameters, path_data["put"]))
            if path_data.get("post") is not None:
                paths.append(Path(path, 'post', parameters, path_data["post"]))
            if path_data.get("delete") is not None:
                paths.append(Path(path, 'delete', parameters, path_data["delete"]))
            if path_data.get("options") is not None:
                paths.append(Path(path, 'options', parameters, path_data["options"]))
            if path_data.get("head") is not None:
                paths.append(Path(path, 'head', parameters, path_data["head"]))
            if path_data.get("patch") is not None:
                paths.append(Path(path, 'patch', parameters, path_data["patch"]))
            if path_data.get("trace") is not None:
                paths.append(Path(path, 'trace', parameters, path_data["trace"]))

        return paths

    def __parse_schemas(self, schema_items):
        schemas = []
        for s_name, s in schema_items:
            schemas.append(Schema(s_name, s))

        return schemas

    def gen_gin_server_code(self):
        gin_server = GinServer(self.paths, self.schemas)
        return gin_server.gen_server_code()


class Path:

    def __init__(self, name, method, parameters, path_data):
        self.name = name
        self.method = method
        self.operation_id = path_data.get("operationId")
        self.parameters = self.__parse_parameters(path_data.get("parameters", parameters))
        self.request_body_type = self.__get_request_body_type(path_data.get("requestBody"))
        self.responses = path_data.get("responses")
        self.description = path_data.get("description")

    def __parse_parameters(self, parameters_data):
        if parameters_data is None:
            return None

        parameters = []
        for parameter_data in parameters_data:
            parameters.append(Parameter(parameter_data))

        return parameters

    def __get_request_body_type(self, request_body):
        if request_body is None:
            return None
        if request_body.get("content").get("application/json").get("schema").get("$ref") is None:
            return None

        return get_type_name_from_ref(request_body.get("content").get("application/json").get("schema").get("$ref"))

    def __str__(self):
        to_print = "name: " + str(self.name or '') + "\n"
        to_print += "method: " + str(self.method or '') + "\n"
        to_print += "operation_id: " + str(self.operation_id or '') + "\n"
        for parameter in self.parameters:
            to_print += "parameters: " + str(parameter or '') + "\n"
        to_print += "request_body_type: " + str(self.request_body_type or '')
        to_print += "responses: " + str(self.responses or '') + "\n"
        to_print += "description: " + str(self.description or '')

        return to_print


class Parameter:

    def __init__(self, parameter_data):
        self.name = parameter_data.get("name")
        self.parameter_in = parameter_data.get("in")
        self.required = parameter_data.get("required")
        self.p_type = parameter_data.get("schema").get("type")
        self.p_format = parameter_data.get("schema").get("format")

    def __str__(self):
        to_print = "name: " + str(self.name or '') + "\n"
        to_print += "parameter_in: " + str(self.parameter_in or '') + "\n"
        to_print += "required: " + str(self.required or '') + "\n"

        return to_print


class Schema:

    def __init__(self, s_name, s_data):
        self.name = s_name
        self.s_type = s_data.get("type")

        if self.s_type == 'object':
            self.required_properties = s_data.get("required")
            self.properties = self.__parse_properties(s_data.get("properties").items())

        if self.s_type == 'array':
            if s_data.get("items").get("$ref") is not None:
                self.items_type = get_type_name_from_ref(s_data.get("items").get("$ref"))
            else:
                self.items_type = s_data.get("items").get("type")

    def __parse_properties(self, properties_items):
        properties = []

        for p_name, p in properties_items:
            if p.get("type") == 'array':
                p_type = ''
                if p.get("items").get("$ref") is not None:
                    p_type = get_type_name_from_ref(p.get("items").get("$ref"))
                else:
                    p_type = p.get("items").get("type")

                properties.append(SchemaProperty(
                    p_name,
                    p_type,
                    None,
                    None
                ))

            is_required = False
            if self.required_properties is not None:
                is_required = self.__is_property_required(p_name)

            properties.append(SchemaProperty(
                p_name,
                p.get("type"),
                p.get("format", None),
                is_required
            ))

        return properties

    def __is_property_required(self, p_name):
        for required_name in self.required_properties:
            if required_name == p_name:
                return True

        return False


class SchemaProperty:

    def __init__(self, name, p_type, p_format, required):
        self.name = name
        self.p_type = p_type
        self.p_format = p_format
        self.required = required
