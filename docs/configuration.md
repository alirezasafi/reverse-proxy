

# Configuration Schema
| Name  | Type       | Description                                                                                                                                                                         |
|-------|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| name | `string` | The name of nginx configuration file.
| servers | [`Servers`](#servers) | List of server specification.

### Servers
A list of server specifications.

| Name  | Type       | Description                                                                                                                                                                         |
|-------|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| port | [`Port`](#port) | The Port on which the proxy should listen for incoming connections.
| hosts | `string[]` | The destination hosts to which traffic is being sent. Could be a DNS name with wildcard prefix or an IP address. Depending on the platform, short-names can also be used instead of a FQDN (i.e. has no dots in the name). In such a scenario, the FQDN of the host would be derived based on the underlying platform. |
| http  | [`HTTP[]`](#http)   | An ordered list of route rules for HTTP traffic. HTTP routes will be applied to platform service ports using HTTP/HTTP2 protocols, gateway ports with protocol HTTP/HTTP2/TLS-terminated-HTTPS and service entry ports using HTTP/HTTP2 protocols. The first rule matching an incoming request is used. |
| tls | [`ServerTLS`](#servertls) | Set of TLS related options that govern the server’s behavior. Use these options to control if all http requests should be redirected to https, and the TLS modes to use.


### Port

| Name       | Type          | Description                                                                                                                                                                                                                                                                                    |
|------------|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| number | `integer` | A valid non-negative integer port number.
| protocol | `string` | The protocol exposed on the port. MUST BE one of HTTP\|HTTPS\|HTTP2\|TCP\|TLS. TLS can be either used to terminate non-HTTP based connections on a specific port or to route traffic based on SNI header to the destination without terminating the TLS connection.

### HTTP

| Name       | Type          | Description                                                                                                                                                                                                                                                                                    |
|------------|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| name | `string` | The name assigned to the http.
| match      | [`HTTPMatchRequest[]`](#httpmatchrequest)    | Match conditions to be satisfied for the rule to be activated. The rule is matched if any one of the match blocks succeed.                                                                                                                                                                                                                                               |
| route      | [`HTTPRoute[]`](#httproute)       | The forwarding target can be one of several versions of a service. Weights associated with the service version determine the proportion of traffic it receives.                                                                                                                                                                                                                                                  |
| redirect   | [`HTTPRedirect`](#httpredirect)    | If traffic passthrough option is specified in the rule, route/redirect will be ignored. The redirect primitive can be used to send a HTTP 301 redirect to a different URI or Authority.                                                                                                                                                                                                                                     |
| *fault      | [`HTTPFaultInjection`](#httpfaultinjection)       | Fault injection policy to apply on HTTP traffic at the client side.                                                                                                                                                                                                                                             |
| directResponse | [`HTTPDirectResponse`](#httpdirectresponse) | Direct Response is used to specify a fixed response that should be sent to clients. It can be set only when Route and Redirect are empty.|
| block | [`HTTPBlock`](#httpblock) | The block primitive can be used to deny or allow access from all users or specific IP addresses.|
| *timeout | `Duration` | Timeout for HTTP requests, default is disabled.
| *rewrite | [`HTTPRewrite`](#httprewrite) | Rewrite HTTP URIs and Authority headers. Rewrite cannot be used with Redirect primitive. Rewrite will be performed before forwarding.
| *mirrors | [`HTTPMirror`](#httpmirror) | Specifies the destinations to mirror HTTP traffic in addition to the original destination. Mirrored traffic is on a best effort basis where the sidecar/gateway will not wait for the mirrored destinations to respond before returning the response from the original destination. Statistics will be generated for the mirrored destination.
| *headers | [`Header`](#) | Header manipulation rules.
### ServerTLS
| Name       | Type          | Description                                                                                                                                                                                                                                                                                    |
|------------|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| httpsRedirect | `bool` | If set to true, the load balancer will send a 301 redirect for all http connections, asking the clients to use HTTPS.
| certificate_file | `string` | The path to the file holding the server-side TLS certificate to use.
| key_file | `string` | The path to the file holding the server’s private key.
### HTTPMatchRequest
| Name       | Type          | Description                                                                                                                                                                                                                                                                                    |
|------------|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| uri | [`StringMatch`](#stringmatch) | URI to match values are case-sensitive.
| *proxyRedirect | `bool` | This directive in Nginx is used to rewrite the location and refresh headers in the HTTP response from a proxied server, adjusting the URL in redirects to be correctly interpreted by the client.

### HTTPRoute
| Name       | Type          | Description                                                                                                                                                                                                                                                                                    |
|------------|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| destination | [`Destination`](#destination) | Destination uniquely identifies the instances of a service to which the request/connection should be forwarded to.
| weight | `integer` | Weight specifies the relative proportion of traffic to be forwarded to the destination. A destination will receive weight/(sum of all weights) requests. If there is only one destination in a rule, it will receive all traffic. Otherwise, if weight is 0, the destination will not receive any traffic.


### HTTPRedirect
| Name       | Type          | Description                                                                                                                                                                                                                                                                                    |
|------------|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| uri | `string` | On a redirect, overwrite the Path portion of the URL with this value. Note that the entire path will be replaced, irrespective of the request URI being matched as an exact path or prefix.
| redirectCode | `integer` | On a redirect, Specifies the HTTP status code to use in the redirect response. The default response code is MOVED_PERMANENTLY (301).

### HTTPFaultInjection

| Name       | Type          | Description                                                                                                                                                                                                                                                                                    |
|------------|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| *delay | [`Delay`](#delay) | Delay requests before forwarding, emulating various failures such as network issues, overloaded upstream service, etc.
| *abort | [`Abort`](#abort) | Abort Http request attempts and return error codes back to downstream service, giving the impression that the upstream service is faulty.


### HTTPDirectResponse
| Name       | Type          | Description                                                                                                                                                                                                                                                                                    |
|------------|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| status | `integer` | Specifies the HTTP response status to be returned.
| body | [`HTTPBody`](#httpbody) | Specifies the content of the response body. If this setting is omitted, no body is included in the generated response.

### HTTPBlock
| Name       | Type          | Description                                                                                                                                                                                                                                                                                    |
|------------|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| returnCode | `integer` | Specified the HTTP response status to be returned.
| allow | `string[]` | Allow access to uri for list of ip address.
| deny | `string[]` | Deny access to uri for list of ip address.

### HTTPRewrite
| Name       | Type          | Description                                                                                                                                                                                                                                                                                    |
|------------|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| *uri | `string` | rewrite the path (or the prefix) portion of the URI with this value. If the original URI was matched based on prefix, the value provided in this field will replace the corresponding matched prefix.

### HTTPMirror
| Name       | Type          | Description                                                                                                                                                                                                                                                                                    |
|------------|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| *destination | [`Destination`](#destination) | Destination specifies the target of the mirror operation.
| *percentage | `double` | Percentage of the traffic to be mirrored by the destination field. If this field is absent, all the traffic (100%) will be mirrored. Max value is 100.

### Header
| Name       | Type          | Description                                                                                                                                                                                                                                                                                    |
|------------|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| *request | [`HeaderOperation`](#) | Header manipulation rules to apply before forwarding a request to the destination service.
| *response | [`HeaderOperation`](#) | Header manipulation rules to apply before returning a response to the caller

### Destination
| Name       | Type          | Description                                                                                                                                                                                                                                                                                    |
|------------|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| host | `string` | Upstream service that traffic is being sent. Could be a DNS name with wildcard prefix or an IP address.
| port | `integer` | Upstream service port number.

#### Delay
| Name       | Type          | Description                                                                                                                                                                                                                                                                                    |
|------------|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| *fixedDelay | `duration` | Add a fixed delay before forwarding the request. Format: 1h/1m/1s/1ms. MUST be >=1ms. |
| *percentage | `double` | Percentage of requests on which the delay will be injected. If left unspecified, no request will be delayed. [0.0, 100.0]

#### Abort
| Name       | Type          | Description                                                                                                                                                                                                                                                                                    |
|------------|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| *httpStatus | `integer` | HTTP status code to use to abort the Http request. |
| *percentage | `double` | Percentage of requests to be aborted with the error code provided. If not specified, no request will be aborted. [0.0, 100.0]

#### HeaderOperation
| Name       | Type          | Description                                                                                                                                                                                                                                                                                    |
|------------|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| *set | `map<string, string>` | Overwrite the headers specified by key with the given values
| *add | `map<string, string>` | Append the given values to the headers specified by keys (will create a comma-separated list of values)
| *remove | `string[]` | Remove the specified headers 

#### HTTPBody

| Name       | Type          | Description                                                                                                                                                                                                                                                                                    |
|------------|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| string | `string` (oneof) | response body as a string |
| bytes | `bytes` (oneof) | response body as base64 encoded bytes.
#### StringMatch

| Name       | Type          | Description                                                                                                                                                                                                                                                                                    |
|------------|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| exact | `string` (oneof) | exact string match. |
| prefix | `string` (oneof) | prefix-based match. |
| regex | `string` (oneof) | regex-based match.