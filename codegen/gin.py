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
        handlerer_interface = 'type {interface_name} interface {{\n{interface_body}}}'
        handlerer_method_pattern = '{operationId}(c *gin.Context)'
        interface_body = ''
        for path in self.api_paths:
            handler = handlerer_method_pattern.format(operationId=path.operation_id)
            interface_body += '\t' + handler + '\n'

        return handlerer_interface.format(
            interface_name=self.interface_name,
            interface_body=interface_body
        ) + '\n\n'

    def gen_server_wrapper_code(self):
        server_wrapper_struct = 'type ServerWrapper struct {{\n' \
                                '\tHandlers\t{interface_name}\n' \
                                '}}'

        wrapper_methods = ''
        wrapper_method_pattern = 'func (sw *ServerWrapper) {operationId}(c gin.Context)'
        for path in self.api_paths:
            handler = wrapper_method_pattern.format(operationId=path.operation_id)
            handler += ' {\n'
            handler += '\tsw.Handler.' + path.operation_id + '(c)' + '\n}\n\n'
            wrapper_methods += handler

        return server_wrapper_struct.format(interface_name=self.interface_name) + '\n\n' + wrapper_methods

    def gen_register_handlers_code(self):
        register_handlers_func = "func RegisterHandlers(router *gin.Engine, handlers {interface_name}) *gin.Engine {{\n{func_body}}}"
        register_handler_pattern = 'router.{method}("{path}", wrapper.{operationId})'

        func_body = '\t' + 'wrapper := ServerWrapper{\n' \
                           '\t\tHandlers:\thandlers\n' \
                           '\t}\n\n'
        for path in self.api_paths:
            register_handler = register_handler_pattern.format(
                method=path.method.upper(),
                path=path.name,
                operationId=path.operation_id
            )
            func_body += '\t' + register_handler + '\n'

        return register_handlers_func.format(
            interface_name=self.interface_name,
            func_body=func_body
        )
