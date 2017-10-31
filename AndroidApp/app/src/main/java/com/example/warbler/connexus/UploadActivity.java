package com.example.warbler.connexus;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.database.DatabaseUtils;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.os.AsyncTask;
import android.os.ParcelFileDescriptor;
import android.provider.MediaStore;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.EditText;
import android.widget.GridView;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileDescriptor;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;

import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

import static com.example.warbler.connexus.AllStreamActivity.STREAM_SELECTED;

import java.io.InputStream;
import java.io.OutputStream;
import java.io.UnsupportedEncodingException;
import java.net.*;

public class UploadActivity extends AppCompatActivity {

    private int PICK_IMAGE_REQUEST = 1;
    private String selectedImagePath;
    private ImageView imageView;
    private static final MediaType MEDIA_TYPE_PNG = MediaType.parse("image/png");

    // Just for testing now
    private String title = "";
    //private String owner = "185804764220139124118";
    private File imageFile;
    private Bitmap photo;
    private boolean uploadSuccess=false;
    private static boolean fromCamera = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_upload);

        Intent i= new Intent(this, LocationHelper.class);
        this.startService(i);

        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_STATE_HIDDEN);
        //Test
        this.imageView = (ImageView)this.findViewById(R.id.preview_chosen_photo);
        //this.imageView.setScaleType(ImageView.ScaleType.FIT_CENTER);

        Bundle extras = getIntent().getExtras();

        if(fromCamera && extras.getString("imageUri")!=null){
            Uri selectedImageUri=  Uri.parse(extras.getString("imageUri"));
            System.out.println("- INFO: " + selectedImageUri);
            System.out.println("- INFO: " + selectedImageUri);

            //selectedImagePath = getPath(selectedImageUri);
            String fileName;


            fileName = selectedImageUri.getPath();
            int cut = fileName.lastIndexOf('/');
            if (cut != -1) {
                fileName = fileName.substring(cut + 1);
            }

            Bitmap bitmap = null;
            try {
                bitmap = MediaStore.Images.Media.getBitmap(this.getContentResolver(), selectedImageUri);
            } catch (FileNotFoundException e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            } catch (IOException e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            }
            //create a file to write bitmap data
            File f = new File(this.getCacheDir(), fileName);
            try {
                f.createNewFile();
            } catch (IOException e) {
                e.printStackTrace();
            }

//Convert bitmap to byte array

            ByteArrayOutputStream bos = new ByteArrayOutputStream();
            bitmap.compress(Bitmap.CompressFormat.PNG, 0 /*ignored for PNG*/, bos);
            byte[] bitmapdata = bos.toByteArray();

//write the bytes in file
            FileOutputStream fos = null;
            try {
                fos = new FileOutputStream(f);
                fos.write(bitmapdata);
                fos.flush();
                fos.close();
            } catch (FileNotFoundException e) {
                e.printStackTrace();
            } catch (IOException e) {
                e.printStackTrace();
            }


            imageFile = f;

            System.out.println("- INFO: " + selectedImageUri);
            System.out.println("- INFO: " + selectedImageUri.getPath());
            //imageFile = new File(selectedImageUri.getPath());
            System.out.println("- INFO " + imageFile.getName());


            this.imageView.setImageURI(selectedImageUri);
            //this.imageView.setRotation(90);
            imageFile = new File(selectedImageUri.getPath());
        }

        //Set Stream Name
        TextView streamName = (TextView) findViewById(R.id.stream_name);
        title = TitleHelper.getCurrentTitle();
        String streamTitle = "StreamName: " + title;
        streamName.setText(streamTitle);


        EditText textArea = (EditText) findViewById(R.id.add_message_or_tags);
        /* if you use this TextArea inside ScrollView then you will face issue
         while scrolling TextArea’s inner contents. to resolve this issue we
         have to do some hack in java file. which is as below :*/
        textArea.setOnTouchListener(new View.OnTouchListener() {
            @Override
            public boolean onTouch(View v, MotionEvent event) {
                v.getParent().requestDisallowInterceptTouchEvent(true);
                switch (event.getAction() & MotionEvent.ACTION_MASK){
                    case MotionEvent.ACTION_UP:
                        v.getParent().requestDisallowInterceptTouchEvent(false);
                        break;
                }
                return false;
            }
        });
    }
    /** Called when the user taps the "USE CAMERA" button */
    public void openCamera(View view) {
        // Do something in response to button
        fromCamera=true;
        Intent intent = new Intent(this, CameraActivity.class);
        startActivity(intent);
    }

    /** Called when the user taps the "CHOOSE FROM LIBRARY" button */
    public void openPhotoLibrary(View view){
        fromCamera=false;
        Intent intent = new Intent();
        // Show only images, no videos or anything else
        intent.setType("image/*");
        intent.setAction(Intent.ACTION_GET_CONTENT);
        // Always show the chooser (if there are multiple options available)
        startActivityForResult(Intent.createChooser(intent, "Select Picture"), PICK_IMAGE_REQUEST);

    }

    public void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (resultCode == RESULT_OK) {
            if (requestCode == PICK_IMAGE_REQUEST && resultCode == Activity.RESULT_OK) {
                Uri selectedImageUri = data.getData();
                //selectedImagePath = getPath(selectedImageUri);
                String fileName;


                fileName = selectedImageUri.getPath();
                int cut = fileName.lastIndexOf('/');
                if (cut != -1) {
                    fileName = fileName.substring(cut + 1);
                }

                Bitmap bitmap = null;
                try {
                    bitmap = MediaStore.Images.Media.getBitmap(this.getContentResolver(), selectedImageUri);
                } catch (FileNotFoundException e) {
                    // TODO Auto-generated catch block
                    e.printStackTrace();
                } catch (IOException e) {
                    // TODO Auto-generated catch block
                    e.printStackTrace();
                }
                //create a file to write bitmap data
                File f = new File(this.getCacheDir(), fileName);
                try {
                    f.createNewFile();
                } catch (IOException e) {
                    e.printStackTrace();
                }

//Convert bitmap to byte array

                ByteArrayOutputStream bos = new ByteArrayOutputStream();
                bitmap.compress(Bitmap.CompressFormat.PNG, 0 /*ignored for PNG*/, bos);
                byte[] bitmapdata = bos.toByteArray();

//write the bytes in file
                FileOutputStream fos = null;
                try {
                    fos = new FileOutputStream(f);
                    fos.write(bitmapdata);
                    fos.flush();
                    fos.close();
                } catch (FileNotFoundException e) {
                    e.printStackTrace();
                } catch (IOException e) {
                    e.printStackTrace();
                }


                imageFile = f;

                System.out.println("- INFO: " + selectedImageUri);
                System.out.println("- INFO: " + selectedImageUri.getPath());
                //imageFile = new File(selectedImageUri.getPath());
                System.out.println("- INFO " + imageFile.getName());
                imageView.setImageURI(selectedImageUri);

/*
                try {
                    //if(photo!=null)
                     //   photo.recycle();
                    //photo = getBitmapFromUri(selectedImageUri);
                    imageView.setImageURI(selectedImageUri);
                    //photo.recycle();
                    //uploadImage(imageFile, imageFile.getName());
                }
                catch(IOException e){
                    Log.d("Upload Activity", "Error accessing file: " + e.getMessage());
                }*/
                /*
                try {
                    Bitmap photo = getBitmapFromUri(selectedImageUri);
                    imageView.setImageBitmap(photo);
                }
                catch (IOException e) {
                }*/
            }
        }
    }
