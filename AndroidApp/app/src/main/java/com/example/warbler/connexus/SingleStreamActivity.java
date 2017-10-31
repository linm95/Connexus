package com.example.warbler.connexus;

import android.content.Intent;
import android.os.AsyncTask;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.GridView;
import android.widget.ImageView;
import android.widget.TextView;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

import static com.example.warbler.connexus.AllStreamActivity.STREAM_SELECTED;

public class SingleStreamActivity extends AppCompatActivity {

    private class Photo {
        String url;
        String title;
    }

    Integer pageNo;

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
            for (int i = 0; i < result.length; i++) {
                urls[i] = result[i].url;
                titles[i] = result[i].title;
            }
            ImageAdapter imageAdapter = new ImageAdapter(SingleStreamActivity.this);
            imageAdapter.setUrlsAndTexts(urls, titles);
            GridView gridview = (GridView) findViewById(R.id.singleStreamBody);
            gridview.setAdapter(imageAdapter);
            pageNo++;
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_single_stream);

        // start with page 0
        pageNo = 0;

        // get which stream is selected
        Intent intent = getIntent();
        String streamTitle = intent.getStringExtra(STREAM_SELECTED);

        // add stream title
        TextView textView = (TextView) findViewById(R.id.singleStreamTitle);
        textView.setText(getString(R.string.singleStreamTitle) + " " + streamTitle);

        // execute async task
        try {
            Fetcher fetcher = new Fetcher();
            fetcher.execute(getString(R.string.rootURL) + getString(R.string.singleStreamURL) +
                    "?title=" + URLEncoder.encode(streamTitle, "UTF-8") +
                    "&page=" + pageNo.toString());
        } catch (UnsupportedEncodingException e) {
            System.err.println("- Error: Unsupported Encoding");
            System.err.println("- Error: " + e.toString());
        }


        // For upload an image btn
        Button uploadImgBtn = (Button)findViewById(R.id.singleStreamUpload);
        uploadImgBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent intent = getIntent();
                intent = new Intent(SingleStreamActivity.this, UploadActivity.class);
                intent.putExtra(getString(R.string.streamTitle), TitleHelper.getCurrentTitle());
                startActivity(intent);
            }
        });
    }

    public void getMorePictures(View view) {
        // get which stream is selected
        Intent intent = getIntent();
        String streamTitle = intent.getStringExtra(AllStreamActivity.STREAM_SELECTED);

        // execute async task
        try {
            Fetcher fetcher = new Fetcher();
            fetcher.execute(getString(R.string.rootURL) + getString(R.string.singleStreamURL) +
                    "?title=" + URLEncoder.encode(streamTitle, "UTF-8") +
                    "&page=" + pageNo.toString());
        } catch (UnsupportedEncodingException e) {
            System.err.println("- Error: Unsupported Encoding");
            System.err.println("- Error: " + e.toString());
        }
    }

    public void backToAllStreams(View view) {
        Intent intent = new Intent(this, AllStreamActivity.class);
        startActivity(intent);
    }
}
