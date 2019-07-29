# Base Nodejs Application
This nodejs webserver was generated with express-generator npm package
(http://expressjs.com/en/starter/generator.html)

It has base functionality such as:
* serve static files
* render html page with ejs templating engine

## Build docker image from source (linux)
To build docker image from source, use this script:
(docker needs to be installed)
```bash
./docker_build.sh tag
```
Replace tag with the tagname you want to use for this version.
For example:
```bash
./docker_build.sh v1.0
```
