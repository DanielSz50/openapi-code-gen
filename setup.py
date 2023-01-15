import yaml


def read_openapi(path):
    with open(path, 'r') as file:
        try:
            openapi = yaml.load(file, Loader=yaml.SafeLoader)
        except yaml.YAMLError as err:
            print('error loading OpenAPI spec file: ', err)

    return openapi


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
        package = 'package gen\n'

        imports = 'import (\n' \
                  '\t"github.com/gin-gonic/gin"\n' \
                  ')\n'

        handlerer_interface = 'type Handlerer interface {\n'
        handler_pattern = '{operationId}(c *gin.Context)'
        register_handlers_func = "func RegisterHandlers(router *gin.Engine, handlerer Handlerer) *gin.Engine {\n"
        register_handler_pattern = 'router.{method}("{path}", handlerer.{operationId})'

        for path in self.paths:
            handler = handler_pattern.format(operationId=path.operation_id)
            handlerer_interface += '\t' + handler + '\n'

            register_handler = register_handler_pattern.format(
                method=path.method.upper(),
                path=path.name,
                operationId=path.operation_id
            )
            register_handlers_func += '\t' + register_handler + '\n'

        server_code = package + '\n' + imports + '\n' + handlerer_interface + '}\n\n' + register_handlers_func + '}\n'
        return server_code


if __name__ == '__main__':
    objects = read_openapi('openapi.yaml')
    openapi = OpenApi(objects)
    print(openapi.gen_gin_server_code())
