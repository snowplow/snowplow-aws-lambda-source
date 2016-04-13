/*
 * Copyright (c) 2016 Snowplow Analytics Ltd. All rights reserved.
 *
 * This program is licensed to you under the Apache License Version 2.0, and
 * you may not use this file except in compliance with the Apache License
 * Version 2.0.  You may obtain a copy of the Apache License Version 2.0 at
 * http://www.apache.org/licenses/LICENSE-2.0.
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the Apache License Version 2.0 is distributed on an "AS
 * IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
 * implied.  See the Apache License Version 2.0 for the specific language
 * governing permissions and limitations there under.
 */
package com.snowplowanalytics.sources.awslambda;

import com.amazonaws.regions.Regions;
import com.amazonaws.services.lambda.AWSLambdaClient;
import com.amazonaws.services.lambda.model.GetFunctionConfigurationRequest;
import com.amazonaws.services.lambda.model.GetFunctionConfigurationResult;

public class LambdaUtils {

    private LambdaUtils() {}

    /**
     * Using the AWS SDK build a AWS Lambda client for the given region
     * @param region an AWS region name
     * @return an AWSLambdaClient for the given region
     */
    public static AWSLambdaClient getAwsLambdaClientForRegion(String region) {
        return new AWSLambdaClient().withRegion(Regions.fromName(region));
    }

    /**
     * Using the AWSLambdaClient given, extract the "description" field for the given lambda function
     * @param client an AWSLambdaClient to request information using
     * @param lambdaFunction the name of the lambda function to get the description for
     * @return the description of the lambda function, trimmed
     */
    public static String getLambdaDescription(AWSLambdaClient client, String lambdaFunction) {
        GetFunctionConfigurationRequest request = new GetFunctionConfigurationRequest().withFunctionName(lambdaFunction);
        GetFunctionConfigurationResult result = client.getFunctionConfiguration(request);
        return result.getDescription().trim();
    }

}
