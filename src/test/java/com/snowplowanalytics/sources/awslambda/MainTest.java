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

import com.snowplowanalytics.snowplow.tracker.http.HttpClientAdapter;
import com.snowplowanalytics.snowplow.tracker.payload.SelfDescribingJson;
import com.squareup.okhttp.OkHttpClient;
import org.junit.Assert;
import org.junit.Test;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.IntStream;
import static org.junit.Assert.assertEquals;
import static org.mockito.Mockito.*;

public class MainTest {

    @Test
    public void testGetRegion() throws Exception {
        String mockArn = "arn:aws:elasticbeanstalk:us-east-1:123456789012:environment/My App/MyEnvironment";
        Assert.assertEquals("us-east-1", Main.getRegion(mockArn));
    }

    @Test (expected = IllegalArgumentException.class)
    public void testGetRegionNull() {
        Main.getRegion(null);
    }

    @Test (expected = IllegalArgumentException.class)
    public void testGetRegionEmpty() {
        Main.getRegion("");
    }

    @Test (expected = IllegalArgumentException.class)
    public void testGetRegionShort() {
        Main.getRegion("1:2:3:"); // not enough ARN
    }

    @Test
    public void testGetAdapter() {
        HttpClientAdapter adapter = Main.getClient("http://snowplowanalytics.com");
        assertEquals("http://snowplowanalytics.com", adapter.getUrl());
        OkHttpClient client = (OkHttpClient)adapter.getHttpClient();
        assertEquals(5000, client.getReadTimeout());
        assertEquals(5000, client.getConnectTimeout());
        assertEquals(5000, client.getWriteTimeout());
    }

    @Test
    public void testTrackEvents() {
        HttpClientAdapter adapter = mock(HttpClientAdapter.class);
        when(adapter.post(any())).thenReturn(200);

        Map<String,String> testEventContent = new HashMap<>();
        testEventContent.put("hello", "world");

        List<SelfDescribingJson> testEvents = new ArrayList<>();
        IntStream.rangeClosed(1,100).forEach(i -> {
            testEvents.add(new SelfDescribingJson("iglu:com.acme/event/jsonschema/1-0-0", testEventContent));
        });

        Main m = new Main();
        m.trackEvents(adapter, testEvents, "main", "com.snowplowanalytics.test");

        verify(adapter).post(any());
    }

    @Test (expected = RuntimeException.class)
    public void testFailuresToTrack() {
            HttpClientAdapter adapter = mock(HttpClientAdapter.class);
            when(adapter.post(any())).thenReturn(503);

            Map<String,String> testEventContent = new HashMap<>();
            testEventContent.put("hello", "world");

            List<SelfDescribingJson> testEvents = new ArrayList<>();
            IntStream.rangeClosed(1,100).forEach(i -> {
                testEvents.add(new SelfDescribingJson("iglu:com.acme/event/jsonschema/1-0-0", testEventContent));
            });

            Main m = new Main();
            m.trackEvents(adapter, testEvents, "main", "com.snowplowanalytics.test");

            verify(adapter).post(any());
    }

    @Test
    public void testToEvent() {
        SelfDescribingJson s = new SelfDescribingJson("iglu:com.acme/event/jsonschema/1-0-0", new Object());
        assertEquals(s.toString(), Main.toEvent("iglu:com.acme/event/jsonschema/1-0-0", new Object()).toString());
    }

}