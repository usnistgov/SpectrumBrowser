package gov.nist.spectrumbrowser.common;

import java.util.logging.Logger;

import com.google.gwt.core.client.GWT;

public abstract class AbstractSpectrumBrowser {
	private static  String baseUrlAuthority ;
	
	private static String iconsPath;
	
	private static String apiPath;
	
	private static final String baseUrl = GWT.getModuleBaseURL();

	private static final Logger logger = Logger.getLogger("SpectrumBrowser");
	
	private static String moduleName = GWT.getModuleName();
	
	private String sessionToken;
	
	
	
	
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
		return this.sessionToken;
	}
	
	public static String getBaseUrl() {
		return baseUrl;
	}
	
	public static String getBaseUrlAuthority() {
		return baseUrlAuthority;
	}
	
	public void setSessionToken(String sessionToken) {
		this.sessionToken = sessionToken;
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
