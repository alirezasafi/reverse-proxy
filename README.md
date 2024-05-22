
# Reverse Proxy

Reverse Proxy is a traffic management tool designed to efficiently control the flow of traffic and API calls between services using a configuration-driven approach. This project, built on NGINX, simplifies the integration and management of service communications, making it ideal for environments where performance and reliability are critical. 

It supports:
- **URI Matching**: This feature offers flexible URI matching options to optimize request routing based on specific needs:
    - Prefix Matching: Routes or blocks requests where the URI starts with a specified prefix. This is less strict and can match multiple URIs under a given path prefix:
        ```yaml
        - name: api-server
          match:
              uri:
                prefix: /api/
          route:
            - destination:
                host: api-service
                port: 8000
        ```
    - Regex Matching: Uses regular expressions for matching URIs, providing a powerful tool for handling complex matching criteria:
        ```yaml
        - name: user-api
          match:
            uri:
              regex: "^/user/\d+$"
        ```
    - Exact Matching: Ensures that only URIs that exactly match the specified string are routed or blocked, suitable for targeting specific resources:
        ```yaml
        - name: exact-uri
          match:
            uri:
              exact: /exact-path/
        ```

- **Request Routing**: Directs incoming requests to the correct backend service based on URL. This feature also includes the ability to redirect requests and return direct responses:
    - Basic Routing: Routes requests to different backend services based on the request path:
        ```yaml
        - name: alertmanager
            match:
                uri:
                  prefix: /alert/
            route:
            - destination:
                host: 0.0.0.0
                port: 9093
            - destination:
                host: 0.0.0.0
                port: 9094
        ```
    - Redirecting Requests: Redirect requests to another URI when specific conditions are met, such as an outdated or moved resource:
        ```yaml
        - name: redirect-old-uri
          match:
            uri:
              regex: ^/old-uri/(.*)
          redirect:
            uri: /new-uri/
            redirectCode: 301
        ```
    - Direct Responses: Return a direct response from the proxy without contacting a backend service, useful for maintenance messages or static error responses:
        ```yaml
        - name: direct-response
          match:
            uri:
              prefix: /maintenance/
          directResponse:
            httpStatus: 503
            body: 
              string: "We are currently undergoing maintenance, please check back later."
        ```
- **Request Blocking**:  block specific URIs and manage IP-based access controls effectively:
    - URI Blocking: You can configure the service to block specific URIs by matching keywords or patterns. For example, blocking access to any URI containing "admin" can be configured as follows:
        ```yaml
        - name: admin
          match:
            uri:
              prefix: /admin/
            block:
              returnCode: 403
        ```
    - IP Address Control: The service supports allowing or denying access based on specific IP addresses. This can be set to allow only certain IPs to access a service or deny specific IPs:
        ```yaml
        - name: admin
          match:
            uri:
              prefix: /admin/
            block:
              allow:
                - "192.168.1.1"
              deny:
                - "192.168.1.100"
        ```
- **Traffic Shifting**: Facilitates canary releases and A/B testing by gradually diverting a percentage of traffic from one service version to another. A destination will receive weight/(sum of all weight of route):
  ```yaml
  route:
    - destination:
        host: 0.0.0.0
        port: 8000
      weight: 90 # for new version
    - destination:
        host: 0.0.0.0
        port: 8001
      weight: 10 # for old version
  ```
- **TLS and Secure Connection**: enables secure communication over the HTTPS protocol by leveraging TLS (Transport Layer Security) to encrypt and secure data in transit. also provide automatic redirects HTTP traffic to HTTPS to ensure secure connection.
    ```yaml
    - port:
        number: 443
        protocol: HTTPS
        hosts:
          - "example.com"
      tls:
        httpsRedirect: true
        certificate_file: /patch/to/example.crt
        key_file: /path/to/example.key
    ```

## Configuration Schema
For detailed information about configuring our service, see the [Configuration Schema](docs/configuration.md).