/*
    public void uploadImage(File image, String imageName) throws IOException {
        System.out.println("Start upload image");
        OkHttpClient client = new OkHttpClient();

        RequestBody requestBody = new MultipartBody.Builder().setType(MultipartBody.FORM)
                .addFormDataPart(getString(R.string.uploadPhoto), imageName, RequestBody.create(MEDIA_TYPE_PNG, image))
                .addFormDataPart(getString(R.string.title), title)
                .addFormDataPart(getString(R.string.owner), owner)
                .build();

        Request request = new Request.Builder().url("http://10.0.2.2:8080/"+getString(R.string.uploadImageHandler))
                .post(requestBody).build();

        Response response = client.newCall(request).execute();
        if (!response.isSuccessful()) {
            throw new IOException("Unexpected code " + response);
        }
        System.out.println("End upload image");

    }*/
    public void clickUploadBtn(View view){
        if(UserHelper.getCurrentUserID()==null){
            Toast.makeText(this,"Please login to upload photo",Toast.LENGTH_SHORT).show();
            return;
        }

        if(imageFile==null){
            Toast.makeText(this,"Please Choose or Take a Photo",Toast.LENGTH_SHORT).show();
            return;
        }

        final String comments = ((EditText) findViewById(R.id.add_message_or_tags)).getText().toString();
        // create an async photo metadata fetcher
        AsyncTask<String, Void, Void> fetcher = new AsyncTask<String, Void, Void>() {
            @Override
            protected Void doInBackground(String... urls) {
                System.out.println("- Info: Start upload image");
                OkHttpClient client = new OkHttpClient();

                // Get upload url
                Request request = new Request.Builder().url(urls[0]).build();
                String uploadUrl;
                try {
                    Response response = client.newCall(request).execute();
                    uploadUrl=response.body().string();
                    //System.out.println(response.body().string());

                } catch (java.io.IOException e) {
                    System.err.println("- Error: IO Exception while getting all streams");
                    System.err.println("- Error: " + e.toString());
                    return null;
                }

                System.out.println("- Info: "+LocationHelper.getLatitude());
                System.out.println("- Info: "+LocationHelper.getLongitude());

                // Uplod Image
                RequestBody requestBody = new MultipartBody.Builder().setType(MultipartBody.FORM)
                        .addFormDataPart(getString(R.string.uploadPhoto), imageFile.getName(), RequestBody.create(MEDIA_TYPE_PNG, imageFile))
                        .addFormDataPart(getString(R.string.streamTitle), title)
                        .addFormDataPart(getString(R.string.userID), UserHelper.getCurrentUserID())
                        .addFormDataPart(getString(R.string.latitude), String.valueOf(LocationHelper.getLatitude()))
                        .addFormDataPart(getString(R.string.longitude), String.valueOf(LocationHelper.getLongitude()))
                        .addFormDataPart(getString(R.string.photoComments), comments)
                        .build();

                request = new Request.Builder().url(uploadUrl).post(requestBody).build();

                Response response = null;
                try {
                    System.out.println("- Info: onEnter try block");
                    response = client.newCall(request).execute();
                    System.out.println("- Info: onExit try block");
                } catch (IOException e) {
                    System.out.println("- Info: onEnter exception block");
                    e.printStackTrace();
                }

                if (!response.isSuccessful()) {

                    uploadSuccess = false;
                    try {
                        throw new IOException("Unexpected code " + response);
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }
                else{
                    uploadSuccess = true;
                }


                System.out.println("End upload image");
                return null;
            }

            @Override
            protected void onPostExecute(Void v) {
                if(uploadSuccess)
                    Toast.makeText(UploadActivity.this,"This photo is uploaded successfully",Toast.LENGTH_SHORT).show();
                else
                    Toast.makeText(UploadActivity.this,"This photo failed to be uploaded",Toast.LENGTH_SHORT).show();

                System.out.println("- Info: End upload image");

            }

        };

        fetcher.execute(getString(R.string.rootURL) + getString(R.string.uploadURL));

    }
    private Bitmap getBitmapFromUri(Uri uri) throws IOException {
        ParcelFileDescriptor parcelFileDescriptor =
                getContentResolver().openFileDescriptor(uri, "r");
        FileDescriptor fileDescriptor = parcelFileDescriptor.getFileDescriptor();
        Bitmap image = BitmapFactory.decodeFileDescriptor(fileDescriptor);
        parcelFileDescriptor.close();
        return image;
    }

    /**
     * helper to retrieve the path of an image URI
     */
    public String getPath(Uri uri) {
        // just some safety built in
        if( uri == null ) {
            // TODO perform some logging or show user feedback
            return null;
        }
        // try to retrieve the image from the media store first
        // this will only work for images selected from gallery
        String[] projection = { MediaStore.Images.Media.DATA };
        Cursor cursor = managedQuery(uri, projection, null, null, null);
        if( cursor != null ){
            int column_index = cursor
                    .getColumnIndexOrThrow(MediaStore.Images.Media.DATA);
            cursor.moveToFirst();
            String path = cursor.getString(column_index);
            cursor.close();
            return path;
        }
        // this is our fallback here
        return uri.getPath();
    }

}
