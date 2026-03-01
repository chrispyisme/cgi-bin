# The Pyuneer Development Roadmap #

1. STRUCTURE     - Basic directory layout & Apache config
2. REWRITE       - .htaccess routing all to our Python script
3. HTTP          - Request/Response objects (CGI mode)
4. ROUTING       - Basic router that can match routes and respond
5. ROUTING-MW    - Middleware support for router
6. MVC-APP       - Controllers, basic MVC structure
7. MVC-APP-VIEW  - Template engine integration
8. MVC-APP-MODEL - Database/models layer  
9. MVC-DI        - Dependency injection container integration
10. OUR-SERVER   - Replace Apache with our own TCP server

# Directory Layout #
text
pyuneer/
├── .htaccess                    # Apache rewrite rules
├── cgi-bin/
│   └── app.py                   # Main CGI entry point
├── public/
│   ├── css/
│   ├── js/
│   └── images/
├── src/
│   ├── __init__.py
│   ├── http/
│   │   ├── __init__.py
│   │   ├── request.py          # Request object
│   │   └── response.py         # Response object
│   └── router.py               # Basic router
└── README.md
