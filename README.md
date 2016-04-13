# Snowplow AWS Lambda source

[ ![Build Status] [travis-image] ] [travis]
[ ![Release] [release-image] ] [releases]
[ ![License] [license-image] ] [license]

Snowplow AWS Lambda source is a tool to track [AWS Lamba event sources](http://docs.aws.amazon.com/lambda/latest/dg/intro-core-components.html#intro-core-components-event-sources) in [Snowplow](http://snowplowanalytics.com/).

## Currently supported sources

* S3 Bucket operations
   * Depending on how you configure the lambda, this can include when a file is created, and when a file is deleted in a single or multiple S3 buckets
   
## Deployment

For a detailed set-up guide, see [here] [setup]. 
   
## Developer quickstart

Snowplow AWS Lambda source is written in Java 8 and uses gradle as a build tool. To get started quickly - a Vagrant set-up is also provided.

### Using Vagrant

The below commands will set up a Vagrant box provisioning Java 8 and gradle.

```{bash}
git clone git@github.com:snowplow/snowplow-aws-lambda-source.git
cd ./snowplow-aws-lambda-source
vagrant up && vagrant ssh
cd /vagrant
./gradlew test
```

### Using the gradle wrapper

```{bash}
git clone git@github.com:snowplow/snowplow-aws-lambda-source.git
cd ./snowplow-aws-lambda-source
./gradlew test
```

## Find out more

| Technical Docs                  | Setup Guide               | Roadmap                 | Contributing                      |
|---------------------------------|---------------------------|-------------------------|-----------------------------------|
| ![i1] [techdocs-image]          | ![i2] [setup-image]       | ![i3] [roadmap-image]   | ![i4] [contributing-image]        |
| **[Technical Docs] [techdocs]** | **[Setup Guide] [setup]** | **[Roadmap] [roadmap]** | **[Contributing] [contributing]** |

### Copyright and license

Snowplow is copyright 2016 Snowplow Analytics Ltd.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this software except in compliance with the License.

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

[travis-image]: https://travis-ci.org/snowplow/snowplow-aws-lambda-source.png?branch=master
[travis]: http://travis-ci.org/snowplow/snowplow-aws-lambda-source

[license-image]: http://img.shields.io/badge/license-Apache--2-blue.svg?style=flat
[license]: http://www.apache.org/licenses/LICENSE-2.0

[release-image]: https://img.shields.io/badge/release-0.1.0-orange.svg?style=flat
[releases]: https://github.com/snowplow/snowplow/releases

[techdocs]:     https://github.com/snowplow/snowplow/wiki/AWS-Lambda-source
[setup]:        https://github.com/snowplow/snowplow/wiki/AWS-Lambda-source-setup
[roadmap]:      https://github.com/snowplow/snowplow/wiki/AWS-Lambda-source-roadmap
[contributing]: https://github.com/snowplow/snowplow/wiki/AWS-Lambda-source-contributing

[techdocs-image]: https://d3i6fms1cm1j0i.cloudfront.net/github/images/techdocs.png
[setup-image]: https://d3i6fms1cm1j0i.cloudfront.net/github/images/setup.png
[roadmap-image]: https://d3i6fms1cm1j0i.cloudfront.net/github/images/roadmap.png
[contributing-image]: https://d3i6fms1cm1j0i.cloudfront.net/github/images/contributing.png
