from string import Template


def first_char_to_upper(str):
    return str[0].upper() + str[1:len(str)]


class GinServer:

    def __init__(self, api_paths):
        self.api_paths = api_paths
        self.interface_name = 'Handlerer'
        self.package_name = 'gen'

    @staticmethod
    def gen_imports_code():
        imports = 'import (\n{import_body})'
        import_body = '\t"github.com/gin-gonic/gin"\n'

        return imports.format(import_body=import_body) + '\n\n'

    def gen_package_code(self):
        return 'package ' + self.package_name + '\n\n'

    def gen_interface_code(self):
        handlerer_interface = 'type {interface_name} interface {{\n' \
                              '{interface_body}}}'
        handlerer_method_pattern = '{handler_name}(*gin.Context{params})'

        interface_body = ''
        for path in self.api_paths:
            params = ''

            if self.query_param_exists(path.parameters):
                params += ', ' + first_char_to_upper(path.operation_id) + 'QueryParams'

            if self.query_param_exists(path.parameters):
                params += ', ' + first_char_to_upper(path.operation_id) + 'UriParams'

            handler = handlerer_method_pattern.format(
                handler_name=first_char_to_upper(path.operation_id),
                params=params
            )

            interface_body += '\t' + handler + '\n'

        return handlerer_interface.format(
            interface_name=self.interface_name,
            interface_body=interface_body
        ) + '\n\n'

    def gen_server_wrapper_code(self):
        wrappers = ''
        for path in self.api_paths:
            wrappers += self.gen_wrapper_method_code(path.operation_id, path.parameters) + '\n\n'

        return 'type ServerWrapper struct {\n' \
               f'\tHandlers {self.interface_name}\n' \
               '}' + wrappers

    def gen_register_handlers_code(self):
        register_handlers_func = "func RegisterHandlers(router *gin.Engine, handlers {interface_name}) {{\n" \
                                 "{func_body}}}"
        register_handler_pattern = 'router.{method}("{path}", wrapper.{operationId})'

        func_body = '\t' + 'wrapper := ServerWrapper{\n' \
                           '\t\tHandlers:\thandlers,\n' \
                           '\t}\n\n'
        for path in self.api_paths:
            path_name = path.name.replace('{',':').replace('}','')
            register_handler = register_handler_pattern.format(
                method=path.method.upper(),
                path=path_name,
                operationId=path.operation_id
            )
            func_body += '\t' + register_handler + '\n'

        return register_handlers_func.format(
            interface_name=self.interface_name,
            func_body=func_body
        )

    def gen_operation_parameters_types(self, operation_id, parameters):
        uri_param_template = Template('\t$go_name string `uri:"$name" binding:"$required"`\n')
        query_param_template = Template('\t$go_name $pointer string `form:"$name" binding:"$required"`\n')

        uri_params = ''
        query_params = ''

        for parameter in parameters:
            required = ''
            pointer = '*'
            if parameter.required:
                required = 'required'
                pointer = ''

            if parameter.parameter_in == 'path':
                uri_params += uri_param_template.substitute(
                    go_name=first_char_to_upper(parameter.name),
                    name=parameter.name,
                    required=required
                )

            if parameter.parameter_in == 'query':
                query_params += query_param_template.substitute(
                    go_name=first_char_to_upper(parameter.name),
                    pointer=pointer,
                    name=parameter.name,
                    required=required
                )

        params_struct_template = Template('type $type_name struct {\n'
                                          '$params'
                                          '}')

        types_code = params_struct_template.substitute(
            type_name=first_char_to_upper(operation_id) + 'UriParams',
            params=uri_params
        ) + '\n\n'

        types_code += params_struct_template.substitute(
            type_name=first_char_to_upper(operation_id) + 'QueryParams',
            params=query_params
        )

        return types_code


    def uri_param_exists(self, parameters):
        if parameters is None:
            return 0

        exists = 0
        for parameter in parameters:
            if parameter.parameter_in == 'path':
                exists = 1

        return exists

    def query_param_exists(self, parameters):
        if parameters is None:
            return 0

        exists = 0
        for parameter in parameters:
            if parameter.parameter_in == 'query':
                exists = 1

        return exists

    def gen_wrapper_method_code(self, operation_id, parameters):
        bind_uri_params = f'\tvar uriParams {first_char_to_upper(operation_id)}UriParams\n' \
                        '\tif err := c.ShouldBindUri(&uriParams); err != nil {\n' \
                        '\t\tc.JSON(400, gin.H{"msg": err})\n' \
                        '\t\treturn\n' \
                        '\t}\n'

        bind_query_params = f'\tvar queryParams {first_char_to_upper(operation_id)}QueryParams\n' \
                            '\tif err := c.ShouldBindQuery(&queryParams); err != nil {\n' \
                            '\t\tc.JSON(400, gin.H{"msg": err})\n' \
                            '\t\treturn\n' \
                            '\t}\n'

        wrapper_method_template = Template('func (sw *ServerWrapper) $method_name(c *gin.Context) {\n'
                                           '$method_body\n'
                                           '}')
        types_code = ''
        if parameters is not None:
            types_code = self.gen_operation_parameters_types(operation_id, parameters)

        params = ''
        method_body = ''
        if self.query_param_exists(parameters):
            params += ', queryParams'
            method_body += bind_query_params

        if self.uri_param_exists(parameters):
            params += ', uriParams'
            method_body += bind_uri_params

        invoke_handler = Template('\tsw.Handlers.$handler_name(c$params)')
        method_body += invoke_handler.substitute(
            handler_name=first_char_to_upper(operation_id),
            params=params
        )

        return types_code + '\n\n' + wrapper_method_template.substitute(
            method_name=first_char_to_upper(operation_id),
            method_body=method_body
        )
