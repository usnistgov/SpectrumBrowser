/*
* Conditions Of Use 
* 
* This software was developed by employees of the National Institute of
* Standards and Technology (NIST), and others. 
* This software has been contributed to the public domain. 
* Pursuant to title 15 Untied States Code Section 105, works of NIST
* employees are not subject to copyright protection in the United States
* and are considered to be in the public domain. 
* As a result, a formal license is not needed to use this software.
* 
* This software is provided "AS IS."  
* NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
* OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
* AND DATA ACCURACY.  NIST does not warrant or make any representations
* regarding the use of the software or the results thereof, including but
* not limited to the correctness, accuracy, reliability or usefulness of
* this software.
*/
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
