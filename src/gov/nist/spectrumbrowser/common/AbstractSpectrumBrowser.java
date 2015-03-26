package gov.nist.spectrumbrowser.common;

import java.util.HashMap;
import java.util.Map;
import java.util.logging.Logger;

import com.google.gwt.core.client.GWT;

public abstract class AbstractSpectrumBrowser {
	private static  String baseUrlAuthority ;
	
	private static String iconsPath;
	
	private static String apiPath;
	
	private static final String baseUrl = GWT.getModuleBaseURL();

	private static final Logger logger = Logger.getLogger("SpectrumBrowser");
	
	private static String moduleName = GWT.getModuleName();
		
	private static Map<String,String> sessionTokens = new HashMap<String,String>();
	
	public static final String ACCOUNT_EMAIL_ADDRESS = "emailAddress";
	public static final String ACCOUNT_FIRST_NAME = "firstName";
	public static final String ACCOUNT_LAST_NAME = "lastName";
	public static final String ACCOUNT_PASSWORD = "password";
	public static final String ACCOUNT_PRIVILEGE = "privilege";
	public static final String ACCOUNT_NUM_FAILED_LOGINS = "numFailedLoginAttempts";
	public static final String ACCOUNT_LOCKED = "accountLocked";
	public static final String USER_ACCOUNTS = "userAccounts";
	public static final String USER_PRIVILEGE = "user";
	public static final String ADMIN_PRIVILEGE = "admin";
	
	public static final String ACCOUNT_OLD_PASSWORD = "oldPassword";
	public static final String ACCOUNT_NEW_PASSWORD = "newPassword";

	public static final String STATUS_MESSAGE = "statusMessage";
	public static final String STATUS = "status";	
	
	static {
		int index = baseUrl.indexOf("/" + moduleName);
		baseUrlAuthority = baseUrl.substring(0,index);
		logger.addHandler(new SpectrumBrowserLoggingHandler(baseUrlAuthority));
		logger.finest("baseUrlAuthority " + baseUrlAuthority);
		iconsPath = baseUrlAuthority + "/myicons/";
		apiPath = baseUrlAuthority + "/api/html/";
		logger.fine("iconsPath = " + iconsPath);
	}
	
	public static String getSessionToken() {
		return sessionTokens.get(getBaseUrlAuthority());
	}
	
	public static String getSessionToken(String url) {
		logger.finer("getSessionToken: " + url);
		return sessionTokens.get(url);
	}
	
	
	public static String getBaseUrl() {
		return baseUrl;
	}
	
	public static String getBaseUrlAuthority() {
		return baseUrlAuthority;
	}
	
	public static void setSessionToken(String sessionToken) {
		logger.finer("setSessionToken: " + getBaseUrlAuthority() + ":" + sessionToken);
		sessionTokens.put(getBaseUrlAuthority(), sessionToken);
	}
	
	public static void clearSessionTokens() {
		sessionTokens.clear();
	}
	
	public static void setSessionToken(String baseUrl, String sessionToken) {
		logger.finer("setSessionToken: " + baseUrl + ":" + sessionToken);
		sessionTokens.put(baseUrl, sessionToken);
	}
	
	

	public static String getIconsPath() {
		return iconsPath;
	}
	
	public static String getApiPath() {
		return apiPath;
	}
	
	public abstract void logoff();
	
	public abstract boolean isUserLoggedIn();
	
}
