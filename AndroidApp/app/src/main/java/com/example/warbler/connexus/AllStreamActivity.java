package com.example.warbler.connexus;

import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.icu.util.ValueIterator;
import android.os.AsyncTask;
import android.os.UserHandle;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.GridView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import java.io.IOException;
import java.io.InputStream;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

public class AllStreamActivity extends AppCompatActivity {

    // A stream icon contains a cover and a title
    private class Stream {
        String cover_url;
        String title;
    }

    private enum StreamToShow {
        ALL,
        SUBSCRIBED
    }

    StreamToShow streamToShow = StreamToShow.ALL;

    // which stream touched
    public static final String STREAM_SELECTED = "com.example.allstreams.selected";

    // query
    public static final String QUERY = "com.example.allstreams.query";

    // create an async photo metadata fetcher
    private class Fetcher extends AsyncTask<String, Void, Stream[]> {
        @Override
        protected Stream[] doInBackground(String... urls) {
            OkHttpClient client = new OkHttpClient();
            Request request = new Request.Builder().url(urls[0]).build();

            try {
                Response response = client.newCall(request).execute();
                GsonBuilder builder = new GsonBuilder();
                Gson gson = builder.create();
                return gson.fromJson(response.body().string(), Stream[].class);
            } catch (java.io.IOException e) {
                System.err.println("- Error: IO Exception while getting all streams");
                System.err.println("- Error: " + e.toString());
                return null;
            }
        }

        @Override
        protected void onPostExecute(Stream[] result) {
            String[] urls = new String[result.length];
            String[] titles = new String[result.length];
            for (int i = 0; i < result.length; i++) {
                urls[i] = result[i].cover_url;
                titles[i] = result[i].title;
            }
            ImageAdapter imageAdapter = new ImageAdapter(AllStreamActivity.this);
            imageAdapter.setUrlsAndTexts(urls, titles);
            GridView gridview = (GridView) findViewById(R.id.allStreamBody);
            gridview.setAdapter(imageAdapter);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (UserHelper.isSignedIn()) {
            setContentView(R.layout.activity_all_stream);
        } else {
            setContentView(R.layout.activity_all_stream_unsigned);
        }
/*
        Intent i= new Intent(this, LocationHelper.class);
        this.startService(i);
*/
        Fetcher fetcher = new Fetcher();
        String url = getString(R.string.rootURL) + getString(R.string.allStreamURL);
        fetcher.execute(url);

        GridView gridview = (GridView) findViewById(R.id.allStreamBody);
        gridview.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            public void onItemClick(AdapterView<?> parent, View v, int position, long id) {
                LinearLayout cell = (LinearLayout) v;
                TextView caption = (TextView) cell.getChildAt(1);
                String streamTitle = caption.getText().toString();
                TitleHelper.setCurrentTitle(streamTitle);
                Intent intent = new Intent(AllStreamActivity.this, SingleStreamActivity.class);
                intent.putExtra(STREAM_SELECTED, streamTitle);
                startActivity(intent);
            }
        });
    }

    public void sendSearch(View view) {
        EditText editText = (EditText) findViewById(R.id.allStreamSchBar);
        String query = editText.getText().toString();
        Intent intent = new Intent(this, SearchActivity.class);
        intent.putExtra(QUERY, query);
        startActivity(intent);
    }

    public void toNearby(View view) {

        Intent intent = new Intent(this, NearbyActivity.class);
        startActivity(intent);
    }

    public void viewSubscribed(View view) {
        if (streamToShow == StreamToShow.ALL) {
            String userEmail = UserHelper.getCurrentUserEmail();
            Fetcher fetcher = new Fetcher();
            fetcher.execute(getString(R.string.rootURL) + getString(R.string.subscribedStreamURL)
                    + "?owner=" + userEmail);

            // change button text
            Button button = (Button) findViewById(R.id.allStreamSubBtn);
            button.setText(R.string.singelStreamBckBtnText);

            // switch flags
            streamToShow = StreamToShow.SUBSCRIBED;
        } else if (streamToShow == StreamToShow.SUBSCRIBED) {
            Fetcher fetcher = new Fetcher();
            fetcher.execute(getString(R.string.rootURL) + getString(R.string.allStreamURL));

            // change button text
            Button button = (Button) findViewById(R.id.allStreamSubBtn);
            button.setText(R.string.allStreamSubBtnText);

            // switch flags
            streamToShow = StreamToShow.ALL;
        }
    }
}
