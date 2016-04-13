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

import java.net.MalformedURLException;
import java.net.URL;
import java.util.HashMap;
import java.util.Map;

public class Configuration {

    private String collectorUrl = "";
    private String appId = "";


    /**
     * Inflate a configuration object from JSON
     * @param configuration a json encoded string expressing a collector_url and app_id
     */
    public Configuration(String configuration) {
        Gson gson = new GsonBuilder().create();
        Map<String,String> conf;

        try {
            conf = gson.fromJson(configuration, Map.class);
        } catch (Exception e) {
            throw new IllegalArgumentException("The config JSON in the lambda description ('" + configuration + "') could not be parsed", e);
        }

        if (!conf.containsKey("collector_url"))
            throw new IllegalArgumentException("The config JSON in the lambda description ('" + configuration + "') does not contain a collector_url field");

        if (!conf.containsKey("app_id"))
            throw new IllegalArgumentException("The config JSON in the lambda description ('" + configuration + "') does not contain an app_id field");

        this.collectorUrl = conf.get("collector_url");
        this.appId = conf.get("app_id");
    }

    /**
     * Get the collector_url specified in the configuration
     * @return the collector url exactly as is in the configuration
     */
    public String getCollectorUrl() {
        return collectorUrl;
    }

    public URL getCollectorUrlObj() throws MalformedURLException {
        return new URL(this.getCollectorUrl());
    }

    /**
     * Get the AppId exactly as specified in the configuration
     * @return AppId as specified in configuration
     */
    public String getAppId() {
        return appId;
    }


}
