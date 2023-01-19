from codegen.gin import GinServer


class OpenApi:

    def __init__(self, spec_data):
        self.paths = []
        for path, path_data in spec_data["paths"].items():
            parameters = path_data.get("parameters")
            if path_data.get("get") is not None:
                self.paths.append(Path(path, 'get', parameters, path_data["get"]))
            if path_data.get("put") is not None:
                self.paths.append(Path(path, 'put', parameters, path_data["put"]))
            if path_data.get("post") is not None:
                self.paths.append(Path(path, 'post', parameters, path_data["post"]))
            if path_data.get("delete") is not None:
                self.paths.append(Path(path, 'delete', parameters, path_data["delete"]))
            if path_data.get("options") is not None:
                self.paths.append(Path(path, 'options', parameters, path_data["options"]))
            if path_data.get("head") is not None:
                self.paths.append(Path(path, 'head', parameters, path_data["head"]))
            if path_data.get("patch") is not None:
                self.paths.append(Path(path, 'patch', parameters, path_data["patch"]))
            if path_data.get("trace") is not None:
                self.paths.append(Path(path, 'trace', parameters, path_data["trace"]))

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
        self.parameters = path_data.get("parameters", parameters)
        self.request_body = path_data.get("requestBody")

    def __str__(self):
        to_print = "name: " + str(self.name or '') + "\n"
        to_print += "method: " + str(self.method or '') + "\n"
        to_print += "operation_id: " + str(self.operation_id or '') + "\n"
        to_print += "parameters: " + str(self.parameters or '') + "\n"
        to_print += "request_body: " + str(self.request_body or '')

        return to_print
