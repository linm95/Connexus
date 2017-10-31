package com.example.warbler.connexus;

import android.content.Intent;
import android.os.AsyncTask;
import android.support.v4.app.NavUtils;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.AdapterView;
import android.widget.GridView;
import android.widget.Toast;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

public class NearbyActivity extends AppCompatActivity {

    private class Photo {
        String url;
        String distance;
        String parent;
    }

    String[] parents;

    // create an async photo metadata fetcher
    private class Fetcher extends AsyncTask<String, Void, Photo[]> {
        @Override
        protected Photo[] doInBackground(String... urls) {
            OkHttpClient client = new OkHttpClient();
            Request request = new Request.Builder().url(urls[0]).build();

            try {
                Response response = client.newCall(request).execute();
                GsonBuilder builder = new GsonBuilder();
                Gson gson = builder.create();
                return gson.fromJson(response.body().string(), Photo[].class);
            } catch (java.io.IOException e) {
                System.err.println("- Error: IO Exception while getting all photos");
                System.err.println("- Error: " + e.toString());
                return null;
            }
        }

        @Override
        protected void onPostExecute(Photo[] result) {
            String[] urls = new String[result.length];
            String[] titles = new String[result.length];
            parents = new String[result.length];
            for (int i = 0; i < result.length; i++) {
                urls[i] = result[i].url;
                titles[i] = result[i].distance;
                parents[i] = result[i].parent;
            }
            ImageAdapter imageAdapter = new ImageAdapter(NearbyActivity.this);
            imageAdapter.setUrlsAndTexts(urls, titles);
            GridView gridview = (GridView) findViewById(R.id.nearbyBody);
            gridview.setAdapter(imageAdapter);
            pageNo++;
        }
    };

    Integer pageNo;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_nearby);
        Intent i= new Intent(this, LocationHelper.class);
        this.startService(i);

        // start from page 0
        pageNo = 0;

        //Double latitude = GPSHelper.getCurrentLatitude();
        //Double longitude = GPSHelper.getCurrentLongitude();
        Double latitude = LocationHelper.getLatitude();
        Double longitude = LocationHelper.getLongitude();


        // execute async task
        try {
            Fetcher fetcher = new Fetcher();
            fetcher.execute(getString(R.string.rootURL) + getString(R.string.nearbyURL)
                    + "?lat=" + URLEncoder.encode(latitude.toString(), "UTF-8")
                    + "&lng=" + URLEncoder.encode(longitude.toString(), "UTF-8")
                    + "&page=" + URLEncoder.encode(pageNo.toString(), "UTF-8"));
        } catch (UnsupportedEncodingException e) {
            System.err.println("- Error: Unsupported Encoding");
            System.err.println("- Error: " + e.toString());
        }

        // onclick
        GridView gridview = (GridView) findViewById(R.id.nearbyBody);
        gridview.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            public void onItemClick(AdapterView<?> parent, View v, int position, long id) {
                Intent intent = new Intent(NearbyActivity.this, SingleStreamActivity.class);
                intent.putExtra(AllStreamActivity.STREAM_SELECTED, parents[position]);
                startActivity(intent);
            }
        });
    }

    public void backToAllStream(View view) {
        Intent upIntent = NavUtils.getParentActivityIntent(this);
        NavUtils.navigateUpTo(this, upIntent);
    }

    public void getMorePictures(View view) {
        // get location
        Double latitude = GPSHelper.getCurrentLatitude();
        Double longitude = GPSHelper.getCurrentLongitude();

        // execute async task
        try {
            Fetcher fetcher = new Fetcher();
            fetcher.execute(getString(R.string.rootURL) + getString(R.string.nearbyURL)
                    + "?lat=" + URLEncoder.encode(latitude.toString(), "UTF-8")
                    + "&lng=" + URLEncoder.encode(longitude.toString(), "UTF-8")
                    + "&page=" + pageNo.toString());
        } catch (UnsupportedEncodingException e) {
            System.err.println("- Error: Unsupported Encoding");
            System.err.println("- Error: " + e.toString());
        }
    }
}
