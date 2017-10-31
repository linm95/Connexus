package com.example.warbler.connexus;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.AsyncTask;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.GridView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.io.InputStream;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

/**
 * Created by doublsky on 10/22/17.
 */

class ImageAdapter extends BaseAdapter {
    private Context mContext;
    private String[] urls;
    private String[] texts;
    private ImageView[] images;
    private TextView[] captions;
    private LinearLayout[] icons;
    private int cellWidth;
    private boolean isWidthSet;

    ImageAdapter(Context c) {
        mContext = c;
        urls = new String[0];
        texts = new String[0];
        images = new ImageView[0];
        captions = new TextView[0];
        icons = new LinearLayout[0];
        cellWidth = 0;
        isWidthSet = false;
    }

    public Object getItem(int position) {
        return null;
    }

    public long getItemId(int position) {
        return 0;
    }

    @Override
    public int getCount() {
        return urls.length;
    }

    public void setUrlsAndTexts(String[] urls, String[] texts) {
        this.urls = urls;
        this.texts = texts;
        images = new ImageView[urls.length];
        captions = new TextView[urls.length];
        icons = new LinearLayout[urls.length];
        for (int i = 0; i < urls.length; i++) {
            images[i] = null;
            captions[i] = null;
            icons[i] = null;
        }
    }

    @Override
    public View getView(final int position, View convertView, ViewGroup parent) {
        if (isWidthSet == false) {
            cellWidth = ((GridView) parent).getColumnWidth();
            isWidthSet = true;
        }
        if (convertView == null) {
            if (icons[position] == null) {
                images[position] = new ImageView(mContext);
                images[position].setScaleType(ImageView.ScaleType.CENTER_CROP);
                images[position].setLayoutParams(new GridView.LayoutParams(cellWidth, cellWidth));

                captions[position] = new TextView(mContext);
                captions[position].setGravity(Gravity.CENTER);
                int capHeight = captions[position].getLineHeight();

                icons[position] = new LinearLayout(mContext);
                icons[position].setLayoutParams(new GridView.LayoutParams(cellWidth, cellWidth+capHeight));
                icons[position].setGravity(Gravity.CENTER);
                icons[position].setOrientation(LinearLayout.VERTICAL);

                icons[position].addView(images[position]);
                icons[position].addView(captions[position]);

                AsyncTask<String, Void, Bitmap> downloader = new AsyncTask<String, Void, Bitmap>() {
                    @Override
                    protected Bitmap doInBackground(String... urls) {
                        String image_url = urls[0].replace("localhost", "10.0.2.2");

                        OkHttpClient client = new OkHttpClient();
                        Request request = new Request.Builder().url(image_url).build();

                        try {
                            Response response = client.newCall(request).execute();
                            InputStream inputStream = response.body().byteStream();
                            return BitmapFactory.decodeStream(inputStream);
                        } catch (java.io.IOException e) {
                            System.err.println("- Error: IO Exception while downloading an image");
                            System.err.println("- Error: " + e.toString());
                            return null;
                        }
                    }

                    @Override
                    protected void onPostExecute(Bitmap result) {
                        images[position].setImageBitmap(result);
                        captions[position].setText(texts[position]);
                        ImageAdapter.this.notifyDataSetChanged();
                    }
                };

                // execute async task
                downloader.execute(urls[position]);
            }
        } else {
            icons[position] = (LinearLayout) convertView;
        }

        return icons[position];
    }
}
