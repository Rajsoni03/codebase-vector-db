import os

def set_proxy_environment_variables():
    """
    Set environment variables for proxy configuration.
    This is useful when running in environments that require proxy settings.
    """
    os.environ["HTTPS_PROXY"] = ""
    os.environ["HTTP_PROXY"] = ""
    os.environ["FTP_PROXY"] = ""
    os.environ["https_proxy"] = ""
    os.environ["http_proxy"] = ""
    os.environ["ftp_proxy"] = ""