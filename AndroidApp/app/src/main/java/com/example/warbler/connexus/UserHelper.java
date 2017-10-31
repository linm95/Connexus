package com.example.warbler.connexus;

/**
 * Created by doublsky on 10/26/17.
 */

class UserHelper {
    private static String userID;
    private static String userEmail;

    public static boolean isSignedIn() {
        // FIXME: 10/26/17 TT: Add actual implementation
        return userID != null;
    }

    public static String getCurrentUserID() {
        // FIXME: 10/26/17 TT: Add actual implementation
        return userID;
    }

    public static void setCurrentUserID(String userID) {
        // FIXME: 10/26/17 TT: Add actual implementation
        UserHelper.userID = userID;
    }

    public static String getCurrentUserEmail() {
        // FIXME: 10/26/17 TT: Add actual implementation
        return userEmail;
    }

    public static void setCurrentUserEmail(String userEmail) {
        // FIXME: 10/26/17 TT: Add actual implementation
        UserHelper.userEmail = userEmail;
    }
}
