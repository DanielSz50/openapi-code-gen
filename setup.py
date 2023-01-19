import yaml

from codegen.openapi import OpenApi


def read_openapi(path):
    with open(path, 'r') as file:
        try:
            open_api = yaml.load(file, Loader=yaml.SafeLoader)
        except yaml.YAMLError as err:
            print('error loading OpenAPI spec file: ', err)

    return open_api


if __name__ == '__main__':
    objects = read_openapi('openapi.yaml')
    openapi = OpenApi(objects)
    print(openapi.gen_gin_server_code())
