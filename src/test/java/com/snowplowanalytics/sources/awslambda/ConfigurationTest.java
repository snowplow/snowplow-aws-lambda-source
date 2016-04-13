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

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import org.junit.Test;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.HashMap;
import java.util.Map;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;

public class ConfigurationTest {

    private String makeJson(String collectorUrl, String appId) {
        Map<String, String> conf = new HashMap<>();
        if (collectorUrl!=null)
            conf.put("collector_url", collectorUrl);
        if (appId!=null)
            conf.put("app_id", appId);

        Gson gson = new GsonBuilder().create();
        return gson.toJson(conf);
    }

    @Test
    public void testMakeJsonValid() {
        Gson gsonBuilder = new GsonBuilder().create();
        Map<String,String> res = gsonBuilder.fromJson(makeJson("hello", "world"), Map.class);

        assertEquals("hello", res.get("collector_url"));
        assertEquals("world", res.get("app_id"));

        res = gsonBuilder.fromJson(makeJson(null, null), Map.class);
        assertFalse(res.containsKey("collector_url"));
        assertFalse(res.containsKey("app_id"));
    }

    @Test
    public void testHappyPath() throws Exception {
        Configuration c = new Configuration(makeJson("collector_url", "app_id"));
        assertEquals("collector_url", c.getCollectorUrl());
        assertEquals("app_id", c.getAppId());
    }

    @Test(expected = IllegalArgumentException.class)
    public void testMalformedJson() throws Exception {
        Configuration c = new Configuration("{");
    }

    @Test(expected = IllegalArgumentException.class)
    public void testMissingAppId() throws Exception {
        new Configuration(makeJson("collector_url", null));
    }

    @Test(expected = IllegalArgumentException.class)
    public void testMissingCollectorUrl() throws Exception {
        new Configuration(makeJson(null, "app_id"));
    }

    @Test
    public void testGetUrlAsObj() throws Exception {
        Configuration c = new Configuration(makeJson("http://hello.world.co.uk", "abc"));
        assertEquals(new URL(c.getCollectorUrl()), c.getCollectorUrlObj());
    }

    @Test (expected = MalformedURLException.class)
    public void testGetUrlAsObjMalformed() throws Exception {
        new Configuration(makeJson("aaaaaaaa", "abc")).getCollectorUrlObj();
    }



}