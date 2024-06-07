import sys
import re
import yaml
import argparse
import colorlog
from dataclasses import dataclass
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader
from dataclass_wizard import fromdict
from dataclass_wizard import JSONWizard
from dataclass_wizard.errors import ParseError, MissingFields
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal


handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
	'%(log_color)s%(levelname)s:%(name)s : %(message)s'))

logger = colorlog.getLogger('reverse_proxy')
logger.addHandler(handler)

SSL_PORT_NUMBER = 443
SSL_PROTOCOL = 'HTTPS'
HTTP_REDIRECT_CODE = 301
IPV4_PATTERN = re.compile(
    r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
    r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
    r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
    r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
)

@dataclass
class StringMatch:
    exact: Optional[str] = None
    prefix: Optional[str] = None
    regex: Optional[str] = None

    def validate(self):
        attributes = [self.exact, self.prefix, self.regex]
        non_none_attributes = [attr for attr in attributes if attr is not None]
        if len(non_none_attributes) != 1:
            raise ValueError("One of 'exact', 'prefix', or 'regex' must be specified.")


@dataclass
class MatchURI:
    uri: StringMatch


@dataclass
class HTTPBody:
    string: Optional[str] = None
    bytes: Optional[bytes] = None


@dataclass
class Abort:
    httpStatus: int
    percentage: float

    def validate(self):
        if type(self.httpStatus) is not int:
            raise ValueError(f"httpStatus should be int got: {self.httpStatus}")
        if not (0.0 <= self.percentage <= 100.0):
            raise ValueError("Percentage must be between 0.0 and 100.0")


@dataclass
class Delay:
    fixedDelay: str
    percentage: float

    def validate(self):
        if not re.match(r'^\d+[hmsms]$', self.fixedDelay):
            raise ValueError("fixedDelay must be in format 1h/1m/1s/1ms")
        if not (0.0 <= self.percentage <= 100.0):
            raise ValueError("Percentage must be between 0.0 and 100.0")


@dataclass
class HTTPFaultInjection:
    delay: Optional[Delay] = None
    abort: Optional[Abort] = None

    def validate(self):
        if self.delay and self.abort:
            raise ValueError(
                "A fault rule must have delay or abort or both!"
            )
        if self.delay:
            self.delay.validate()
        if self.abort:
            self.abort.validate()


@dataclass
class HTTPDirectResponse:
    httpStatus: int
    body: HTTPBody


@dataclass
class HTTPRedirect:
    uri: str
    redirectCode: Optional[int] = HTTP_REDIRECT_CODE

    def validate(self):
        if (self.redirectCode is not None and not self.redirectCode > 0):
            raise ValueError(
                f"Weight value isn't valid! must be a positive integer. got {self.redirectCode}"
            )

@dataclass
class Destination:
    host: str
    port: int


@dataclass
class HTTPRoute:
    destination: Destination
    weight: Optional[int] = None

    def validate(self):
        if (self.weight is not None and not self.weight > 0):
            raise ValueError(
                f"Weight value isn't valid! must be a positive integer. got {self.weight}"
            )

@dataclass
class HTTPBlock:
    returnCode: Optional[int] = None
    allow: Optional[List[str]] = None
    deny: Optional[List[str]] = None
    
    def validate(self):
        if self.returnCode is not None and not 100 < self.returnCode < 599:
            raise ValueError(
                f"HTTP block return code isn't valid! must be an integer between 100 and 599." 
                f" got {self.returnCode}"
            )
        if self.deny:
            for ip in self.deny:
                if not IPV4_PATTERN.match(ip):
                    raise ValueError(f"IP address {ip} isn't valid!")
        if self.allow:
            for ip in self.allow:
                if not IPV4_PATTERN.match(ip):
                    raise ValueError(f"IP address {ip} isn't valid!")
        if self.returnCode and (self.deny or self.allow):
            logger.warning(
                "The fields 'allow' and 'deny' aren't work properly when you use 'returnCode'!"
            )

