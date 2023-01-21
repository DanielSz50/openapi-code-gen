from string import Template


def first_char_to_upper(str):
    if str is None:
        return None
    if len(str) == 0:
        return ''

    return str[0].upper() + str[1:len(str)]


class GinServer:

    def __init__(self, api_paths, api_schemas):
        self.api_paths = api_paths
        self.api_schemas = api_schemas
        self.interface_name = 'Handlerer'
        self.package_name = 'gen'
        self.import_time = False

    def gen_imports_code(self):
        imports = 'import (\n{import_body})'
        import_body = '\t"github.com/gin-gonic/gin"\n'
        if self.import_time:
            import_body += '\t"time"\n'

        return imports.format(import_body=import_body) + '\n\n'

    def gen_server_code(self):
        server_code = self.gen_interface_code()
        server_code += self.gen_server_wrapper_code()
        server_code += self.gen_register_handlers_code()
        server_code += self.gen_types_code()

        # gen imports code last so it knows what to include
        return self.gen_package_code() + self.gen_imports_code() + server_code

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

            if self.uri_param_exists(path.parameters):
                params += ', ' + first_char_to_upper(path.operation_id) + 'UriParams'

            if path.request_body_type is not None:
                params += ', ' + first_char_to_upper(path.request_body_type)

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
            wrappers += self.gen_wrapper_method_code(
                path.operation_id,
                path.parameters,
                path.request_body_type) + '\n\n'

        return 'type ServerWrapper struct {\n' \
               f'\tHandlers {self.interface_name}\n' \
               '}' + '\n\n' + wrappers

    def gen_register_handlers_code(self):
        register_handlers_func = "func RegisterHandlers(router *gin.Engine, handlers {interface_name}) {{\n" \
                                 "{func_body}}}"
        register_handler_pattern = 'router.{method}("{path}", wrapper.{operationId})'

        func_body = '\t' + 'wrapper := ServerWrapper{\n' \
                           '\t\tHandlers:\thandlers,\n' \
                           '\t}\n\n'
        for path in self.api_paths:
            path_name = path.name.replace('{', ':').replace('}', '')
            register_handler = register_handler_pattern.format(
                method=path.method.upper(),
                path=path_name,
                operationId=path.operation_id
            )
            func_body += '\t' + register_handler + '\n'

        return register_handlers_func.format(
            interface_name=self.interface_name,
            func_body=func_body
        ) + '\n\n'

    def gen_operation_parameters_types(self, operation_id, parameters):
        uri_param_template = Template('\t$go_name $pointer$property_type `uri:"$name" binding:"$required"`\n')
        query_param_template = Template('\t$go_name $pointer$property_type `form:"$name" binding:"$required"`\n')

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
                    pointer=pointer,
                    property_type=self.__openapi_type_to_go_type(parameter.p_type, parameter.p_format),
                    name=parameter.name,
                    required=required
                )

            if parameter.parameter_in == 'query':
                query_params += query_param_template.substitute(
                    go_name=first_char_to_upper(parameter.name),
                    pointer=pointer,
                    property_type=self.__openapi_type_to_go_type(parameter.p_type, parameter.p_format),
                    name=parameter.name,
                    required=required
                )

        params_struct_template = Template(
            'type $type_name struct {\n'
            '$params'
            '}')

        params_code = ''
        if self.uri_param_exists(parameters):
            params_code += params_struct_template.substitute(
                type_name=first_char_to_upper(operation_id) + 'UriParams',
                params=uri_params
            ) + '\n\n'

        if self.query_param_exists(parameters):
            params_code += params_struct_template.substitute(
                type_name=first_char_to_upper(operation_id) + 'QueryParams',
                params=query_params
            ) + '\n\n'

        return params_code

    def uri_param_exists(self, parameters):
        if parameters is None:
            return False

        for parameter in parameters:
            if parameter.parameter_in == 'path':
                return True

        return False

    def query_param_exists(self, parameters):
        if parameters is None:
            return False

        for parameter in parameters:
            if parameter.parameter_in == 'query':
                return True

        return False

    def gen_wrapper_method_code(self, operation_id, parameters, req_body_type):
        bind_query_params = f'\tvar queryParams {first_char_to_upper(operation_id)}QueryParams\n' \
                            '\tif err := c.ShouldBindQuery(&queryParams); err != nil {\n' \
                            '\t\tc.JSON(400, gin.H{"msg": err})\n' \
                            '\t\treturn\n' \
                            '\t}\n\n'

        bind_uri_params = f'\tvar uriParams {first_char_to_upper(operation_id)}UriParams\n' \
                          '\tif err := c.ShouldBindUri(&uriParams); err != nil {\n' \
                          '\t\tc.JSON(400, gin.H{"msg": err})\n' \
                          '\t\treturn\n' \
                          '\t}\n\n'

        bind_req_body = f'\tvar reqBody {first_char_to_upper(req_body_type)}\n' \
                        f'\tif err := c.ShouldBindJSON(&reqBody); err != nil {{\n' \
                        '\t\tc.JSON(400, gin.H{"msg": err})\n' \
                        '\t\treturn\n' \
                        '\t}\n\n'

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

        if req_body_type is not None:
            params += ', reqBody'
            method_body += bind_req_body

        invoke_handler = Template('\tsw.Handlers.$handler_name(c$params)')
        method_body += invoke_handler.substitute(
            handler_name=first_char_to_upper(operation_id),
            params=params
        )

        return types_code + wrapper_method_template.substitute(
            method_name=first_char_to_upper(operation_id),
            method_body=method_body
        )

    def gen_types_code(self):
        types = ''
        for schema in self.api_schemas:
            if schema.s_type == 'object':
                types += self.gen_struct_type_code(schema) + '\n\n'
            if schema.s_type == 'array':
                types += self.gen_array_type_code(schema) + '\n\n'

        return types

    def gen_array_type_code(self, schema):
        array_template = Template(
            'type $type_name []$items_type'
        )

        return array_template.substitute(
            type_name=first_char_to_upper(schema.name),
            items_type=self.__openapi_type_to_go_type(schema.items_type, None)
        )

    def gen_struct_type_code(self, schema):
        struct_template = Template(
            'type $type_name struct {\n'
            '$type_body'
            '}'
        )

        struct_property_template = Template(
            '\t$go_name $property_type `json:"$name$omit_empty"`\n'
        )

        type_code = ''
        for p in schema.properties:
            omit_empty = ',omitempty'
            if p.required:
                omit_empty = ''
            type_code += struct_property_template.substitute(
                go_name=first_char_to_upper(p.name),
                property_type=self.__openapi_type_to_go_type(p.p_type, p.p_format),
                name=p.name,
                omit_empty=omit_empty
            )

        return struct_template.substitute(
            type_name=first_char_to_upper(schema.name),
            type_body=type_code)

    def __openapi_type_to_go_type(self, openapi_type, openapi_format):
        if (openapi_type == 'integer') & (openapi_format == 'int32'):
            return 'int32'
        if (openapi_type == 'integer') & (openapi_format == 'int64'):
            return 'int64'
        if (openapi_type == 'integer') & (openapi_format is None):
            return 'int'
        if (openapi_type == 'number') & (openapi_format == 'float'):
            return 'float32'
        if (openapi_type == 'number') & (openapi_format == 'double'):
            return 'float64'
        if (openapi_type == 'number') & (openapi_format is None):
            return 'float32'
        if (openapi_type == 'string') & (openapi_format == 'byte'):
            return 'byte'
        if (openapi_type == 'string') & (openapi_format == 'binary'):
            return '[]byte'
        if (openapi_type == 'string') & (openapi_format == 'date'):
            self.import_time = True
            return 'time.Time'
        if (openapi_type == 'string') & (openapi_format == 'date-time'):
            self.import_time = True
            return 'time.Time'
        if (openapi_type == 'string') & (openapi_format == 'password'):
            return 'string'
        if (openapi_type == 'string') & (openapi_format is None):
            return 'string'
        if openapi_type == 'boolean':
            return 'bool'

        # openapi_type is custom one in this case, it needs to be exported then
        return first_char_to_upper(openapi_type)
