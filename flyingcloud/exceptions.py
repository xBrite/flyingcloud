class FlyingCloudError(Exception):
    """Base error"""


class EnvironmentVarError(FlyingCloudError):
    """Missing environment variable"""


class NotSudoError(FlyingCloudError):
    """Not running as root"""


class CommandError(FlyingCloudError):
    """Command failure"""


class ExecError(FlyingCloudError):
    """Failure to run a command in Docker container"""


class DockerResultError(FlyingCloudError):
    """Error in result from Docker Daemon"""

