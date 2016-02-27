#!/usr/bin/env python
# -*- coding: utf-8 -*-


from flyingcloud import DockerBuildLayer


APP_NAMES = {
    'dev': 'development',
    'stg': 'staging',
    'prod': 'production',
}


#TODO: generalize this?
class CookBriteDockerLayer(DockerBuildLayer):
    USERNAME_VAR = 'COOKBRITE_DOCKER_REGISTRY_USERNAME'
    PASSWORD_VAR = 'COOKBRITE_DOCKER_REGISTRY_PASSWORD'
    Registry = 'quay.io'
    RegistryDockerVersion = "1.17"
    Organization = 'cookbrite'
    AppName = None
    SquashLayer = True


