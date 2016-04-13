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

import com.amazonaws.services.lambda.AWSLambdaClient;
import com.amazonaws.services.lambda.model.GetFunctionConfigurationRequest;
import com.amazonaws.services.lambda.model.GetFunctionConfigurationResult;
import org.junit.Test;
import static org.junit.Assert.*;
import static org.mockito.Mockito.*;

public class LambdaUtilsTest {

    @Test (expected = IllegalArgumentException.class)
    public void testGetLambdaClientBadRegion() {
        LambdaUtils.getAwsLambdaClientForRegion("banana");
    }

    @Test
    public void testGetLambdaClient() throws Exception {
        AWSLambdaClient c = LambdaUtils.getAwsLambdaClientForRegion("eu-west-1");
        assertNotNull(c);
    }

    @Test
    public void testGetLambdaDescription() throws Exception {
        AWSLambdaClient mockClient = mock(AWSLambdaClient.class);

        GetFunctionConfigurationResult result = new GetFunctionConfigurationResult()
                .withFunctionName("test")
                .withDescription("http://snowplowanalytics.com");

        GetFunctionConfigurationRequest expected = new GetFunctionConfigurationRequest().withFunctionName("test");

        when(mockClient.getFunctionConfiguration(expected)).thenReturn(result);

        String desc = LambdaUtils.getLambdaDescription(mockClient, "test");

        verify(mockClient).getFunctionConfiguration(expected);
        assertEquals("http://snowplowanalytics.com", desc);
    }

    @Test
    public void testGetLambdaDescriptionSpaces() throws Exception {
        AWSLambdaClient mockClient = mock(AWSLambdaClient.class);

        GetFunctionConfigurationResult result = new GetFunctionConfigurationResult()
                .withFunctionName("test")
                .withDescription("                http://snowplowanalytics.com                    ");

        GetFunctionConfigurationRequest expected = new GetFunctionConfigurationRequest().withFunctionName("test");

        when(mockClient.getFunctionConfiguration(expected)).thenReturn(result);

        String desc = LambdaUtils.getLambdaDescription(mockClient, "test");

        verify(mockClient).getFunctionConfiguration(expected);
        assertEquals("http://snowplowanalytics.com", desc);
    }

}