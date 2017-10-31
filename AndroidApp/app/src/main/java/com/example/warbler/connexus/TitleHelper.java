package com.example.warbler.connexus;

/**
 * Created by AhPan on 10/27/17.
 */

public class TitleHelper {
    private static String title;

    public static String getCurrentTitle() {

        return title;
    }

    public static void setCurrentTitle(String title) {

        TitleHelper.title = title;
    }


}
