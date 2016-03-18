package gov.nist.spectrumbrowser.common;

import java.util.HashMap;
import java.util.Map;
import java.util.logging.Logger;
import com.google.gwt.storage.client.Storage;

import com.google.gwt.core.client.GWT;

public abstract class AbstractSpectrumBrowser {
	private static  String baseUrlAuthority ;
	
	private static String iconsPath;
	
	private static String apiPath;
	
	private static String helpPath;
	
	private static final String baseUrl = GWT.getModuleBaseURL();

	private static final Logger logger = Logger.getLogger("SpectrumBrowser");
	
	private static String moduleName = GWT.getModuleName();
		
	private static Storage sessionTokens = Storage.getSessionStorageIfSupported();
	
	
	static {
		int index = baseUrl.indexOf("/" + moduleName);
		baseUrlAuthority = baseUrl.substring(0,index);
		logger.addHandler(new SpectrumBrowserLoggingHandler(baseUrlAuthority + "/" + moduleName));
		logger.finest("baseUrlAuthority " + baseUrlAuthority);
		iconsPath = baseUrlAuthority + "/myicons/";
		apiPath = baseUrlAuthority + "/api/html/";
		//helpPath = baseUrlAuthority + "/help/html/";
		helpPath = baseUrlAuthority + "/spectrumbrowser/getHelpPage";
		logger.fine("iconsPath = " + iconsPath);
	}
	
	public static String getSessionToken() {
		return sessionTokens.getItem(getBaseUrlAuthority());
	}
	
	public static void destroySessionToken() {
		sessionTokens.removeItem(getBaseUrlAuthority());
	}
	
	public static String getSessionToken(String url) {
		logger.finer("getSessionToken: " + url);
		return sessionTokens.getItem(url);
	}
	
	
	public static String getBaseUrl() {
		return baseUrl;
	}
	
	public static String getBaseUrlAuthority() {
		return baseUrlAuthority;
	}
	
	public static void setSessionToken(String sessionToken) {
		logger.finer("setSessionToken: " + getBaseUrlAuthority() + ":" + sessionToken);
		sessionTokens.setItem(getBaseUrlAuthority(), sessionToken);
	}
	
	public static void clearSessionTokens() {
		sessionTokens.clear();
	}
	
	public static void setSessionToken(String baseUrl, String sessionToken) {
		logger.finer("setSessionToken: " + baseUrl + ":" + sessionToken);
		sessionTokens.setItem(baseUrl, sessionToken);
	}
	
	

	public static String getIconsPath() {
		return iconsPath;
	}
	
	public static String getApiPath() {
		return apiPath;
	}
	
	public static String getHelpPath() {
		return helpPath;
	}
	
	 /**
     * Close browser window.
     */
    public static native void closeBrowser()
    /*-{
        $wnd.close();
    }-*/;

	public abstract void logoff();
	
	public abstract boolean isUserLoggedIn();
	
}
