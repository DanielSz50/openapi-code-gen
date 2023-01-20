from codegen.gin import GinServer


class OpenApi:

    def __init__(self, spec_data):
        self.paths = self.__parse_paths(spec_data["paths"].items())

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

    def gen_gin_server_code(self):
        gin_server = GinServer(self.paths)

        server_code = gin_server.gen_package_code()
        server_code += gin_server.gen_imports_code()
        server_code += gin_server.gen_interface_code()
        server_code += gin_server.gen_server_wrapper_code()
        server_code += gin_server.gen_register_handlers_code()

        return server_code


class Path:

    def __init__(self, name, method, parameters, path_data):
        self.name = name
        self.method = method
        self.operation_id = path_data.get("operationId")
        self.parameters = self.__parse_parameters(path_data.get("parameters", parameters))
        self.request_body = path_data.get("requestBody")
        self.responses = path_data.get("responses")
        self.description = path_data.get("description")

    def __parse_parameters(self, parameters_data):
        if parameters_data is None:
            return None

        parameters = []
        for parameter_data in parameters_data:
            parameters.append(Parameter(parameter_data))

        return parameters

    def __str__(self):
        to_print = "name: " + str(self.name or '') + "\n"
        to_print += "method: " + str(self.method or '') + "\n"
        to_print += "operation_id: " + str(self.operation_id or '') + "\n"
        for parameter in self.parameters:
            to_print += "parameters: " + str(parameter or '') + "\n"
        to_print += "request_body: " + str(self.request_body or '')
        to_print += "responses: " + str(self.responses or '') + "\n"
        to_print += "description: " + str(self.description or '')

        return to_print


class Parameter:

    def __init__(self, parameter_data):
        self.name = parameter_data.get("name")
        self.parameter_in = parameter_data.get("in")
        self.required = parameter_data.get("required")

    def __str__(self):
        to_print = "name: " + str(self.name or '') + "\n"
        to_print += "parameter_in: " + str(self.parameter_in or '') + "\n"
        to_print += "required: " + str(self.required or '') + "\n"

        return to_print
