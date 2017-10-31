package com.example.warbler.connexus;

import android.app.SearchManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.media.Image;
import android.os.AsyncTask;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.support.v7.widget.RecyclerView;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.GridView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.SearchView;
import android.widget.TextView;
import android.widget.Toast;

import com.google.gson.Gson;

import org.w3c.dom.Text;

import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;

import okhttp3.FormBody;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class SearchActivity extends AppCompatActivity {
    //corresponding backend server for search
    private String searchUrl;

    private static final String defaultImageUrl = ""; //default image url if no url is offered
    private List<Stream> streamList = null; //streams got from the server
    private Context searchContext = this; //context of this searchActivity
    private String globalQuery = ""; //current query
    private int status = 0; //indicate the status of search
    private HashMap<String, Bitmap> imageMap = new HashMap<String, Bitmap>(); //HashMap to cache the content of the cover photo
    private int cellWidth = -1; //initialize the width of the grid point

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_search);

        searchUrl = getString(R.string.rootURL) + "/app-search";
        Button button = (Button)findViewById(R.id.seeMoreStreams);
        button.setVisibility(View.GONE);
        SearchView searchView = (SearchView) findViewById(R.id.searchView);
        searchView.setIconifiedByDefault(false);
        searchView.setSubmitButtonEnabled(true);
        searchView.setOnQueryTextListener(new SearchView.OnQueryTextListener(){
            @Override
            public boolean onQueryTextSubmit(String query){
                if(status == 0) {
                    globalQuery = query;
                    status = 1;
                    TextView info = (TextView) findViewById(R.id.info);
                    info.setText("Searching...\n");
                    new Search(query).execute("");
                }
                else
                    Toast.makeText(SearchActivity.this, "Please try later", Toast.LENGTH_SHORT).show();
                return true;
            }

            @Override
            public boolean onQueryTextChange(String newText) { return true;}
        });

        Intent intent = getIntent();
        String msg = intent.getStringExtra(AllStreamActivity.QUERY);
        if(msg.length() != 0){
            globalQuery = msg;
            new Search(msg).execute("");
        }
    }

    private class Search extends AsyncTask{
        //search in another thread
        String query;

        public Search(String query){
            super();
            this.query = query;
        }

        @Override
        protected Object doInBackground(Object... args){
            OkHttpClient client = new OkHttpClient();
            RequestBody body = new FormBody.Builder()
                    .add("query",query)
                    .build();
            Request request = new Request.Builder()
                    .url(searchUrl)
                    .post(body)
                    .build();
            try {
                Response response = client.newCall(request).execute();
                Gson gson = new Gson();
                Streams streams = gson.fromJson(response.body().string(), Streams.class);
                streamList = streams.streamList;
            } catch (IOException e) {
                Toast.makeText(SearchActivity.this, "network failed", Toast.LENGTH_SHORT).show();
                System.out.print("http request failure");
            }
            return null;
        }

        @Override
        protected void onPostExecute(Object result){
            TextView info = (TextView) findViewById(R.id.info);
            if(streamList.size() > 0) {
                info.setText(streamList.size() + " results for " + globalQuery + ",\n" +
                        "loading streams...");
            }
            else setInfo();
            setGridView(false);
            Button button = (Button) findViewById(R.id.seeMoreStreams);
            button.setVisibility(View.VISIBLE);
            button.setOnClickListener(new Button.OnClickListener(){
                public void onClick(View v){
                    setGridView(true);
                }
            });
        }
    }

    private class DownloadImage extends AsyncTask<Integer, Void, Bitmap>{
        //download the cover image accoring to the url
        private ImageView imageView;
        private TextView textView;
        private ImageAdapter imageAdapter;
        private int pos;
        private int max;
        private int cellWidth;

        public DownloadImage(int cellWidth, ImageView imageView, TextView textView,
                             int pos, int max, ImageAdapter imageAdapter){
            this.cellWidth = cellWidth;
            this.imageView = imageView;
            this.imageAdapter = imageAdapter;
            this.textView = textView;
            this.pos = pos;
            this.max = max;
        }

        @Override
        protected Bitmap doInBackground(Integer... positions){
            Integer position = positions[0];
            Stream stream = streamList.get(position);
            Bitmap image = null;
            String url = stream.url;
            if(url.length() == 0)
                url = defaultImageUrl;
            try{
                InputStream in = new java.net.URL(url).openStream();
                image = BitmapFactory.decodeStream(in);
                }catch(Exception e){
                    try{
                        InputStream in = new java.net.URL(defaultImageUrl).openStream();
                        image = BitmapFactory.decodeStream(in);
                    }catch(Exception e2){
                        Log.e("downloading image error", e2.getMessage());
                    }
                }
            return image;
        }

        @Override
        protected void onPostExecute(Bitmap result){
            imageView.setImageBitmap(result);
            imageView.setScaleType(ImageView.ScaleType.CENTER_CROP);
            imageView.setLayoutParams(new LinearLayout.LayoutParams(cellWidth, cellWidth));
            String title = streamList.get(pos).title;
            imageMap.put(title, result);
            textView.setText(title);
            imageAdapter.notifyDataSetChanged();
            if(pos == max - 1) {
                setInfo();
            }
        }
    }

    private class ImageAdapter extends BaseAdapter{
        //adapter to set the grid view
        private Context mContext;
        private int max;

        public ImageAdapter(Context c, int max){
            mContext = c;
            this.max = max;
        }

        public int getCount(){ return max; }

        public Object getItem(int position){ return null; }

        public long getItemId(int position){ return 0; }

        public View getView(int position, View convertView, ViewGroup parent){
            View grid;
            LayoutInflater inflater = (LayoutInflater) mContext.getSystemService(Context.LAYOUT_INFLATER_SERVICE);
            if(convertView == null){
                if(cellWidth == -1)
                    cellWidth = ((GridView) parent).getColumnWidth();

                grid = inflater.inflate(R.layout.grid_single, null);
                TextView textView = (TextView) grid.findViewById(R.id.grid_text);
                ImageView imageView = (ImageView) grid.findViewById(R.id.grid_image);
                String title = streamList.get(position).title;

                if(imageMap.containsKey(title)){
                    imageView.setImageBitmap(imageMap.get(title));
                    imageView.setScaleType(ImageView.ScaleType.CENTER_CROP);
                    imageView.setLayoutParams(new LinearLayout.LayoutParams(cellWidth, cellWidth));
                    textView.setText(title);
                    if(position == max - 1)
                        setInfo();
                }
                else {
                    new DownloadImage(cellWidth, imageView, textView, position, max, this).execute(position);
                }
            } else {
                grid = (View) convertView;
            }
            return grid;
        }
    }

    private void setGridView(boolean expand){
        //set the content of grid view
        int max = 0;

        if(expand) {
            Button button = (Button) findViewById(R.id.seeMoreStreams);
            button.setVisibility(View.GONE);
            max = streamList.size();
        }
        else{
            max = Math.min(8, streamList.size());
        }

        GridView gridView = (GridView) findViewById(R.id.gridview);
        gridView.setAdapter(new ImageAdapter(searchContext, max));
        gridView.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override
            public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
                //Toast.makeText(SearchActivity.this, "" + position, Toast.LENGTH_SHORT).show();
                Intent intent = new Intent(searchContext,SingleStreamActivity.class);
                intent.putExtra(AllStreamActivity.STREAM_SELECTED, streamList.get(position).title);
                startActivity(intent);
            }
        });
    }

    private class Streams{
        //class for json convert
        List<Stream> streamList = null;
    }

    private class Stream{
        //class for json convert
        String title = null;
        String url = null;
    }

    private void setInfo(){
        //set the content of info textView when search is done
        TextView info = (TextView) findViewById(R.id.info);
        String infoString = streamList.size() + " results for: " + globalQuery + ",\n" +
                " click on an image to view stream";
        info.setText(infoString);
        status = 0;
    }
}
