from project.settings import IS_DEVELOPMENT, IS_TEST, IS_PRODUCTION


def environments(request):
    return {
        "is_development": IS_DEVELOPMENT,
        "is_test": IS_TEST,
        "is_production": IS_PRODUCTION,
    }