@dataclass
class HTTP:
    name: str
    match: MatchURI
    route: Optional[List[HTTPRoute]] = None
    redirect: Optional[HTTPRedirect] = None
    fault: Optional[HTTPFaultInjection] = None
    directResponse: Optional[HTTPDirectResponse] = None
    block: Optional[HTTPBlock] = None

    def validate(self):
        if self.block:
            self.block.validate()
        if self.match:
            self.match.uri.validate()
        if self.fault:
            self.fault.validate()
        if self.route:
            for route in self.route:
                route.validate()
        if self.block and self.redirect:
            raise ValueError(
                "you can't use `block` and `redirect` configs simultaneously"
            )            
        if self.directResponse:
            if self.route or self.redirect:
                raise ValueError(
                    "directResponse can be set only when `route` and `redirect` are empty!"
                )

@dataclass
class ServerTLS:
    httpsRedirect: bool
    certificate_file: str
    key_file: str

    def validate(self, port_number):
        if port_number != SSL_PORT_NUMBER and self.httpsRedirect:
            raise ValueError(
                f"To enabling ssl protocol you should change the port number to {SSL_PORT_NUMBER}."
                f" got {port_number}"
            )


@dataclass
class Port(JSONWizard):
    number: int
    protocol: Literal["HTTP", "HTTPS", "HTTP2", "TCP", "TLS"]

    def validate(self):
        if not isinstance(self.number, int) or self.number < 0:
            raise ValueError(f"Port number must be a non-negative integer. got {self.number}")
        if (self.protocol == SSL_PROTOCOL and self.number != SSL_PORT_NUMBER) \
            or (self.number == SSL_PORT_NUMBER and self.protocol != SSL_PROTOCOL):
            raise ValueError(
                f"Port number and protocol isn't match for SSL."
                f" to enabling ssl you should use port '{SSL_PORT_NUMBER}' and protocol '{SSL_PROTOCOL}'"
            )


@dataclass
class Server:
    port: Port
    hosts: List[str]
    http: List[HTTP]
    tls: Optional[ServerTLS] = None
    
    def validate(self):
        self.port.validate()
        for http in self.http:
            http.validate()
        if self.tls:
            self.tls.validate(self.port.number)


@dataclass
class Config(JSONWizard):
    class _(JSONWizard.Meta):
        debug_enabled = True

    servers: List[Server]
    name: str

    def validate(self):
        for server in self.servers:
            server.validate()


def load_config(file_path: str) -> Config:
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
        try:
            config = fromdict(Config, data)
            config.validate()
            return config
        except ParseError as error:
            logger.error(
                f"Failure parsing field `{error.field_name}` in config `{error.class_name}`.\n"
                f"Expected a type `{error.ann_type}`, got `{error.obj_type}`\n"
                f"Value: `{error.obj}`"
            )   
            sys.exit(1)
        except ValueError as error:
            logger.error(error)
            sys.exit(1)
        except MissingFields as error:
            logger.error(
                f"Missing values for required config '{error.class_name}'\n"
                f"missing fields: {error.missing_fields}\n"
                f"captured config: {error.obj}"
            )
            sys.exit(1)


def render_nginx_config(config: Config, template_path: str) -> str:
    env = Environment(loader=FileSystemLoader(searchpath="."))
    template = env.get_template(template_path)
    return template.render(servers=config.servers)

def main():
    parser = argparse.ArgumentParser(description="Generate NGINX configuration from YAML config.")
    parser.add_argument("config", type=str, help="Path to the configuration YAML file.")
    parser.add_argument("template", type=str, help="Path to the nginx template file.")
    parser.add_argument("output", type=str, help="Output directory.")
    args = parser.parse_args()
    config = load_config(args.config)
    nginx_config = render_nginx_config(config, args.template)

    with open(f'{args.output}/{config.name}.conf', 'w') as file:
        file.write(nginx_config)

if __name__ == "__main__":
    main()
