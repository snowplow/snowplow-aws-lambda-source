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
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.events.S3Event;
import com.snowplowanalytics.snowplow.tracker.DevicePlatform;
import com.snowplowanalytics.snowplow.tracker.Tracker;
import com.snowplowanalytics.snowplow.tracker.emitter.BatchEmitter;
import com.snowplowanalytics.snowplow.tracker.emitter.Emitter;
import com.snowplowanalytics.snowplow.tracker.emitter.RequestCallback;
import com.snowplowanalytics.snowplow.tracker.events.Unstructured;
import com.snowplowanalytics.snowplow.tracker.http.HttpClientAdapter;
import com.snowplowanalytics.snowplow.tracker.http.OkHttpClientAdapter;
import com.snowplowanalytics.snowplow.tracker.payload.SelfDescribingJson;
import com.snowplowanalytics.snowplow.tracker.payload.TrackerPayload;
import com.squareup.okhttp.OkHttpClient;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

/**
 *
 */
public class Main {

    public static final String SCHEMA = "iglu:com.amazon.aws.lambda/s3_notification_event/jsonschema/1-0-0";
    public static final Object isFinishedSending = new Object();

    /**
     * Get a suitable HttpClient adapter for use with the Snowplow tracker
     * @param url Snowplow collector endpoint
     * @return a HttpClient that can transmit events to the provided Snowplow collector
     */
    public static HttpClientAdapter getClient(String url) {
        OkHttpClient client = new OkHttpClient();

        client.setConnectTimeout(5, TimeUnit.SECONDS);
        client.setReadTimeout(5, TimeUnit.SECONDS);
        client.setWriteTimeout(5, TimeUnit.SECONDS);

        return OkHttpClientAdapter.builder()
                .url(url)
                .httpClient(client)
                .build();
    }

    /**
     * This method sends a list of events to a collector using the specified HttpClientAdapter
     * and waits for this to finish
     * @param adapter a constructed httpclient pointing to a Snowplow collector
     * @param events a list of events to send
     * @param namespace any namespacing for the list of events
     */
    public void trackEvents(HttpClientAdapter adapter, List<SelfDescribingJson> events, String namespace, String appId) {

        final long expectedSuccesses = events.size();
        final AtomicInteger failureCount = new AtomicInteger();

        Emitter emitter = BatchEmitter.builder()
                .httpClientAdapter(adapter)
                .requestCallback(new RequestCallback() {
                    @Override
                    public void onSuccess(int successCount) {
                        if (successCount==expectedSuccesses)
                        {
                            synchronized (isFinishedSending)
                            {
                                isFinishedSending.notify();
                            }
                        }
                    }

                    @Override
                    public void onFailure(int successCount, List<TrackerPayload> failedEvents) {
                        failureCount.getAndAdd(failedEvents.size());
                        if (successCount+failedEvents.size()==expectedSuccesses)
                        {
                            synchronized (isFinishedSending) {
                                isFinishedSending.notify();
                            }
                        }
                    }
                })
                .bufferSize(events.size())
                .build();

        Tracker tracker = new Tracker.TrackerBuilder(emitter, namespace, appId)
                .base64(true)
                .platform(DevicePlatform.ServerSideApp)
                .build();

        for (SelfDescribingJson e : events) {
            tracker.track(Unstructured.builder().eventData(e).build());
        }

        try {
            synchronized (isFinishedSending) {  // AWS will kill remaining threads if main exits,
                isFinishedSending.wait();       // so we are turning the async emitter into a sync one
            }                                   // lambda's also have timeouts so if this wait is forever it'll still die
        } catch (InterruptedException e)
        {
            throw new IllegalStateException(e);
        }

        if (failureCount.get() > 0)
        {
            throw new RuntimeException("Failed to send " + failureCount + " events to collector!");
        }
    }

    /**
     * Converts an object with a schema into SelfDescribingJson
     * @param schema a self describing json schema
     * @param event an object that can be deserialized into json matching the given schema
     * @return a SelfDescribingJson representing the given object/schema
     */
    public static SelfDescribingJson toEvent(String schema, Object event) {
        return new SelfDescribingJson(schema, event);
    }

    /**
     * Determine the region of an ARN
     * @param arn an AWS ARN string
     * @return the region contained in the ARN
     */
    public static String getRegion(String arn) {

        if (arn==null||arn.trim().isEmpty())
            throw new IllegalArgumentException("Cannot extract region from empty ARN");

        String region;
        try {
            region = arn.split(":")[3];
        } catch (Exception e){
            throw new IllegalArgumentException("Couldn't get region from ARN '" + arn + "'", e);
        }

        return region;
    }

    /**
     * AWS Lambda entry point
     * @param s3event a S3 bucket event pushed by AWS
     * @param context a companion object from AWS Lambda with extra information
     */
    public void handleRequest(S3Event s3event, Context context) {

        List<SelfDescribingJson> events = s3event.getRecords()
                .stream()
                .map(x -> toEvent(SCHEMA, x))
                .collect(Collectors.toList());

        String region = getRegion(context.getInvokedFunctionArn());
        AWSLambdaClient awsLambdaClient = LambdaUtils.getAwsLambdaClientForRegion(region);
        Configuration c = new Configuration(LambdaUtils.getLambdaDescription(awsLambdaClient, context.getFunctionName()));

        try {
            c.getCollectorUrlObj();
        } catch (MalformedURLException e) {
            throw new IllegalStateException("Collector URL in lambda description is invalid - '" + c.getCollectorUrl() + "'", e);
        }

        trackEvents(getClient(c.getCollectorUrl()), events, "main", c.getAppId());
    }
}