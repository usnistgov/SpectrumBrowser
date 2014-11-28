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
	
	private static Map<String,String> sensorIdToBaseUrlMap = new HashMap<String,String>();
	
	
	
	static {
		int index = baseUrl.indexOf("/" + moduleName);
		baseUrlAuthority = baseUrl.substring(0,index);
		logger.addHandler(new SpectrumBrowserLoggingHandler(baseUrlAuthority));
		logger.finest("baseUrlAuthority " + baseUrlAuthority);
		iconsPath = baseUrlAuthority + "/myicons/";
		apiPath = baseUrlAuthority + "/api/html/";
		logger.fine("iconsPath = " + iconsPath);
	}
	
	public String getSessionId() {
		return sessionTokens.get(getBaseUrlAuthority());
	}
	
	
	public static String getBaseUrl() {
		return baseUrl;
	}
	
	public static String getBaseUrlAuthority() {
		return baseUrlAuthority;
	}
	
	public void setSessionToken(String sessionToken) {
		sessionTokens.put(getBaseUrlAuthority(), sessionToken);
	}
	
	public void setSessionToken(String baseUrl, String sensorId, String sessionToken) {
		sessionTokens.put(baseUrl, sessionToken);
		sensorIdToBaseUrlMap.put(sensorId, baseUrl); 
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
